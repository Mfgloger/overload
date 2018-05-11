# handles and oversees processing of vendor records (top level below gui)
# logging and passing exception to gui happens here
from datetime import datetime, date
import shelve
import logging
from sqlalchemy.exc import IntegrityError


from bibs.bibs import VendorBibMeta, read_marc21, \
    create_target_id_field, write_marc21, check_sierra_id_presence, \
    check_sierra_format_tag_presence, create_field_from_template, \
    db_template_to_960, db_template_to_961, db_template_to_949
from bibs.crosswalks import platform2meta
from platform_comms import open_platform_session, platform_queries_manager
from pvf.vendors import vendor_index, identify_vendor, get_query_matchpoint
from pvf import reports
from analyzer import PVR_NYPLReport
from setup_dirs import BATCH_STATS, BATCH_META
from errors import OverloadError, APITokenExpiredError
from datastore import session_scope, Vendor, \
    PVR_Batch, PVR_File, NYPLOrderTemplate
from db_worker import insert_or_ignore, retrieve_values, \
    retrieve_record, update_nypl_template, delete_record


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
        template, output_directory, progbar):

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
    batch['template'] = template
    batch['file_names'] = files
    module_logger.debug(
        'BATCH_META new data: {}, {}, {}, {}, {}, {}'.format(
            timestamp, system, library, agent, template, files))

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
            elif agent == 'sel':
                # default matchpoints 020 than 001 for all
                if system == 'nypl':
                    query_matchpoints = dict()
                    with session_scope() as db_session:
                        trec = retrieve_record(
                            db_session, NYPLOrderTemplate, tName=template)

                        if trec.match1st == 'sierra_id':
                            query_matchpoints['primary'] = (
                                'id', trec.match1st)
                        else:
                            query_matchpoints['primary'] = (
                                'tag', trec.match1st)
                        if trec.match2nd is not None:
                            if trec.match2nd == 'sierra_id':
                                query_matchpoints['secondary'] = (
                                    'id', trec.match2nd)
                            else:
                                query_matchpoints['secondary'] = (
                                    'tag', trec.match2nd)
                        if trec.match3rd is not None:
                            if trec.match3rd == 'sierra_id':
                                query_matchpoints['tertiary'] = (
                                    'id', trec.match3rd)
                            else:
                                query_matchpoints['tertiary'] = (
                                    'tag', trec.match3rd)
                else:
                    raise OverloadError(
                        'selection workflow for BPL not implemented yet')

                # vendor code
                vendor = get_vendor_from_template(template)
                if vendor is None:
                    # do not apply but keep for stats
                    vendor == 'UNKNOWN'
            else:
                # acq workflows
                module_logger.warning(
                    'ACQ workflows for vendor identification '
                    'has not been implemented yet.')
                raise OverloadError(
                    'Acquisition workflows not yet implemented.')

            if vendor == 'UNKNOWN':
                module_logger.warning(
                    'Encounted unidentified vendor in record # : {} '
                    'in file {}.'.format(n, file))

            # determine vendor bib meta
            meta_in = VendorBibMeta(bib, vendor=vendor, dstLibrary=library)
            module_logger.debug('Vendor bib meta: {}'.format(str(meta_in)))

            # Platform API workflow
            if api_type == 'Platform API':
                matchpoint = query_matchpoints['primary'][1]
                module_logger.debug(
                    'Using primary marchpoint: {}.'.format(
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
                            'Using secondary marchpoint: {}.'.format(
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
                        elif result[0] == 'nohit':
                            # run query for the 3rd matchpoint
                            if 'tertiary' in query_matchpoints:
                                matchpoint = query_matchpoints['tertiary'][1]
                                module_logger.debug(
                                    'Using tertiary marchpoint: {}.'.format(
                                        matchpoint))

                                # run platform request for the tertiary 
                                # matchpoint
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
                                if result[0] == 'hit':
                                    meta_out = platform2meta(result[1])
                                elif result[0] == 'error':
                                    raise OverloadError(
                                        'Platform server error.')
                        elif result[0] == 'error':
                            raise OverloadError('Platform server error.')
                    else:
                        module_logger.debug(
                            'No secondary matchpoint specified. '
                            'Ending queries.')
                elif result[0] == 'error':
                    raise OverloadError('Platform server error.')

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
            if agent == 'cat':
                fh_dups = output_directory + '/{}.DUP-0.mrc'.format(
                    date_today)
                fh_new = output_directory + '/{}.NEW-0.mrc'.format(
                    date_today)
            elif agent == 'sel':
                fh = output_directory + '/{}-{}.FILE-0.mrc'.format(
                    date_today, vendor)
            elif agent == 'acq':
                fh_dups = output_directory + '/{}-{}.DUP-0.mrc'.format(
                    date_today, vendor)
                fh_new = output_directory + '/{}-{}.NEW-0.mrc'.format(
                    date_today, vendor)

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
            elif agent in ('sel', 'acq'):
                # batch template details should be retrieved instead for the
                # whole batch = no need to pull it for each bib
                with session_scope() as db_session:
                    trec = retrieve_record(
                        db_session, NYPLOrderTemplate, tName=template)

                    new_fields = []
                    for t960 in bib.get_fields('960'):
                        new_field = db_template_to_960(trec, t960)
                        if new_field:
                            new_fields.append(new_field)
                    if '960' in bib:
                        bib.remove_fields('960')
                    for field in new_fields:
                        bib.add_field(field)

                    new_fields = []
                    for t961 in bib.get_fields('961'):
                        new_field = db_template_to_961(trec, t961)
                        if new_field:
                            new_fields.append(new_field)
                    if '961' in bib:
                        bib.remove_fields('961')
                    for field in new_fields:
                        bib.add_field(field)

                    if trec.bibFormat and \
                            not check_sierra_format_tag_presence(bib):
                        new_field = db_template_to_949(trec.bibFormat)
                        bib.add_field(new_field)

            # append to appropirate output file
            if agent in ('cat', 'acq'):
                if analysis['action'] == 'attach':
                    module_logger.info(
                        'Appending vendor record to the dup file.')
                    write_marc21(fh_dups, bib)
                else:
                    module_logger.info(
                        'Appending vendor record to the new file.')
                    write_marc21(fh_new, bib)
            else:
                module_logger.info(
                    'Appending vendor record to a file.')
                write_marc21(fh, bib)

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


def get_template_names():
    with session_scope() as session:
        values = retrieve_values(session, NYPLOrderTemplate, 'tName')
        return [x.tName for x in values]


def save_template(record):
    try:
        with session_scope() as session:
            insert_or_ignore(session, NYPLOrderTemplate, **record)
    except IntegrityError as e:
        module_logger.error(
            'IntegrityError on template save: {}'.format(e))
        raise OverloadError(
            'Duplicate/missing template name\n'
            'or missing primary matchpoint')


def update_template(otid, record):
    try:
        with session_scope() as session:
            update_nypl_template(session, otid, **record)
    except IntegrityError as e:
        module_logger.error(
            'IntegrityError on template update: {}'.format(e))
        raise OverloadError(
            'Duplicate/missing template name\n'
            'or missing primary matchpoint')


def delete_template(otid):
    with session_scope() as session:
        delete_record(session, NYPLOrderTemplate, otid=otid)


def get_vendor_from_template(template):
    with session_scope() as session:
        record = retrieve_record(
            session, NYPLOrderTemplate, tName=template)
        return record.vendor
