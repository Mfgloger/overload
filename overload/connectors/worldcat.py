import requests


BASE_URL = "http://www.worldcat.org"


class InvalidObject(Exception):
    """Invalid argument passed"""

    def __init__(self, message):
        self.message = message


class WorldcatSession(requests.Session):
    """
    Worldcat APIs wrapper
    args:
        access token
    """

    def __init__(self, base_url=BASE_URL, access_token=None):
        requests.Session.__init__(self)
        self.base_url = base_url
        self.access_token = access_token
        self.timeout = (5, 5)
        self.headers.update({
            'User-Agent': ''
        })


class WorldcatSearchSession(WorldcatSession):
    """ Interface for querying WorldCat using Search API.
        Search API uses Wskey Lite authorization method:
        https://www.oclc.org/developer/develop/authentication/wskey-lite.en.html
        args:
            wskey: str, Worldcat services key
    """

    def __init__(self, wskey=None):
        WorldcatSession.__init__(self)
        self.base_url += '/webservices/catalog/'
        self.wskey = wskey
        self.headers.update({
            'Accept': 'application/xml'
        })

        if not self.wskey:
            raise TypeError('Missing wskey argument')

    def lookup_by_isbn(self, isbn):
        """
        Use to get a record with the highest holdingsin marcxml
        format by ISNB.
        Warning: may return records using different cataloging language
        then English.
        args:
            isbn: str, ISBN number
        returns:
            response: class requests.models.Response, default
                      Worldcat format is marcxml
        """

        url = self.base_url + 'content/isbn/{}'.format(isbn)
        payload = {
            'wskey': self.wskey
        }
        # send request
        try:
            response = self.get(
                url, params=payload, timeout=self.timeout)
            return response
        except requests.exceptions.Timeout:
            # log error
            raise
        except requests.exceptions.ConnectionError:
            # log
            raise
