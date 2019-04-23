import csv
import logging
import shelve


from bibs.bibs import BibOrderMeta
from errors import OverloadError, APITokenExpiredError
from logging_setup import LogglyAdapter
from bibs.crosswalks import platform2meta, bibs2meta
from pvf.analyzer import PVR_NYPLReport, PVR_BPLReport
from pvf.platform_comms import open_platform_session, platform_queries_manager
from setup_dirs import USER_DATA
from pvf.z3950_comms import z3950_query_manager

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
        source_fh: str, path to source file
        dst_fh: str, path to destination file
        progbar: tkinter widget

    """

    # calc progbar maximum
    ids = []
    with open(source_fh) as source:
        reader = csv.reader(source)
        # skip header
        reader.next()
        c = 0
        for row in reader:
            rid = row[0].strip()
            if rid:
                c += 1
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
        meta_in = BibOrderMeta()  # like vendor meta in PVR
        meta_in.dstLibrary = library
        if id_type == 'ISBN':
            meta_in.t020 = [i]
        elif id_type == 'ISSN':
            meta_in.t022 = [i]
        elif id_type == 'UPC':
            meta_in.t024 = [i]
        elif id_type == 'OCLC #':
            meta_in.t001 = i

        # query NYPL Platform
        if target['method'] == 'Platform API':
            try:
                print('query')
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

        if analysis.target_sierraId:
            target_sierraId = 'b{}a'.format(analysis.target_sierraId)
            with open(dst_fh, 'a') as csvfile:
                out = csv.writer(
                    csvfile, delimiter=' ',
                    lineterminator='\n',
                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
                out.writerow([target_sierraId])
        progbar['value'] += 1
        progbar.update()
