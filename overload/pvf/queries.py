# constructs Z3950/SierraAPI/PlatformAPI queries for particular resource


def status_interpreter(response):
    """
    iterprets request status codes results and raises appropriate msg to
    be passed to gui
    """
    if response is not None:
        return (response.status_code, response.json())
    else:
        return (None, None)


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
                response = session.query_standardNo(keywords=bibmeta.t020)
            else:
                # do not attempt even to make a request to API
                response = None
        elif matchpoint == '024':
            print '024 matchpoint'
            if len(bibmeta.t024) > 0:
                response = session.query_standardNo(keywords=bibmeta.t024)
            else:
                response = None
        elif matchpoint == '945':
            if bibmeta.sierraID is not None:
                # sierraID must be passed as a list to query_bibId
                response = session.query_bibId(keywords=[bibmeta.sierraID])
            else:
                response = None
        elif matchpoint == '001':
            if bibmeta.t001 is not None:
                # endpoint does not exist yet
                # (must be requested from the Digital)
                # response = session.query_standardNo(keywords=bibmeta.t001)
                pass
            else:
                response = None
        result = status_interpreter(response)
        return result
    elif request_dst == 'SierraAPIs':
        pass
    elif request_dst == 'Z3950s':
        pass
    else:
        raise ValueError('invalid query destionation provided')
