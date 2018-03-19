# handles and oversees processing of vendor records (top level below gui)
# logging and passing exception to gui happens here
from datetime import datetime
import base64
import shelve
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout


from bibs.bibs import VendorBibMeta, read_marc21
from pvf.vendors import vendor_index, identify_vendor, get_query_matchpoint
from pvf import queries
from connectors import platform
from setup_dirs import USER_DATA
from connectors.platform import PlatformSession
from connectors.errors import APITokenExpiredError, APITokenError, Error


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
    except ConnectTimeout as e:
        session.close()
        raise Error(e)
    except ReadTimeout as e:
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
            except ConnectTimeout as e:
                # log
                raise Error(e)
            except ReadTimeout as e:
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


def run_processing(files, system, library, api_type, api_name):
    # tokens and sessions are opened on this level

    # determine destination API
    if api_type == 'PlatformAPIs':
        session = open_platform_session(api_name)
    elif api_type == 'Z3950s':
        print 'parsing Z3950 settings'
    elif api_type == 'SierraAPIs':
        print 'parsing SierraAPI settings'

    # run queries and results analysis for each bib in each file
    for file in files:
        reader = read_marc21(file)

        rules = './rules/vendors.xml'
        vx = vendor_index(rules, system)
        # print 'vendor_index:', vx

        for bib in reader:
            vendor = identify_vendor(bib, vx)
            meta = VendorBibMeta(bib, vendor=vendor, dstLibrary=library)
            query_matchpoints = get_query_matchpoint(vendor, vx)

            # on this level I should know if the bib should be requeried
            # result must be evaluated in queries module, here action on
            # the evaluation
            if api_type == 'PlatformAPIs':
                print 'sending request to Platform'
                matchpoint = query_matchpoints['primary']
                print 'primary matchpoint'
                result = run_platform_queries(
                    api_type, session, meta, matchpoint)

                # query_manager returns tuple (status, response in json)
                if result[0] == 'hit':
                    print result[1]
                elif result[0] == 'nohit':
                    # requery with alternative matchpoint
                    print 'secondary matchpoint'
                    matchpoint = query_matchpoints['secondary']
                    result = run_platform_queries(
                        api_type, session, meta, matchpoint)
                elif result[0] == 'error':
                    raise ConnectionError('Platform server error')

                print 'status: {}'.format(result[0])
                print result[1], '\n'
            elif 'api_type' == 'Z3950s':
                print 'sending reuqest to Z3950'
            elif 'api_type' == 'SierraAPIs':
                print 'sending request to SierraAPI'

    # clean-up
    # close any open session if Platform or Sierra API has been used
    if api_type in ('PlatformAPIs', 'SierraAPIs') and session is not None:
        session.close()
        print 'session closed'
