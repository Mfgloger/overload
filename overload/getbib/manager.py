from datetime import datetime
import csv
import logging
import os
import shelve


from bibs.bibs import BibOrderMeta
from errors import OverloadError, APITokenExpiredError
from logging_setup import LogglyAdapter
from bibs.crosswalks import platform2meta, bibs2meta
from pvf.analyzer import PVR_NYPLReport, PVR_BPLReport
from pvf.platform_comms import open_platform_session, platform_queries_manager
from setup_dirs import USER_DATA, GETBIB_REP
from pvf.z3950_comms import z3950_query_manager
from utils import save2csv


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def run_platform_queries(api_type, session, meta_in, matchpoint):
    try:
        results = platform_queries_manager(
            api_type, session, meta_in, matchpoint)
        return results
    except OverloadError:
        raise


def launch_process(
        system, library, target, id_type, action, source_fh, dst_fh,
        progbar, hit_counter, nohit_counter):
    """
    manages retrieval of bibs or bibs numbers based on
    args:
        system: str, NYPL or BPL
        library: str, branches or research
        target: dict, keys = name, method
        id_type: str, one of ISBN, ISSN, LCCN, OCLC number, or UPC
        output: str, MARC or bib #
        dst_fh: str, path to destination file
        progbar: tkinter widget

    """
    # temp report
    timestamp_start = datetime.now()
    try:
        os.remove(GETBIB_REP)
    except WindowsError:
        pass
    header = None

    # calc progbar maximum and dedup
    ids = []
    dups = set()
    with open(source_fh) as source:
        reader = csv.reader(source)
        # skip header
        reader.next()
        c = 0
        d = 0
        for row in reader:
            rid = row[0].strip()
            if rid:
                c += 1
                if rid in ids:
                    d += 1
                    dups.add(rid)
                else:
                    ids.append(rid)
        progbar['maximum'] = c

    # determine correct matchpoint based on id_type
    if id_type == 'ISBN':
        matchpoint = '020'
    elif id_type == 'ISSN':
        matchpoint = '022'
    elif id_type == 'UPC':
        matchpoint = '024'
    elif id_type == 'OCLC #':
        matchpoint = '001'
    else:
        raise OverloadError(
            'Query by {} not yet implemented'.format(
                id_type))

    # determine destination API
    if target['method'] == 'Platform API':
        module_logger.debug('Creating Platform API session.')
        try:
            session = open_platform_session(target['name'])
        except OverloadError:
            raise
    elif target['method'] == 'Z3950':
        module_logger.debug('retrieving Z3950 settings for {}'.format(
            target['name']))
        user_data = shelve.open(USER_DATA)
        target = user_data['Z3950s'][target['name']]
        user_data.close()

    for i in ids:
        meta_in = BibOrderMeta(
            system=system, dstLibrary=library)  # like vendor meta in PVR
        meta_in.dstLibrary = library
        if id_type == 'ISBN':
            meta_in.t020 = [i]
        elif id_type == 'ISSN':
            meta_in.t022 = [i]
        elif id_type == 'UPC':
            meta_in.t024 = [i]
        elif id_type == 'OCLC #':
            meta_in.t001 = i

        module_logger.debug(str(meta_in))

        # query NYPL Platform
        if target['method'] == 'Platform API':
            try:
                result = platform_queries_manager(
                    target['method'], session, meta_in, matchpoint)
            except APITokenExpiredError:
                module_logger.info(
                    'Platform token expired. '
                    'Requesting new one and opening new session.')
                session = open_platform_session(target['method'])
                result = platform_queries_manager(
                    target['method'], session, meta_in, matchpoint)

            meta_out = []
            if result[0] == 'hit':
                hit_counter.set(hit_counter.get() + 1)
                meta_out = platform2meta(result[1])
            elif result[0] == 'nohit':
                nohit_counter.set(nohit_counter.get() + 1)

        elif target['method'] == 'Z3950':
            meta_out = []
            status, bibs = z3950_query_manager(
                target, meta_in, matchpoint)
            if status == 'hit':
                hit_counter.set(hit_counter.get() + 1)
                meta_out = bibs2meta(bibs)
            elif status == 'nohit':
                nohit_counter.set(nohit_counter.get() + 1)

        if system == 'NYPL':
            analysis = PVR_NYPLReport('cat', meta_in, meta_out)
        elif system == 'BPL':
            analysis = PVR_BPLReport('cat', meta_in, meta_out)
        module_logger.debug(str(analysis))

        if not header:
            header = analysis.to_dict().keys()
            header.insert(0, 'pos')
            save2csv(GETBIB_REP, header)
        analysis.target_sierraId = 'b{}a'.format(analysis.target_sierraId)
        row = analysis.to_dict().values()
        row.insert(0, progbar['value'])
        save2csv(GETBIB_REP, row)

        progbar['value'] += 1
        progbar.update()

    # record data about the batch
    timestamp_end = datetime.now()
    user_data = shelve.open(USER_DATA)
    user_data['getbib_batch'] = {
        'timestamp': timestamp_start,
        'time_elapsed': timestamp_end - timestamp_start,
        'total_queries': c,
        'target': target,
        'hits': hit_counter.get(),
        'misses': nohit_counter.get(),
        'dup_count': d,
        'dups': dups
    }
    user_data.close()
