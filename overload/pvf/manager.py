# handles and oversees processing of vendor records (top level below gui)
# logging and passing exception to gui happens here
from datetime import datetime, date
import base64
import shelve
import logging
from requests.exceptions import ConnectionError, Timeout


from bibs.bibs import VendorBibMeta, read_marc21, \
    create_target_id_field, write_marc21, check_sierra_id_presence, \
    create_fields_from_template
from bibs.crosswalks import platform2meta
from pvf.vendors import vendor_index, identify_vendor, get_query_matchpoint
from pvf import queries
from pvf import reports
from analyzer import PVR_NYPLReport
from connectors import platform
from setup_dirs import USER_DATA, BATCH_STATS, BATCH_META
from connectors.platform import PlatformSession
from errors import OverloadError, APITokenExpiredError, APITokenError
from datastore import session_scope, Vendor, \
    PVR_Batch, PVR_File
from db_worker import insert_or_ignore


module_logger = logging.getLogger('overload_console.pvr_manager')


def run_platform_queries(api_name, session, meta, matchpoint):
    module_logger.info('Running platform query.') 
    try:
        result = queries.query_manager(
            api_name, session, meta, matchpoint)
        return result
    except APITokenExpiredError:
        # close current session and start over (silently)
        module_logger.debug('Expired token. Requesting new one.')
        session.close()
        session = open_platform_session(api_name)
        result = queries.query_manager(
            api_name, session, meta, matchpoint)
    except ConnectionError as e:
        module_logger.error('ConnectionError')
        session.close()
        raise OverloadError(e)
    except Timeout as e:
        session.close()
        raise OverloadError(e)


def open_platform_session(api_name=None):
    """
    wrapper around platform authorization and platform session obj
    args:
        api_type str
        api_name str
    return:
        session obj
    """
    reusing_token = False
    module_logger.info('Opening platform session')

    try:
        ud = shelve.open(USER_DATA, writeback=True)

        # retrieve specified Platform authorization
        conn_data = ud['PlatformAPIs'][api_name]
        client_id = base64.b64decode(conn_data['client_id'])
        client_secret = base64.b64decode(
            conn_data['client_secret'])
        auth_server = conn_data['oauth_server']
        base_url = conn_data['host']
        last_token = conn_data['last_token']  # encrypt?

        # check if valid token exists and reuse if can
        if last_token is not None:
            if last_token.get('expires_on') < datetime.now():
                # token expired, request new one
                module_logger.info(
                    'Platform token expired. Requesting new one.')
                auth = platform.AuthorizeAccess(
                    client_id, client_secret, auth_server)
                token = auth.get_token()
            else:
                module_logger.info(
                    'Last Platform token still valid. Re-using.')
                reusing_token = True
                token = last_token
        else:
            module_logger.info('Requesting Platform access token.')
            auth = platform.AuthorizeAccess(
                client_id, client_secret, auth_server)
            token = auth.get_token()

        # save token for reuse
        if not reusing_token:
            module_logger.debug('Saving Platform token for reuse')
            print 'saving token to shelf'
            ud['PlatformAPIs'][api_name]['last_token'] = token

    except KeyError as e:
        module_logger.critical(
            'KeyError in user_data: api name: {}. Error msg:{}'.format(
                api_name, e))
        raise OverloadError(
            'Error parsing user_data while retrieving connection info')

    except ValueError as e:
        module_logger.critical(
            e)

    except APITokenError as e:
        module_logger.error(
            'Unable to obtain Platform access token. Error: {}'.format(
                e))
        raise OverloadError(e)
    except ConnectionError as e:
        module_logger.critical(
            'Unable to obtain Platform access token. Error: {}'.format(
                e))
        raise OverloadError(e)
    except Timeout as e:
        module_logger.error(
            'Unable to obtain Platform access token. Error: {}'.format(
                e))
        raise OverloadError(e)

    finally:
        ud.close()

    # open Platform session
    try:
        session = PlatformSession(base_url, token)
        return session
    except ValueError as e:
        module_logger.error(e)
        raise OverloadError(e)
    except APITokenExpiredError:
        module_logger.critical(e)
        raise OverloadError(e)


def run_processing(
    files, system, library, agent, api_type, api_name,
        output_directory, progbar):
    # tokens and sessions are opened on this level

    module_logger.info('PVR process launched.')
    # determine destination API
    if api_type == 'Platform API':
        module_logger.debug('Connecting to Platform API')
        session = open_platform_session(api_name)
    elif api_type == 'Z3950':
        print 'parsing Z3950 settings'
    elif api_type == 'Sierra API':
        print 'parsing SierraAPI settings'

    # clean-up batch metadata & stats
    batch = shelve.open(BATCH_META, writeback=True)
    batch.clear()
    batch['timestamp'] = datetime.now()
    batch['system'] = system
    batch['library'] = library
    batch['agent'] = agent
    batch['file_names'] = files

    stats = shelve.open(BATCH_STATS, writeback=True)
    stats.clear()

    # run queries and results analysis for each bib in each file
    n = 0
    f = 0
    for file in files:
        f += 1
        reader = read_marc21(file)

        rules = './rules/vendors.xml'
        vx = vendor_index(rules, system, agent)

        for bib in reader:
            n += 1
            if agent == 'cat':
                vendor = identify_vendor(bib, vx)  # in SEL or ACQ scenario vendor provided via GUI
            else:
                print 'sel & acq will identify vendor by selecting a template'
            meta_in = VendorBibMeta(bib, vendor=vendor, dstLibrary=library)
            query_matchpoints = get_query_matchpoint(vendor, vx)

            # on this level I should know if the bib should be requeried
            # result must be evaluated in queries module, here action on
            # the evaluation
            if api_type == 'Platform API':
                print 'sending request to Platform'
                matchpoint = query_matchpoints['primary'][1]
                print 'primary matchpoint'
                result = run_platform_queries(
                    api_type, session, meta_in, matchpoint)

                # query_manager returns tuple (status, response in json)
                meta_out = []
                if result[0] == 'hit':
                    meta_out = platform2meta(result[1])
                elif result[0] == 'nohit':
                    # requery with alternative matchpoint
                    if 'secondary' in query_matchpoints:
                        print 'secondary matchpoint'
                        matchpoint = query_matchpoints['secondary'][1]
                        result = run_platform_queries(
                            api_type, session, meta_in, matchpoint)
                        if result[0] == 'hit':
                            meta_out = platform2meta(result[1])
                        elif result[0] == 'error':
                            raise OverloadError('Platform server error')
                elif result[0] == 'error':
                    raise OverloadError('Platform server error')

            elif 'api_type' == 'Z3950s':
                print 'sending reuqest to Z3950'
            elif 'api_type' == 'Sierra APIs':
                print 'sending request to SierraAPI'
            else:
                module_logger.error('Invalid api_type')

            if system == 'nypl':
                analysis = PVR_NYPLReport(agent, meta_in, meta_out)
            elif system == 'bpl':
                # analysis = PVR_BPLReport(agent, meta_in, meta_out)
                pass

            # save analysis to shelf
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
            bib.leader = bib.leader[:9] + 'a' + bib.leader[10:]
            sierra_id_present = check_sierra_id_presence(
                system, bib)
            if not sierra_id_present and \
                    analysis['target_sierraId'] is not None:
                try:
                    bib.add_field(
                        create_target_id_field(
                            system, analysis['target_sierraId']))
                except ValueError as e:
                    raise OverloadError(e)

            # add fields form bib & order templates
            if agent == 'cat':
                templates = vx[vendor].get('bib_template')
                if len(templates) > 0:
                    new_fields = create_fields_from_template(templates)
                    for field in new_fields:
                        bib.add_field(field)

            # append to appropirate output file
            if analysis['action'] == 'attach':
                write_marc21(fh_dups, bib)
            else:
                write_marc21(fh_new, bib)

            # update progbar
            progbar['value'] = n
            progbar.update()

    batch['processing_time'] = datetime.now() - batch['timestamp']
    batch['processed_files'] = f
    batch['processed_bibs'] = n
    batch.close()
    stats.close()

    # clean-up
    # close any open session if Platform or Sierra API has been used
    if api_type in ('Platform API', 'Sierra API') and session is not None:
        session.close()
        print 'session closed'


def save_stats():
    batch = shelve.open(BATCH_META)
    timestamp = batch['timestamp']
    system = batch['system']
    library = batch['library']
    agent = batch['agent']
    file_qty = len(batch['file_names'])
    batch.close()

    df = reports.shelf2dataframe(BATCH_STATS)
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
