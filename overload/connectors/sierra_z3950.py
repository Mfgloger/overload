# handles Z3950 requests

from PyZ3950 import zoom


# query qualifiers use CCL specs
# more on CCL @ www.indexdata.com/yaz/doc/tools.html#CCL

Z3950_QUALIFIERS = {
    'isbn': '(1,7)',
    'issn': '(1,8)',
    'title': '(1,4)',
    'personalName': '(1,1)',
    'bib number': '(1,12)',
    'keyword': '(1,1016)'
}


def z3950_query(target=None, keyword=None, qualifier='(1,1016)',
                query_type='CCL'):
    if target is not None:
        host = target['host']
        database = target['database']
        port = target['port']
        syntax = target['syntax']
        user = target['user']
        password = target['password']

        try:
            if user is not None \
                    and password is not None:
                conn = zoom.Connection(
                    host, port,
                    user=user, password=password)
            else:
                conn = zoom.Connection(host, port)

            conn.databaseName = database
            conn.preferredRecordSyntax = syntax
            query_str = qualifier + '=' + keyword
            query = zoom.Query(query_type, query_str)
            res = conn.search(query)

            return True, res

        except zoom.ConnectionError:
            raise
    else:
        raise ValueError('Z3950 target not provided.')
