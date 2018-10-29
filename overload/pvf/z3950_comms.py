import logging


from errors import OverloadError
from pvf import queries
from logging_setup import LogglyAdapter
from PyZ3950.zoom import ConnectionError


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


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
    module_logger.debug('Making new Z3950 request to: {}'.format(
        target['host']))
    try:
        result = queries.query_runner(
            'Z3950', target, meta, matchpoint)
        return result
    except ConnectionError:
        module_logger.error('Z3950 Connection error on host {}'.format(
            target['host']))
        raise OverloadError(
            'Connection error. Unable to reach Z3950 host: {}.'.format(
                target))
    except ValueError:
        module_logger.error(
            'Z3950 ValueError on target parameters {}'.format(
                target))
        raise OverloadError(
            'Z3950 target not provided')
