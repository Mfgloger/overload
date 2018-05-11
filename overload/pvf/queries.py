# constructs Z3950/SierraAPI/PlatformAPI queries for particular resource
import logging


module_logger = logging.getLogger('overload_console.pvr_queries')


def platform_status_interpreter(response=None):
    """
    iterprets request status codes results and raises appropriate msg to
    be passed to gui
    args:
        response response return by Platform API
    return:
        (status, response) tuple (str, dict)
    """
    module_logger.info('Interpreting response status code')
    if response is not None:
        code = response.status_code
        module_logger.debug(
            'Platform response status code: {}'.format(
                code))
        if code == 200:
            status = 'hit'
        elif code == 404:
            status = 'nohit'
        elif code == 405:
            module_logger.error(
                'Platform endpoint is not valid. '
                'Response text: {}'. format(
                    response.text))
            status = 'error'
        elif code >= 500:
            status = 'error'
        else:
            module_logger.error(
                'Platform returned unidentified '
                'status code: {}, text: {}'.format(
                    response.status_code,
                    response.text))
            status = None
    else:
        status = 'nohit'
    return status


def query_runner(request_dst, session, bibmeta, matchpoint):
    """
    picks api endpoint and runs the query
    return:
        list of InhouseBibMeta instances
    """
    if request_dst == 'Platform API':
        if matchpoint == '020':
            module_logger.debug(
                'Platform bibStandardNo endpoint request, '
                'keywords (020): {}'.format(
                    bibmeta.t020))
            if len(bibmeta.t020) > 0:
                response = session.query_bibStandardNo(keywords=bibmeta.t020)
            else:
                # do not attempt even to make a request to API
                response = None
        elif matchpoint == '024':
            module_logger.debug(
                'Platform bibStandardNo endpoint request, '
                'keywords (024): {}'.format(
                    bibmeta.t024))
            if len(bibmeta.t024) > 0:
                response = session.query_bibStandardNo(keywords=bibmeta.t024)
            else:
                response = None
        elif matchpoint == 'sierra_id':
            module_logger.debug(
                'Platform bibId endpoint request, '
                'keywords (sierra id): {}'.format(
                    bibmeta.sierraId))
            if bibmeta.sierraId is not None:
                # sierraID must be passed as a list to query_bibId
                response = session.query_bibId(keywords=[bibmeta.sierraId])
            else:
                response = None
        elif matchpoint == '001':
            module_logger.debug(
                'Platform bibControlNo endpoint request, '
                'keywords (001): {}'.format(
                    bibmeta.t001))
            if bibmeta.t001 is not None:
                response = session.query_bibControlNo(keywords=[bibmeta.t001])
            else:
                response = None
        else:
            module_logger.error(
                'Unsupported matchpoint specified: {}'.format(
                    matchpoint))
            raise ValueError(
                'unsupported matchpoint specified: {}'.format(
                    matchpoint))

        status = platform_status_interpreter(response)
        module_logger.debug('Platform response: {}'.format(
            status))

        if response is not None:
            module_logger.debug(
                'Converting Platform response to json')
            response = response.json()
        return (status, response)

    elif request_dst == 'Sierra API':
        pass
    elif request_dst == 'Z3950':
        pass
    else:
        raise ValueError(
            'Invalid query destionation provided: {}'.format(
                request_dst))
