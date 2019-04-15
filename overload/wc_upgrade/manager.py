# module controlling upgrade/catalog from Worldcat process
import csv

from bibs.bibs import (BibOrderMeta, create_initials_field,
                       write_marc21, create_controlfield)
from bibs.parsers import (parse_isbn, remove_oclcNo_prefix)
from bibs.crosswalks import string2xml, marcxml2array
from bibs.bpl_callnum import create_bpl_fiction_callnum
from bibs.nypl_callnum import create_nypl_fiction_callnum
from datastore import (session_scope, WCSourceBatch, WCSourceMeta, WCHit)
from db_worker import (insert_or_ignore, delete_all_table_data,
                       retrieve_records, retrieve_related, update_record)
from connectors.worldcat.session import (SearchSession, MetadataSession,
                                         is_positive_response, no_match,
                                         extract_record_from_response)
from credentials import get_from_vault, evaluate_worldcat_creds
from criteria import meets_global_criteria, meets_user_criteria
from bibs.xml_bibs import (get_oclcNo, get_cuttering_fields,
                           get_tag_008, get_record_leader, get_tag_300a)


def update_progbar(progbar):
    """creates progbar ticks"""
    progbar['value'] += 1
    progbar.update()


def store_meta(model, record):
    pass


def remove_previous_process_data():
    with session_scope() as db_session:
        # deletes WCSourceBatch data and all related tables
        delete_all_table_data(db_session, WCSourceBatch)


def get_credentials(api):
    creds = get_from_vault(api, 'Overload')
    return evaluate_worldcat_creds(creds)


def request_record(session, oclcNo):
    if oclcNo:
        res = session.get_record(oclcNo)
        if is_positive_response(res) and not no_match(res):
            xml_record = extract_record_from_response(res)
            return xml_record


def create_callNum(marcxml, system, library):
    leader_string = get_record_leader(marcxml)
    cuttering_opts = get_cuttering_fields(marcxml)
    tag_008 = get_tag_008(marcxml)
    tag_300a = get_tag_300a(marcxml)

    if system == 'NYPL' and library == 'branches':
        callNum = create_nypl_fiction_callnum(
            leader_string, tag_008, tag_300a, cuttering_opts)
        return callNum
    elif system == 'BPL':
        callNum = create_bpl_fiction_callnum(
            leader_string, tag_008, tag_300a, cuttering_opts)
        return callNum
    else:
        print('NOT IMPLEMENTED YET')
        return None


def nypl_oclcNo_field(marcxml):
    oclcNo = get_oclcNo(marcxml)
    oclcNo = remove_oclcNo_prefix(oclcNo)
    tag_001 = create_controlfield('001', oclcNo)
    return tag_001


def launch_process(source_fh, dst_fh, system, library, progbar1, progbar2,
                   process_label, hits, nohits, meet_crit_counter,
                   fail_user_crit_counter, fail_glob_crit_counter,
                   action, encode_level, rec_type, cat_rules, cat_source,
                   id_type='ISBN', api=None):
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
        progbar: tkinter widget
        counter: tkinter StringVar
        hits: tkinter IntVar
        nohits: tkinter IntVar
    """

    remove_previous_process_data()

    # calculate max counter
    process_label.set('reading:')
    with open(source_fh, 'r') as file:
        reader = csv.reader(file)
        # skip header
        reader.next()
        c = 0
        for row in reader:
            c += 1
        progbar1['maximum'] = c * 4
        progbar2['maximum'] = c

    with open(source_fh, 'r') as file:
        reader = csv.reader(file)
        # sniff what type of data it is
        header = reader.next()
        with session_scope() as db_session:
            # create batch record
            batch_rec = insert_or_ignore(
                db_session, WCSourceBatch, file=source_fh)
            db_session.flush()
            batch_id = batch_rec.wcsbid
            if len(header) == 1:
                # list of id
                if id_type == 'ISBN':
                    for row in reader:
                        meta = BibOrderMeta(
                            isbn=[parse_isbn(row[0])])
                        insert_or_ignore(
                            db_session, WCSourceMeta,
                            wcsbid=batch_id, meta=meta)
                        update_progbar(progbar1)
                        update_progbar(progbar2)
            else:
                # differenciate between correct sierra export (headers)
                # and invalid formats
                pass

    processed_counter = 0
    found_counter = 0
    not_found_counter = 0
    creds = get_credentials(api)

    # query Worldcat
    process_label.set('querying:')
    # reset progbar2
    progbar2['value'] = 0
    with session_scope() as db_session:
        metas = retrieve_records(
            db_session, WCSourceMeta, wcsbid=batch_id)
        with SearchSession(creds) as session:
            for m in metas:
                if m.meta.wcid:
                    # query by OCLC number
                    pass
                elif m.meta.lcid:
                    # query by LC number
                    pass
                elif m.meta.isbn:
                    for i in m.meta.isbn:
                        res = session.lookup_by_isbn(i)
                        if is_positive_response(res) and \
                                not no_match(res):
                            found_counter += 1
                            # convert from string to xml (or remain as string?)
                            doc = string2xml(res.content)
                            # persist
                            res = insert_or_ignore(
                                db_session, WCHit, wcsmid=m.wcsmid,
                                hit=True, search_marcxml=doc)
                        else:
                            not_found_counter += 1
                            res = insert_or_ignore(
                                db_session, WCHit, wcsmid=m.wcsmid,
                                hit=False, search_marcxml=None)

                        hits.set(found_counter)
                        nohits.set(not_found_counter)

                elif m.meta.issn:
                    # query by ISSN
                    pass
                elif m.meta.upc:
                    # query by UPC
                    pass
                update_progbar(progbar1)
                update_progbar(progbar2)
                processed_counter += 1

        db_session.commit()

        # verify found matches meet set criteria
        process_label.set('downloading:')
        # reset progbar2
        progbar2['value'] = 0

        with MetadataSession(creds) as session:
            metas = retrieve_related(
                db_session, WCSourceMeta, 'wchit', wcsbid=batch_id)
            for m in metas:
                for x in m.wchit:
                    if x.hit:
                        oclcNo = get_oclcNo(x.search_marcxml)
                        xml_record = request_record(session, oclcNo)
                        if xml_record is not None:
                            update_record(
                                db_session, WCHit, x.wchid,
                                match=oclcNo,
                                match_marcxml=xml_record)
                update_progbar(progbar1)
                update_progbar(progbar2)
        db_session.commit()

        # check if meet criteria & write (will be replaced with user selection)
        process_label.set('compiling:')
        progbar2['value'] = 0
        rows = retrieve_records(
            db_session, WCHit, hit=True)
        for row in rows:
            xml_record = row.match_marcxml
            if meets_global_criteria(xml_record):
                if meets_user_criteria(
                        xml_record,
                        encode_level,
                        rec_type,
                        cat_rules,
                        cat_source):

                    # add call number & write to file
                    callNum = create_callNum(
                        xml_record, system, library)
                    if callNum:
                        meet_crit_counter.set(meet_crit_counter.get() + 1)
                        initials = create_initials_field(
                            system, library, 'CATbot')
                        marc_record = marcxml2array(xml_record)[0]
                        marc_record.add_ordered_field(callNum)
                        marc_record.add_ordered_field(initials)
                        if system == 'NYPL':
                            tag_001 = nypl_oclcNo_field(xml_record)
                            marc_record.remove_fields('001')
                            marc_record.add_ordered_field(tag_001)

                        write_marc21(dst_fh, marc_record)

                    else:
                        fail_glob_crit_counter.set(
                            fail_glob_crit_counter.get() + 1)
                else:
                    fail_user_crit_counter.set(
                        fail_user_crit_counter.get() + 1)
            else:
                fail_glob_crit_counter.set(fail_glob_crit_counter.get() + 1)

            update_progbar(progbar1)
            update_progbar(progbar2)

    # show completed
    progbar1['value'] = progbar1['maximum']
    progbar2['value'] = progbar2['maximum']
