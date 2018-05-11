# module responsible for PVF communication with Platform

import shelve
import logging
import base64
from datetime import datetime
from requests.exceptions import ConnectionError, Timeout

from connectors.platform import AuthorizeAccess, PlatformSession
from pvf import queries
from errors import OverloadError, APITokenError, APITokenExpiredError
from setup_dirs import USER_DATA


module_logger = logging.getLogger('overload_console.pvr_plat_comms')


def open_platform_session(api_name=None):
    """
    wrapper around platform authorization and platform session obj
    args:
        api_type str
        api_name str
    return:
        session obj
    """
    module_logger.info('Preping to open Platform session.')
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
        last_token = conn_data['last_token']  # encrypt?

        # check if valid token exists and reuse if can
        if last_token is not None:
            if last_token.get('expires_on') < datetime.now():
                # token expired, request new one
                module_logger.info(
                    'Platform token expired. Requesting new one.')
                auth = AuthorizeAccess(
                    client_id, client_secret, auth_server)
                token = auth.get_token()
            else:
                module_logger.info(
                    'Last Platform token still valid. Re-using.')
                reusing_token = True
                token = last_token
        else:
            module_logger.info('Requesting Platform access token.')
            auth = AuthorizeAccess(
                client_id, client_secret, auth_server)
            token = auth.get_token()

        # save token for reuse
        if not reusing_token:
            module_logger.debug('Saving Platform token for reuse.')
            ud['PlatformAPIs'][api_name]['last_token'] = token

    except KeyError as e:
        module_logger.critical(
            'KeyError in user_data: api name: {}. Error msg:{}'.format(
                api_name, e))
        raise OverloadError(
            'Error parsing user_data while retrieving connection info')

    except ValueError as e:
        module_logger.critical(e)
        raise OverloadError(e)

    except APITokenError as e:
        module_logger.error(e)
        raise OverloadError(e)

    except ConnectionError as e:
        module_logger.critical(e)
        raise OverloadError(e)

    except Timeout as e:
        module_logger.error(e)
        raise OverloadError(e)

    finally:
        ud.close()

    # open Platform session
    try:
        module_logger.info('Auth obtained. Opening Platform session.')
        session = PlatformSession(base_url, token)
        return session

    except ValueError as e:
        module_logger.error(e)
        raise OverloadError(e)

    except APITokenExpiredError:
        module_logger.critical(e)
        raise OverloadError(e)


def platform_queries_manager(api_type, session, meta, matchpoint):
    """
    Oversees queries sent to platform
    args:
        api_type
        session obj
        meta obj
        matchpoint
    return:
        query result
    """
    module_logger.info('Making new Platform request.')
    try:
        result = queries.query_runner(
            api_type, session, meta, matchpoint)
        return result

    except APITokenExpiredError:
        session.close()
        raise APITokenExpiredError(
            'Unable to perform query. Platform token expired.')

    except ConnectionError as e:
        module_logger.error(
            'ConnectionError while running Platform queries. '
            'Closing session and terminating processing.')
        session.close()
        raise OverloadError(e)

    except Timeout as e:
        module_logger.error(
            'Timeout error while running Platform queries. '
            'Closing session and terminating processing')
        session.close()
        raise OverloadError(e)

    except ValueError as e:
        session.close()
        module_logger.error(
            e)
        raise OverloadError(e)
