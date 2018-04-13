# constructs Z3950/SierraAPI/PlatformAPI queries for particular resource


def platform_status_interpreter(response=None):
    """
    iterprets request status codes results and raises appropriate msg to
    be passed to gui
    args:
        response response return by Platform API
    return:
        (status, response) tuple (str, dict)
    """
    if response is not None:
        code = response.status_code
        if code == 200:
            status = 'hit'
        elif code == 404:
            status = 'nohit'
        elif code == 405:
            # log invalid endpoint (method)
            status = 'error'
        elif code >= 500:
            status = 'error'
        else:
            # log for examination
            print 'Platform returned unidentified status code: {}'.format(response.status_code)
            status = None
            print response.text
            print response.status_code
    else:
        status = None
    return status


def query_manager(request_dst, session, bibmeta, matchpoint):
    """
    picks api endpoint and runs the query
    return:
        list of InhouseBibMeta instances
    """
    if request_dst == 'PlatformAPIs':
        # exceptions raised again?
        if matchpoint == '020':
            print '020 matchpoint'
            if len(bibmeta.t020) > 0:
                print 'keywords: {}'.format(bibmeta.t020)
                response = session.query_bibStandardNo(keywords=bibmeta.t020)
            else:
                # do not attempt even to make a request to API
                response = None
        elif matchpoint == '024':
            print '024 matchpoint'
            if len(bibmeta.t024) > 0:
                print 'keywords: {}'.format(bibmeta.t024)
                response = session.query_bisStandardNo(keywords=bibmeta.t024)
            else:
                response = None
        elif matchpoint == 'sierra_id':
            print 'sierraID matchpoint'
            if bibmeta.sierraID is not None:
                print 'keywords: {}'.format(bibmeta.sierraID)
                # sierraID must be passed as a list to query_bibId
                response = session.query_bibId(keywords=[bibmeta.sierraID])
            else:
                response = None
        elif matchpoint == '001':
            print '001 matchpoint'
            if bibmeta.t001 is not None:
                print 'keywords: {}'.format(bibmeta.t001)
                response = session.query_bibControlNo(keywords=bibmeta.t001)
            else:
                response = None
        else:
            raise ValueError(
                'unsupported matchpoint specified: {}'.format(
                    matchpoint))

        status = platform_status_interpreter(response)

        if response is not None:
            response = response.json()
        return (status, response)
    elif request_dst == 'SierraAPIs':
        pass
    elif request_dst == 'Z3950s':
        pass
    else:
        raise ValueError('invalid query destionation provided')
