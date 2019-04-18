import csv
import logging
import shelve


from bibs import BibOrderMeta
from errors import OverloadError
from logging_setup import LogglyAdapter
from pvf.platform_comms import open_platform_session, platform_queries_manager
from setup_dirs import USER_DATA


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def run_platform_queries(api_type, session, meta_in, matchpoint):
    try:
        results = platform_queries_manager(
            api_type, session, meta_in, matchpoint)
        return results
    except OverloadError:
        raise


def launch_process(
        system, library, target, id_type, output, source_fh, dst_fh, progbar):
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
        print(target)
        user_data.close()

    if target['method'] == 'Platform API':
        if id_type == 'ISBN':
            matchpoint = '020'
        elif id_type == 'ISSN':
            matchpoint = '022'
        elif id_type == 'UPC':
            matchpoint = '024'
        elif id_type == 'OCLC #':
            matchpoint = '001'
        else:
            raise ValueError

        for i in ids:
            # meta = BibOrderMeta(
            #     )
            result = platform_queries_manager(
                target['method'], session, meta, matchpoint)

