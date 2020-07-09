# module controlling upgrade/catalog from Worldcat process
import csv
import logging
import os

from bibs.bibs import (
    BibOrderMeta,
    create_initials_field,
    write_marc21,
    create_controlfield,
    create_target_id_field,
    create_command_line_field,
)
from bibs.parsers import parse_isbn, remove_oclcNo_prefix
from bibs.crosswalks import string2xml, marcxml2array
from bibs.bpl_callnum import create_bpl_callnum
from bibs.nypl_callnum import (
    create_nypl_callnum,
    create_nypl_recap_callnum,
    create_nypl_recap_item,
)
from bibs.patches import (
    remove_unsupported_subject_headings,
    remove_unwanted_tags,
    remove_ebook_isbns,
)
from bibs.sierra_dicts import NW2SEXPORT_COLS, BW2SEXPORT_COLS, NBIB_DEFAULT_LOCATIONS
from bibs.xml_bibs import (
    get_oclcNo,
    get_cuttering_fields,
    get_subject_fields,
    get_tag_008,
    get_tag_082,
    get_record_leader,
    get_tag_300a,
    results2record_list,
)
from connectors.worldcat.accesstoken import WorldcatAccessToken
from connectors.worldcat.search_session import SearchSession
from connectors.worldcat.metadata_session import (
    MetadataSession,
    construct_sru_query,
    holdings_responses,
)
from connectors.worldcat.session import (
    is_positive_response,
    has_records,
    extract_record_from_response,
)
from credentials import get_from_vault, evaluate_worldcat_creds
from criteria import meets_upgrade_criteria, meets_catalog_criteria, meets_user_criteria
from datastore import session_scope, WCSourceBatch, WCSourceMeta, WCHit
from db_worker import (
    insert_or_ignore,
    delete_all_table_data,
    retrieve_record,
    retrieve_one_related,
    retrieve_records,
    retrieve_related,
    update_hit_record,
    update_meta_record,
)
from errors import OverloadError
from logging_setup import LogglyAdapter
from source_parsers import sierra_export_data
from utils import save2csv
from setup_dirs import W2S_MULTI_ORD, W2S_SKIPPED_ORD


module_logger = LogglyAdapter(logging.getLogger("overload"), None)


def update_progbar(progbar):
    """progbar ticks"""
    progbar["value"] += 1
    progbar.update()


def interpret_search_response(response, db_session, wcsmid):
    rec = retrieve_record(db_session, WCHit, wcsmid=wcsmid)
    if is_positive_response(response) and has_records(response):
        module_logger.debug("Service response is positive and has records.")
        hit = True
        doc = string2xml(response.content)

    else:
        module_logger.debug("Service NOT responded or no hits.")
        hit = False
        doc = None

    if not rec:
        insert_or_ignore(db_session, WCHit, wcsmid=wcsmid, hit=hit, query_results=doc)
    else:
        update_hit_record(db_session, WCHit, rec.wchid, hit=hit, query_results=doc)

    return hit


def remove_previous_process_data():
    module_logger.debug("Deleting previous process data.")
    with session_scope() as db_session:
        # deletes WCSourceBatch data and all related tables
        delete_all_table_data(db_session, WCSourceBatch)
        module_logger.debug("Data from previous run has been deleted.")

    try:
        os.remove(W2S_MULTI_ORD)
        os.remove(W2S_SKIPPED_ORD)
    except WindowsError:
        pass


def get_credentials(api):
    module_logger.debug("Acquiring Worldcat credentials.")
    creds = get_from_vault(api, "Overload")
    return evaluate_worldcat_creds(creds)


def get_token(creds):
    module_logger.debug(
        "Requesting Worldcat access token using {} creds".format(creds["name"])
    )
    token = WorldcatAccessToken(
        oauth_server=creds["oauth_server"],
        key=creds["key"],
        secret=creds["secret"],
        options={
            "scope": creds["scope"],
            "principal_id": creds["principal_id"],
            "principal_idns": creds["principal_idns"],
        },
    )

    return token


def request_record(session, oclcNo):
    if oclcNo:
        oclcNo = str(oclcNo)
        res = session.get_record(oclcNo)
        module_logger.info("Metadata API request: {}".format(res.url))
        if is_positive_response(res):
            module_logger.info("Match found.")
            xml_record = extract_record_from_response(res)
            return xml_record
        else:
            module_logger.info("No record found.")
    else:
        module_logger.info("Metadata API request skipped: no data to query")


def create_local_fields(marcxml, system, library, order_data=None, recap_no=None):
    module_logger.debug("Creating local fields.")

    local_fields = []
    leader_string = get_record_leader(marcxml)
    cuttering_opts = get_cuttering_fields(marcxml)
    tag_008 = get_tag_008(marcxml)
    tag_300a = get_tag_300a(marcxml)
    tag_082 = get_tag_082(marcxml)
    subject_fields = get_subject_fields(marcxml)

    if system == "NYPL" and library == "branches":
        callNum = create_nypl_callnum(
            leader_string,
            tag_008,
            tag_082,
            tag_300a,
            cuttering_opts,
            subject_fields,
            order_data,
        )
        if callNum is not None:
            local_fields.append(callNum)
    elif system == "NYPL" and library == "research":
        callNum = create_nypl_recap_callnum(recap_no)
        local_fields.append(callNum)
        itemField = create_nypl_recap_item(order_data, recap_no)
        module_logger.debug("Created itemField: {}".format(str(itemField)))
        local_fields.append(itemField)
    elif system == "BPL":
        callNum = create_bpl_callnum(
            leader_string,
            tag_008,
            tag_082,
            tag_300a,
            cuttering_opts,
            subject_fields,
            order_data,
        )
        if callNum is not None:
            local_fields.append(callNum)
    else:
        module_logger.warning(
            "Call number creation for {}-{} not implemented yet".format(system, library)
        )

    return local_fields


def nypl_oclcNo_field(marcxml):
    oclcNo = get_oclcNo(marcxml)
    oclcNo = remove_oclcNo_prefix(oclcNo)
    tag_001 = create_controlfield("001", oclcNo)
    return tag_001


def estimate_progbars_max(reader, progbar1, progbar2):
    # calculate pogbar max values
    c = 0
    for row in reader:
        c += 1
    progbar1["maximum"] = c * 5
    progbar2["maximum"] = c


def sierra_export_reader(source_fh, system, progbar1, progbar2):
    with open(source_fh, "r") as file:
        reader = csv.reader(file)

        # skip header
        header = reader.next()

        # check if Sierra export file has a correct structure
        if system == "NYPL":
            if header != NW2SEXPORT_COLS:
                raise OverloadError(
                    "Sierra Export format incorrect.\nPlease refer to help"
                    "for more info."
                )
        elif system == "BPL":
            if header != BW2SEXPORT_COLS:
                raise OverloadError(
                    "Sierra Export format incorrect.\nPlease refer to help"
                    "for more info."
                )
        estimate_progbars_max(reader, progbar1, progbar2)


def id_list_reader(source_fh, progbar1, progbar2):
    with open(source_fh, "r") as file:
        reader = csv.reader(file)
        estimate_progbars_max(reader, progbar1, progbar2)


def launch_process(
    source_fh,
    data_source,
    system,
    library,
    progbar1,
    progbar2,
    process_label,
    hits,
    nohits,
    skipped,
    meet_crit_counter,
    fail_user_crit_counter,
    fail_glob_crit_counter,
    action,
    encode_level,
    mat_type,
    cat_rules,
    cat_source,
    recap_range,
    id_type="ISBN",
    api=None,
):
    """
    work notes:
    1. iterate through the source files and extract bib/order metadata
    2. temporarily persist this data in local datastore
    3. iterate over the batch and find best hit for each
    4. persist in local store matched record as a pymarc object
    5. display results (with all data needed for Sierra import) to user
    5. allow user to decide what to write to final file

    args:
        source_fh: str, file path
        data_source: str, 'Sierra export' or 'IDs list'
        system: str, 'NYPL' or 'BPL'
        library: str, 'research' or 'branches'
        progbar1: tkinter widget, overall progressbar
        progbar2: tkinter widget, task progressbar
        process_label: tkinter StrinVar, current task label
        hits: tkinter IntVar, hits counter
        nohits: tkinter IntVar, failed search counter
        meet_crit_counter: tkinter IntVar, success match & eval counter
        fail_user_crit_counter: tkinter IntVar, failed user criteria counter
        fail_glob_crit_counter: tkinter IntVar, failed global criteria counter
        action: str, 'catalog' or 'upgrade'
        encode_level: str, 'any', ...
        mat_type: str, 'any', print', 'large print', 'dvd', 'bluray'
        cat_rules: str,  'any', 'RDA-only'
        cat_source: str, 'any', 'DLC'
        recap_range: list, uppper and lower limits of Recap numbers
        id_type: str, 'ISBN', 'UPC', 'ISSN', 'LCCN', 'OCLC #'
        api: str, name of api to be used for queries
    """

    if mat_type == "":
        mat_type = None
    if cat_source == "":
        cat_source = None

    module_logger.debug(
        "Launching W2S process. "
        "Params: source_fh:{}, data_source:{}, system:{}, "
        "library:{}, action:{}, encode_level:{}, mat_type:{}, "
        "cat_rules:{}, cat_source:{}, recap_range:{}, id_type:{}, "
        "api:{}".format(
            source_fh,
            data_source,
            system,
            library,
            action,
            encode_level,
            mat_type,
            cat_rules,
            cat_source,
            recap_range,
            id_type,
            api,
        )
    )

    processed_counter = 0
    found_counter = 0
    not_found_counter = 0
    skipped_counter = 0

    remove_previous_process_data()

    # validate correctness of sierra export
    process_label.set("reading:")

    if data_source == "Sierra export":
        sierra_export_reader(source_fh, system, progbar1, progbar2)
    elif data_source == "IDs list":
        id_list_reader(source_fh, progbar1, progbar2)

    # keep track of recap call numbers
    if recap_range:
        recap_no = recap_range[0]
    else:
        recap_no = None

    with session_scope() as db_session:
        # create batch record
        batch_rec = insert_or_ignore(
            db_session,
            WCSourceBatch,
            file=source_fh,
            system=system,
            library=library,
            action=action,
            api=api,
            data_source=data_source,
            encode_level=encode_level,
            mat_type=mat_type,
            cat_rules=cat_rules,
            cat_source=cat_source,
            id_type=id_type,
        )
        db_session.flush()
        batch_id = batch_rec.wcsbid

        # parse depending on the data source
        if data_source == "IDs list":
            with open(source_fh, "r") as file:
                reader = csv.reader(file)
                # skip header
                reader.next()
                if id_type == "ISBN":
                    for row in reader:
                        meta = BibOrderMeta(
                            system=system, dstLibrary=library, t020=[parse_isbn(row[0])]
                        )
                        insert_or_ignore(
                            db_session, WCSourceMeta, wcsbid=batch_id, meta=meta
                        )
                        update_progbar(progbar1)
                        update_progbar(progbar2)
                elif id_type == "UPC":
                    raise OverloadError("Not implemented.")
                    pass

                    # will be implemented later
                    # for row in reader:
                    #     meta = BibOrderMeta(
                    #         system=system,
                    #         dstLibrary=library,
                    #         t024=[parse_upc(row[0])])

                elif id_type == "OCLC #":
                    for row in reader:
                        meta = BibOrderMeta(
                            system=system, dstLibrary=library, t001=row[0]
                        )
                        insert_or_ignore(
                            db_session, WCSourceMeta, wcsbid=batch_id, meta=meta
                        )
                        update_progbar(progbar1)
                        update_progbar(progbar2)
                else:
                    raise OverloadError("Not implemented.")

        elif data_source == "Sierra export":
            data = sierra_export_data(source_fh, system, library)
            for meta, single_order in data:
                if single_order is None:
                    row = ["b{}a".format(meta.sierraId), meta.title]
                    skipped_counter += 1
                    skipped.set(skipped_counter)
                    save2csv(W2S_SKIPPED_ORD, row)
                    progbar1["maximum"] = progbar1["maximum"] - 3
                elif single_order is False:
                    row = ["b{}a".format(meta.sierraId), meta.title]
                    save2csv(W2S_MULTI_ORD, row)
                    progbar1["maximum"] = progbar1["maximum"] - 3
                else:
                    insert_or_ignore(
                        db_session, WCSourceMeta, wcsbid=batch_id, meta=meta
                    )
                    update_progbar(progbar1)
                update_progbar(progbar2)

        creds = get_credentials(api)
        wskey = creds["key"]
        db_session.commit()

        # query Worldcat
        process_label.set("querying:")
        # reset progbar2
        progbar2["value"] = 0
        metas = retrieve_records(db_session, WCSourceMeta, wcsbid=batch_id)
        with SearchSession(credentials=wskey) as session:
            for m in metas:
                module_logger.debug(m.meta)
                hit = False
                if m.meta.t001:
                    query = construct_sru_query(
                        m.meta.t001,
                        keyword_type="OCLC #",
                        mat_type=mat_type,
                        cat_source=cat_source,
                    )
                    res = session.sru_query(query=query)
                    module_logger.debug("OCLC# request: {}".format(res.url))

                    hit = interpret_search_response(res, db_session, m.wcsmid)

                    if hit:
                        found_counter += 1

                if m.meta.t010 and not hit:
                    query = construct_sru_query(
                        m.meta.t010,
                        keyword_type="LCCN",
                        mat_type=mat_type,
                        cat_source=cat_source,
                    )
                    res = session.sru_query(query=query)
                    module_logger.debug("LCCN request: {}".format(res.url))

                    hit = interpret_search_response(res, db_session, m.wcsmid)

                    if hit:
                        found_counter += 1

                if m.meta.t020 and not hit:
                    # will iterate over all ISBNs if no hits
                    for isbn in m.meta.t020:
                        query = construct_sru_query(
                            isbn,
                            keyword_type="ISBN",
                            mat_type=mat_type,
                            cat_source=cat_source,
                        )
                        res = session.sru_query(query=query)
                        module_logger.debug("ISBN request: {}".format(res.url))

                        hit = interpret_search_response(res, db_session, m.wcsmid)

                        if hit:
                            found_counter += 1
                            break  # stop searching

                if m.meta.t024 and not hit:
                    for upc in m.meta.t024:
                        query = construct_sru_query(
                            upc,
                            keyword_type="UPC",
                            mat_type=mat_type,
                            cat_source=cat_source,
                        )
                        res = session.sru_query(query=query)
                        module_logger.debug("UPC request: {}".format(res.url))

                        hit = interpret_search_response(res, db_session, m.wcsmid)

                        if hit:
                            found_counter += 1
                            break  # stop searching

                if not hit:
                    not_found_counter += 1
                    module_logger.debug(
                        "Unable to find any matches in Worldcat for {}.".format(m.meta)
                    )
                    interpret_search_response(None, db_session, m.wcsmid)

                hits.set(found_counter)
                nohits.set(not_found_counter)

                update_progbar(progbar1)
                update_progbar(progbar2)
                processed_counter += 1

        db_session.commit()

        # check if meet criteria
        process_label.set("analyzing:")
        progbar2["value"] = 0
        rows = retrieve_records(db_session, WCHit, hit=True)
        for row in rows:
            results = row.query_results
            recs = results2record_list(results)
            for xml_record in recs:
                fulfills = False
                fail_types = []
                if meets_upgrade_criteria(xml_record):
                    if meets_user_criteria(
                        xml_record, encode_level, mat_type, cat_rules, cat_source
                    ):
                        fulfills = True
                        if action == "upgrade":
                            meet_crit_counter.set(meet_crit_counter.get() + 1)

                            oclcNo = get_oclcNo(xml_record)
                            update_hit_record(
                                db_session, WCHit, row.wchid, match_oclcNo=oclcNo
                            )

                            update_progbar(progbar1)
                            update_progbar(progbar2)
                            break

                        elif action == "catalog":
                            if meets_catalog_criteria(xml_record, library):
                                fulfills = True
                                meet_crit_counter.set(meet_crit_counter.get() + 1)
                                oclcNo = get_oclcNo(xml_record)
                                update_hit_record(
                                    db_session, WCHit, row.wchid, match_oclcNo=oclcNo
                                )

                                update_progbar(progbar1)
                                update_progbar(progbar2)
                                break
                            else:
                                fail_types.append("global")
                    else:
                        fail_types.append("user")
                else:
                    fail_types.append("global")

            if not fulfills:
                if "user" in fail_types:
                    fail_user_crit_counter.set(fail_user_crit_counter.get() + 1)
                else:
                    fail_glob_crit_counter.set(fail_glob_crit_counter.get() + 1)

        db_session.commit()

        # download and prep
        process_label.set("downloading:")
        # reset progbar2
        progbar2["value"] = 0

        # obtain access token
        token = get_token(creds)
        if token.token_str is None:
            module_logger.error(
                "Worldcat token not obtained. Error: {}.".format(token.server_response)
            )
        else:
            module_logger.debug("Worldcat token obtained.")

        # open Metadata API session
        with MetadataSession(credentials=token) as session:
            metas = retrieve_related(
                db_session, WCSourceMeta, "wchits", wcsbid=batch_id
            )
            for m in metas:
                if m.wchits.match_oclcNo:
                    xml_record = request_record(session, m.wchits.match_oclcNo)
                    if xml_record is not None:
                        update_hit_record(
                            db_session, WCHit, m.wchits.wchid, match_marcxml=xml_record
                        )
                update_progbar(progbar1)
                update_progbar(progbar2)

        db_session.commit()

        # prepare MARC files
        process_label.set("prepping:")
        progbar2["value"] = 0

        # check if Sierra bib # provided and use
        # for overlay command line
        rows = retrieve_records(db_session, WCSourceMeta, wcsbid=batch_id)

        for row in rows:
            # initial workflow shared by updgrade fuctionality
            xml_record = row.wchits.match_marcxml
            if xml_record is not None:
                marc_record = marcxml2array(xml_record)[0]
                remove_unsupported_subject_headings(system, marc_record)
                remove_unwanted_tags(marc_record)
                remove_ebook_isbns(marc_record)
                marc_record.remove_fields("901", "907", "945", "949", "947")
                initials = create_initials_field(system, library, "W2Sbot")
                marc_record.add_ordered_field(initials)

                if data_source == "Sierra export":
                    order_data = row.meta
                    if order_data.sierraId:
                        overlay_tag = create_target_id_field(
                            system, order_data.sierraId
                        )
                        marc_record.add_ordered_field(overlay_tag)

                if system == "NYPL":
                    marc_record.remove_fields("001")
                    tag_001 = nypl_oclcNo_field(xml_record)
                    marc_record.add_ordered_field(tag_001)

                    # add Sierra bib code 3 and default location
                    if library == "branches":
                        defloc = NBIB_DEFAULT_LOCATIONS["branches"]
                    elif library == "research":
                        defloc = NBIB_DEFAULT_LOCATIONS["research"]

                    tag_949 = create_command_line_field("*b3=h;bn={};".format(defloc))
                    marc_record.add_ordered_field(tag_949)

                if action == "catalog":
                    # add call number & persist
                    if data_source == "Sierra export":
                        order_data = row.meta

                        local_fields = create_local_fields(
                            xml_record,
                            system,
                            library,
                            order_data=order_data,
                            recap_no=recap_no,
                        )

                    else:
                        # data source a list of IDs
                        local_fields = create_local_fields(
                            xml_record, system, library, recap_no=recap_no
                        )

                    if local_fields:
                        for field in local_fields:
                            if field is not None:
                                marc_record.add_ordered_field(field)
                        if system == "NYPL" and library == "research":
                            recap_no += 1

                update_hit_record(
                    db_session, WCHit, row.wchits.wchid, prepped_marc=marc_record
                )

            update_progbar(progbar1)
            update_progbar(progbar2)

            # make sure W2S stays within assigned Recap range
            if system == "NYPL" and library == "research":
                if action == "catalog":
                    if recap_no > recap_range[1]:
                        raise OverloadError(
                            "Used all available ReCAP call numbers " "assigned for W2S."
                        )

    # show completed
    progbar1["value"] = progbar1["maximum"]
    progbar2["value"] = progbar2["maximum"]


def get_bib(meta_id):
    data = []
    with session_scope() as db_session:
        r = retrieve_one_related(db_session, WCSourceMeta, "wchits", wcsmid=meta_id)
        sierra_data = dict(
            title=r.meta.title,
            sierraId=r.meta.sierraId,
            oid=r.meta.oid,
            locs=r.meta.locs,
            venNote=r.meta.venNote,
            note=r.meta.note,
            intNote=r.meta.intNote,
            choice=r.selected,
            barcode=r.barcode,
        )
        if r.wchits.prepped_marc:
            worldcat_data = str(r.wchits.prepped_marc).splitlines()
        else:
            worldcat_data = None
        data.append((r.wchits.wchid, sierra_data, worldcat_data))
    db_session.expunge_all()

    return data


def count_total():
    meta_ids = []
    with session_scope() as db_session:
        recs = retrieve_records(db_session, WCSourceMeta)
        total = 0
        for rec in recs:
            total += 1
            meta_ids.append(rec.wcsmid)
    return total, meta_ids


def get_batch_criteria_record():
    with session_scope() as db_session:
        rec = retrieve_record(db_session, WCSourceBatch)
        db_session.expunge_all()
        return rec


def persist_choice(meta_ids, selected, barcode_var=None):
    with session_scope() as db_session:
        for mid in meta_ids:
            if barcode_var:
                if barcode_var.get():
                    barcode = barcode_var.get()
                else:
                    barcode = None
            else:
                barcode = None

            update_meta_record(
                db_session, WCSourceMeta, mid, selected=selected, barcode=barcode
            )


def create_marc_file(system, dst_fh, no_holdings_msg=None):
    with session_scope() as db_session:
        recs = retrieve_related(db_session, WCSourceMeta, "wchits", selected=True)
        for r in recs:
            marc = r.wchits.prepped_marc
            if marc:
                # delete unsupported headings
                # remove_unsupported_subject_headings(marc)
                # remove_unwanted_tags(marc)
                # remove_ebook_isbns(marc)
                # add barcode if added by user
                if r.barcode is not None:
                    for field in marc.get_fields("949"):
                        if field.indicators == [" ", "1"]:
                            field.add_subfield("i", r.barcode)
                if no_holdings_msg:
                    msg = "OCLC holdings not updated"
                    if system == "NYPL":
                        field = marc["901"]
                    elif system == "BPL":
                        field = marc["947"]
                    if "h" not in field:
                        field.add_subfield("h", msg)
                    else:
                        field["h"] = msg
                try:
                    write_marc21(dst_fh, marc)
                except TypeError:
                    module_logger.error(
                        "Unable to create marc file for record: "
                        "wchid: {}, oclcNo: {}".format(
                            r.wchits.wchid, r.wchits.match_oclcNo
                        )
                    )
                    raise

    if ".mrc" in dst_fh:
        dst_fh = dst_fh.replace(".mrc", ".csv")
    else:
        dst_fh = "{}.csv".format(dst_fh)
    header = ["position", "result", "title", "ISBN"]
    save2csv(dst_fh, header)

    with session_scope() as db_session:
        recs = retrieve_related(db_session, WCSourceMeta, "wchits")
        for r in recs:
            if r.selected and r.wchits.prepped_marc:
                result = "pass"
            else:
                result = "reject"
            try:
                row = [r.wchits.wchid, result, r.meta.title, r.meta.t020[0]]
            except IndexError:
                row = [r.wchits.wchid, result, r.meta.title, None]
            save2csv(dst_fh, row)


def set_oclc_holdings(dst_fh):
    oclc_numbers = []
    hold_not_set = []
    with session_scope() as db_session:
        recs = retrieve_related(db_session, WCSourceMeta, "wchits", selected=True)
        for r in recs:
            if r.wchits.match_oclcNo:
                oclc_numbers.append(str(r.wchits.match_oclcNo))

        # update holdings
        batch_rec = retrieve_record(db_session, WCSourceBatch)
        creds = get_credentials(batch_rec.api)
        token = get_token(creds)

        with MetadataSession(credentials=token) as session:
            responses = session.holdings_set_batch(oclc_numbers)
            holdings = holdings_responses(responses)
            if holdings:
                for oclcNo, holding in holdings.items():
                    recs = retrieve_records(db_session, WCHit, match_oclcNo=oclcNo)
                    for rec in recs:
                        if holding[0] in ("set", "exists"):
                            holding_set = True
                        else:
                            holding_set = False
                        update_hit_record(
                            db_session,
                            WCHit,
                            rec.wchid,
                            holding_set=holding_set,
                            holding_status=holding[0],
                            holding_response=holding[1],
                        )

        db_session.commit()

        # verify all selected had holdings set
        recs = retrieve_related(db_session, WCSourceMeta, "wchits", selected=True)
        for r in recs:
            if not r.wchits.holding_set:
                hold_not_set.append(r.wchits.match_oclcNo)

    fh_csv = os.path.join(os.path.split(dst_fh)[0], "holdings-issues.csv")
    if hold_not_set:
        for oclcNo in hold_not_set:
            save2csv(fh_csv, [oclcNo])
        return False
    else:
        return True
