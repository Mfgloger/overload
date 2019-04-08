# module controlling upgrade/catalog from Worldcat process
import csv

from bibs.bibs import (BibOrderMeta, parse_isbn)
from bibs.crosswalks import string2xml
from datastore import (session_scope, WCSourceBatch, WCSourceMeta, WCHit)
from db_worker import insert_or_ignore, delete_record, retrieve_values
from connectors.worldcat import (WorldcatSearchSession, evaluate_response)
from credentials import get_from_vault, evaluate_worldcat_creds


def store_meta(model, record):
    pass


def remove_temp_data(source_fh):
    with session_scope() as db_session:
        delete_record(db_session, WCSourceBatch, file=source_fh)


def get_credentials(api):
    creds = get_from_vault(api, 'Overload')
    return evaluate_worldcat_creds(creds)


def launch_process(source_fh, progbar, counter, hits, nohits,
                   id_type='isbn', api=None):
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
    # temp
    remove_temp_data(source_fh)

    # calculate max counter
    with open(source_fh, 'r') as file:
        reader = csv.reader(file)
        c = 0
        for row in reader:
            c +=1

        # update progbar here
        # update counter max

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
                if id_type == 'isbn':
                    for row in reader:
                        meta = BibOrderMeta(
                            isbn=[parse_isbn(row[0])])
                        insert_or_ignore(db_session, WCSourceMeta, wcsbid=batch_id, meta=meta)
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
        with WorldcatSearchSession(wskey=creds['key']) as session:
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
                            insert_or_ignore(
                                db_session, WCHit, wcsmid=m.wcsmid,
                                hit=True, marcxml=doc)
                        else:
                            not_found_counter += 1

                elif m.meta.issn:
                    # query by ISSN
                    pass
                elif m.meta.upc:
                    # query by UPC
                    pass
                processed_counter += 1

        db_session.flush()



    print(processed_counter)




    # remove_temp_data(source_fh)
