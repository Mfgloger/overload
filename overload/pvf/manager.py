# handles and oversees processing of vendor records (top level below gui)
# logging and passing exception to gui happens here
from datetime import datetime
import base64
import shelve
import pandas as pd
from requests.exceptions import ConnectionError, Timeout


from bibs.bibs import VendorBibMeta, read_marc21
from bibs.crosswalks import platform2meta
from pvf.vendors import vendor_index, identify_vendor, get_query_matchpoint
from pvf import queries
from analyzer import PVR_NYPLReport
from connectors import platform
from setup_dirs import USER_DATA, BATCH_STATS, BATCH_META
from connectors.platform import PlatformSession
from connectors.errors import APITokenExpiredError, APITokenError, Error
from datastore import session_scope


def run_platform_queries(api_name, session, meta, matchpoint):
    try:
        result = queries.query_manager(
            api_name, session, meta, matchpoint)
        return result
    except APITokenExpiredError:
        # close current session and start over (silently)
        session.close()
        session = open_platform_session(api_name)
        result = queries.query_manager(
            api_name, session, meta, matchpoint)
    except ConnectionError as e:
        session.close()
        raise Error(e)
    except Timeout as e:
        session.close()
        raise Error(e)


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
    try:
        ud = shelve.open(USER_DATA, writeback=True)
        # retrieve specified Platform authorization
        conn_data = ud['PlatformAPIs'][api_name]
        client_id = base64.b64decode(conn_data['client_id'])
        client_secret = base64.b64decode(
            conn_data['client_secret'])
        auth_server = conn_data['oauth_server']
        base_url = conn_data['host']
        last_token = conn_data['last_token']  # should it be encrypted

        # check if valid token exists and reuse if can
        if last_token is not None:
            if last_token.get('expires_on') < datetime.now():
                # token expired, request new one
                print 'requesting new token'
                auth = platform.AuthorizeAccess(
                    client_id, client_secret, auth_server)
                token = auth.get_token()
            else:
                print 'reusing token'
                reusing_token = True
                token = last_token
        else:
            print 'requesting token for the first time'
            auth = platform.AuthorizeAccess(
                client_id, client_secret, auth_server)
            try:
                token = auth.get_token()
            except APITokenError as e:
                # log
                raise Error(e)
            except ConnectionError as e:
                # log
                raise Error(e)
            except Timeout as e:
                # log
                raise Error(e)

        # save token for reuse
        if not reusing_token:
            print 'saving token to shelf'
            ud['PlatformAPIs'][api_name]['last_token'] = token

    except KeyError:
        raise ValueError(
            'Provided Platform connection setting does not exist')

    # open Platform session
    session = PlatformSession(base_url, token)

    ud.close()
    return session


def run_processing(files, system, library, agent, api_type, api_name):
    # tokens and sessions are opened on this level

    # determine destination API
    if api_type == 'PlatformAPIs':
        session = open_platform_session(api_name)
    elif api_type == 'Z3950s':
        print 'parsing Z3950 settings'
    elif api_type == 'SierraAPIs':
        print 'parsing SierraAPI settings'

    # clean-up batch metadata & stats
    batch = shelve.open(BATCH_META, writeback=True)
    batch.clear()
    batch['timestamp'] = datetime.now().strftime('%Y%M%d%H%M.%f')
    batch['system'] = system
    batch['library'] = library
    batch['agent'] = agent
    batch.close()

    stats = shelve.open(BATCH_STATS, writeback=True)
    stats.clear()

    # run queries and results analysis for each bib in each file
    n = 0
    for file in files:
        reader = read_marc21(file)

        rules = './rules/vendors.xml'
        vx = vendor_index(rules, system, agent)
        # print 'vendor_index:', vx

        for bib in reader:
            n += 1
            vendor = identify_vendor(bib, vx)  # in SEL or ACQ scenario vendor provided via GUI
            meta_in = VendorBibMeta(bib, vendor=vendor, dstLibrary=library)
            query_matchpoints = get_query_matchpoint(vendor, vx)

            # on this level I should know if the bib should be requeried
            # result must be evaluated in queries module, here action on
            # the evaluation
            if api_type == 'PlatformAPIs':
                print 'sending request to Platform'
                matchpoint = query_matchpoints['primary']
                print 'primary matchpoint'
                result = run_platform_queries(
                    api_type, session, meta_in, matchpoint)

                # query_manager returns tuple (status, response in json)
                meta_out = []
                if result[0] == 'hit':
                    meta_out = platform2meta(result[1])
                elif result[0] == 'nohit':
                    # requery with alternative matchpoint
                    print 'secondary matchpoint'
                    matchpoint = query_matchpoints['secondary']
                    result = run_platform_queries(
                        api_type, session, meta_in, matchpoint)
                    if result[0] == 'hit':
                        meta_out = platform2meta(result[1])
                    elif result[0] == 'error':
                        raise Error('Platform server error')
                elif result[0] == 'error':
                    raise Error('Platform server error')

            elif 'api_type' == 'Z3950s':
                print 'sending reuqest to Z3950'
            elif 'api_type' == 'SierraAPIs':
                print 'sending request to SierraAPI'

            if system == 'nypl':
                analysis = PVR_NYPLReport(agent, meta_in, meta_out)
            elif system == 'bpl':
                # analysis = PVR_BPLReport(agent, meta_in, meta_out)
                pass

            # save analysis to shelf
            analysis = analysis.to_dict()
            stats[str(n)] = analysis


    # clean-up
    # close any open session if Platform or Sierra API has been used
    if api_type in ('PlatformAPIs', 'SierraAPIs') and session is not None:
        session.close()
        print 'session closed'

    stats.close()

    create_stats_dataframe()


def create_stats_dataframe():
    stats = shelve.open(BATCH_STATS)
    frames = []
    for key, value in stats.iteritems():
        # print value
        frames.append(pd.DataFrame(value, index=[key]))
    df = pd.concat(frames, ignore_index=True)
    stats.close()
    return df


def archive():
    batch = shelve.open(BATCH_STATS)
    timestamp = batch['timestamp']

    with session_scope() as session:
        # insert_or_ingore(session, )
        pass

    batch.close()