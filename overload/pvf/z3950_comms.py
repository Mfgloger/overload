import logging


from connectors.sierra_z3950 import Z3950_QUALIFIERS, z3950_query
from pvf import queries
from errors import OverloadError
from setup_dirs import USER_DATA
from PyZ3950.zoom import ConnectionError


module_logger = logging.getLogger('overload_console.pvr_z3950_comms')


def z3950_query_manager(target, meta, matchpoint):
    """
    Oversees queries send to Sierra Z3950
    args:
        api_name
        meta obj
        matchpoint
    return:
        query result
    """
    module_logger.info('Making new Z3950 request to: {}'.format(
        target['host']))
    try:
        result = queries.query_runner(
            'Z3950', target, meta, matchpoint)
        return result
    except ConnectionError:
        raise OverloadError(
            'Connection error. Unable to reach Z3950 host.')
    except ValueError:
        raise OverloadError(
            'Z3950 target not provided')
