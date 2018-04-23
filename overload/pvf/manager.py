# handles and oversees processing of vendor records (top level below gui)
# logging and passing exception to gui happens here
from datetime import datetime, date
import shelve
import logging
# from requests.exceptions import ConnectionError, Timeout


from bibs.bibs import VendorBibMeta, read_marc21, \
    create_target_id_field, write_marc21, check_sierra_id_presence, \
    create_field_from_template
from bibs.crosswalks import platform2meta
from platform_comms import open_platform_session, platform_queries_manager
from pvf.vendors import vendor_index, identify_vendor, get_query_matchpoint
from pvf import reports
from analyzer import PVR_NYPLReport
from setup_dirs import BATCH_STATS, BATCH_META
from errors import OverloadError, APITokenExpiredError, APITokenError
from datastore import session_scope, Vendor, \
    PVR_Batch, PVR_File
from db_worker import insert_or_ignore


module_logger = logging.getLogger('overload_console.pvr_manager')


def run_platform_queries(api_type, session, meta_in, matchpoint):
    try:
        results = platform_queries_manager(
            api_type, session, meta_in, matchpoint)
        return results
    except OverloadError:
        raise


def run_processing(
    files, system, library, agent, api_type, api_name,
        output_directory, progbar):

    module_logger.info('PVR process launched.')

    # tokens and sessions are opened on this level

    # determine destination API
    if api_type == 'Platform API':
        module_logger.info('Connecting Platform API session.')
        try:
            session = open_platform_session(api_name)
        except OverloadError:
            raise
    elif api_type == 'Z3950':
        module_logger.info('Connecting to Z3950')
    elif api_type == 'Sierra API':
        module_logger.info('Connecting to Sierra API')

    # clean-up batch metadata & stats
    module_logger.debug('Opening BATCH_META.')
    batch = shelve.open(BATCH_META, writeback=True)
    batch.clear()
    module_logger.debug(
        'BATCH_META has been emptied from previous content.')
    timestamp = datetime.now()
    batch['timestamp'] = timestamp
    batch['system'] = system
    batch['library'] = library
    batch['agent'] = agent
    batch['file_names'] = files
    module_logger.debug(
        'BATCH_META new data: {}, {}, {}, {}, {}'.format(
            timestamp, system, library, agent, files))

    stats = shelve.open(BATCH_STATS, writeback=True)
    stats.clear()
    module_logger.debug(
        'BATCH_STATS has been emptied from previous content.')

    # create reference index
    module_logger.debug(
        'Creatig vendor index data for {}-{}'.format(
            system, agent))
    rules = './rules/vendors.xml'
    vx = vendor_index(rules, system, agent)  # wrap in exception?

    # run queries and results analysis for each bib in each file
    n = 0
    f = 0
    for file in files:
        f += 1
        module_logger.debug(
            'Opening new MARC reader for file: {}'.format(
                file))
        reader = read_marc21(file)

        for bib in reader:
            n += 1

            if agent == 'cat':
                vendor = identify_vendor(bib, vx)

                try:
                    query_matchpoints = get_query_matchpoint(vendor, vx)
                    module_logger.debug(
                        'Cat vendor index has following query matchpoints: '
                        '{} for vendor {}.'.format(
                            query_matchpoints, vendor))

                except KeyError:
                    module_logger.critical(
                        'Unable to match vendor {} with data '
                        'in cat vendor index'.format(
                            vendor))
            else:
                # sel & acq workflows
                # data pulled from db instead
                # rules xml file used only to seed db with basic info
                module_logger.warning(
                    'SEL & ACQ workflows for vendor identification '
                    'has not been implemented yet.')
                raise OverloadError(
                    'Selection & Acquisition workflows not implemented yet.')

            if vendor == 'UNKNOWN':
                module_logger.warning(
                    'Encounted unidentified vendor in record # : {} '
                    'in file {}'.format(n, file))

            # determine vendor bib meta
            meta_in = VendorBibMeta(bib, vendor=vendor, dstLibrary=library)
            module_logger.debug('Vendor bib meta: {}'.format(str(meta_in)))

            # Platform API workflow
            if api_type == 'Platform API':
                matchpoint = query_matchpoints['primary'][1]
                module_logger.debug(
                    'Using primary marchpoint: {}'.format(
                        matchpoint))
                try:
                    result = run_platform_queries(
                        api_type, session, meta_in, matchpoint)

                except APITokenExpiredError:
                    module_logger.info(
                        'Requesting new Platform token. Opening new session.')
                    session = open_platform_session(api_name)
                    result = platform_queries_manager(
                        api_type, session, meta_in, matchpoint)

                # run_patform_queries returns tuple (status, response in json)
                meta_out = []

                if result[0] == 'hit':
                    meta_out = platform2meta(result[1])

                elif result[0] == 'nohit':
                    # requery with alternative matchpoint
                    if 'secondary' in query_matchpoints:
                        matchpoint = query_matchpoints['secondary'][1]
                        module_logger.debug(
                            'Using secondary marchpoint: {}'.format(
                                matchpoint))

                        # run platform request for the secondary matchpoint
                        try:
                            result = run_platform_queries(
                                api_type, session, meta_in, matchpoint)

                        except APITokenExpiredError:
                            module_logger.info(
                                'Requesting new Platform token. '
                                'Opening new session.')

                            session = open_platform_session(api_name)
                            result = run_platform_queries(
                                api_type, session, meta_in, matchpoint)
                            # other exceptions raised in run_platform_queries

                        if result[0] == 'hit':
                            meta_out = platform2meta(result[1])
                        elif result[0] == 'error':
                            raise OverloadError('Platform server error')
                    else:
                        module_logger.debug(
                            'No secondary matchpoint specified. '
                            'Ending queries.')
                elif result[0] == 'error':
                    raise OverloadError('Platform server error')

            # queries performed via Z3950
            elif 'api_type' == 'Z3950s':
                module_logger.error('Z3950 is not yet implemented.')
                raise OverloadError('Z3950 is not yet implemented.')
            # queries performed via Sierra API
            elif 'api_type' == 'Sierra API':
                module_logger.error('Sierra API is not implemented yet.')
                raise OverloadError('Sierra API is not implemented yet.')
            else:
                module_logger.error('Invalid api_type')
                raise OverloadError('Invalid api_type encountered.')

            if system == 'nypl':
                analysis = PVR_NYPLReport(agent, meta_in, meta_out)
            elif system == 'bpl':
                # analysis = PVR_BPLReport(agent, meta_in, meta_out)
                pass

            # save analysis to shelf
            module_logger.info('Analyzing query results and vendor bib')
            analysis = analysis.to_dict()
            stats[str(n)] = analysis

            # determine mrc files namehandles
            date_today = date.today().strftime('%y%m%d')
            fh_dups = output_directory + '/{}.DUP-0.mrc'.format(
                date_today)
            fh_new = output_directory + '/{}.NEW-0.mrc'.format(
                date_today)

            # output processed records according to analysis
            # add Sierra bib id if matched

            # enforce utf-8 encoding in MARC leader
            bib.leader = bib.leader[:9] + 'a' + bib.leader[10:]

            sierra_id_present = check_sierra_id_presence(
                system, bib)
            module_logger.debug(
                'Checking if vendor bib has Sierra ID provided: '
                '{}'.format(sierra_id_present))

            if not sierra_id_present and \
                    analysis['target_sierraId'] is not None:

                try:
                    module_logger.info(
                        'Adding MARC field with target Sierra id '
                        'to vendor record: {}.'.format(
                            analysis['target_sierraId']))
                    bib.add_field(
                        create_target_id_field(
                            system, analysis['target_sierraId']))

                except ValueError as e:
                    module_logger.error(e)
                    raise OverloadError(e)

            # add fields form bib & order templates
            module_logger.info(
                'Adding template field(s) to the vendor record.')
            if agent == 'cat':
                templates = vx[vendor].get('bib_template')
                module_logger.debug(
                    'Selected CAT templates for {}: {}'.format(
                        vendor, templates))
                for template in templates:
                    # skip if present or always add

                    if template['option'] == 'skip':
                        if template['tag'] not in bib:
                            module_logger.debug(
                                'Field {} not present, adding '
                                'from template'.format(
                                    template['tag']))
                            new_field = create_field_from_template(template)
                            bib.add_field(new_field)
                        else:
                            module_logger.debug(
                                'Field {} found. Skipping.'.format(
                                    template['tag']))
                    elif template['option'] == 'add':
                        module_logger.debug(
                            'Field {} being added without checking '
                            'if already present'.format(
                                template['tag']))
                        new_field = create_field_from_template(template)
                        bib.add_field(new_field)

            # append to appropirate output file
            if analysis['action'] == 'attach':
                module_logger.info(
                    'Appending vendor record to the dup file.')
                write_marc21(fh_dups, bib)
            else:
                module_logger.info(
                    'Appending vendor record to the new file.')
                write_marc21(fh_new, bib)

            # update progbar
            progbar['value'] = n
            progbar.update()

    processing_time = datetime.now() - batch['timestamp']
    module_logger.info(
        'Batch stats: {} files, {} records, '
        'processing time: {}'.format(
            f, n, processing_time))
    batch['processing_time'] = processing_time
    batch['processed_files'] = f
    batch['processed_bibs'] = n
    batch.close()
    stats.close()

    # clean-up
    # close any open session if Platform or Sierra API has been used
    if api_type in ('Platform API', 'Sierra API') and session is not None:
        session.close()
        module_logger.info('Closing API session.')


def save_stats():
    module_logger.info('Saving batch stats.')
    batch = shelve.open(BATCH_META)
    timestamp = batch['timestamp']
    system = batch['system']
    library = batch['library']
    agent = batch['agent']
    file_qty = len(batch['file_names'])
    batch.close()

    try:
        df = reports.shelf2dataframe(BATCH_STATS)
    except ValueError:
        df = None

    if df is not None:
        stats = reports.create_stats(system, df)

        with session_scope() as session:
            # find out if timestamp already added
            # if not add records
            # add batch record
            record = insert_or_ignore(
                session, PVR_Batch,
                timestamp=timestamp,
                system=system,
                library=library,
                agent=agent,
                file_qty=file_qty)
            session.flush()
            bid = record.bid
            for row in stats.iterrows():
                name = row[1]['vendor']
                record = insert_or_ignore(session, Vendor, name=name)
                session.flush()
                vid = record.vid

                if system == 'nypl':
                    record = insert_or_ignore(
                        session, PVR_File,
                        bid=bid,
                        vid=vid,
                        new=row[1]['insert'],
                        dups=row[1]['attach'],
                        updated=row[1]['update'],
                        mixed=row[1]['mixed'],
                        other=row[1]['other'])
                else:
                    record = insert_or_ignore(
                        session, PVR_File,
                        bid=bid,
                        vid=vid,
                        new=row[1]['insert'],
                        dups=row[1]['attach'],
                        updated=row[1]['update'])
    else:
        module_logger.warning(
            'Unable to created dataframe from the BATCH_STATS.')
        raise OverloadError(
            'Encountered problems while trying to save statistics.')
