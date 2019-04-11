# module controlling upgrade/catalog from Worldcat process
import csv

from bibs.bibs import (BibOrderMeta, parse_isbn, create_initials_field,
                       write_marc21)
from bibs.crosswalks import string2xml, marcxml2array
from bibs.nypl_callnum import create_nypl_fiction_callnum
from datastore import (session_scope, WCSourceBatch, WCSourceMeta, WCHit)
from db_worker import (insert_or_ignore, delete_records,
                       retrieve_values, retrieve_related, update_record)
from connectors.worldcat.session import (SearchSession,
                                         MetadataSession, evaluate_response,
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


def remove_temp_data(source_fh):
    with session_scope() as db_session:
        delete_records(db_session, WCSourceBatch)


def get_credentials(api):
    creds = get_from_vault(api, 'Overload')
    return evaluate_worldcat_creds(creds)


def request_record(session, oclcNo):
    res = session.get_record(oclcNo)
    res = evaluate_response(res)
    return res


def create_callNum(marcxml, system, library):
    if system == 'NYPL' and library == 'branches':
        leader_string = get_record_leader(marcxml)
        cuttering_opts = get_cuttering_fields(marcxml)
        tag_008 = get_tag_008(marcxml)
        tag_300a = get_tag_300a(marcxml)
        callNum = create_nypl_fiction_callnum(
            leader_string, tag_008, tag_300a, cuttering_opts)
        return callNum
    else:
        print('NOT IMPLEMENTED YET')
        return None


def launch_process(source_fh, dst_fh, system, library, progbar, counter,
                   hits, nohits,
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

    remove_temp_data(source_fh)

    # calculate max counter
    with open(source_fh, 'r') as file:
        reader = csv.reader(file)
        c = 0
        for row in reader:
            c += 1
        progbar['maximum'] = c * 2

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
                        update_progbar(progbar)
            else:
                # differenciate between correct sierra export (headers)
                # and invalid formats
                pass

    processed_counter = 0
    found_counter = 0
    not_found_counter = 0
    creds = get_credentials(api)

    with session_scope() as db_session:
        metas = retrieve_values(
            db_session, WCSourceMeta, 'meta', wcsbid=batch_id)
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
                        res = evaluate_response(res)
                        if res:
                            found_counter += 1
                            # convert from string to xml (or remain as string?)
                            doc = string2xml(res)
                            # persist
                            res = insert_or_ignore(
                                db_session, WCHit, wcsmid=m.wcsmid,
                                hit=True, search_marcxml=doc)
                        else:
                            not_found_counter += 1
                            res = insert_or_ignore(
                                db_session, WCHit, wcsmid=m.wcsmid,
                                hit=False, search_marcxml=None)

                        hits.set(str(found_counter))
                        nohits.set(str(not_found_counter))

                elif m.meta.issn:
                    # query by ISSN
                    pass
                elif m.meta.upc:
                    # query by UPC
                    pass
                update_progbar(progbar)
                processed_counter += 1

        db_session.flush()

        # verify found matches meet set criteria
        with MetadataSession(creds) as session:
            metas = retrieve_related(
                db_session, WCSourceMeta, 'wchit', wcsbid=batch_id)
            for m in metas:
                for x in m.wchit:
                    if x.hit:
                        oclcNo = get_oclcNo(x.search_marcxml)
                        res = request_record(session, oclcNo)
                        if res:
                            xml_record = extract_record_from_response(res)
                            update_record(
                                db_session, WCHit, x.wchid,
                                match=oclcNo,
                                match_marcxml=xml_record)

                            # check if meet criteria
                            if meets_global_criteria(xml_record) and \
                                    meets_user_criteria(
                                        xml_record,
                                        encode_level,
                                        rec_type,
                                        cat_rules,
                                        cat_source):

                                # add call number & write to file

                                callNum = create_callNum(
                                    xml_record, system, library)
                                initials = create_initials_field(
                                    system, library, 'TEST GENERATED BIB TEST')
                                marc_record = marcxml2array(xml_record)[0]
                                if callNum:
                                    marc_record.add_ordered_field(callNum)
                                    marc_record.add_ordered_field(initials)

                                    write_marc21(dst_fh, marc_record)

                            else:
                                # add counter for rejected bibs
                                pass

                update_progbar(progbar)



    # remove_temp_data(source_fh)
