import requests
import wskey


BASE_URL = "http://www.worldcat.org"


class InvalidObject(Exception):
    """Invalid argument passed"""

    def __init__(self, message):
        self.message = message


def get_access_token(creds):
    """
    temp code - create own way to request token;
    for the moment use OCLC library
    """

    key = creds['key']
    secret = creds['secret']
    authenticating_institution_id = creds['authenticating_institution_id']
    context_institution_id = creds['context_institution_id']
    services = creds['scopes']

    # # Configure the wskey library object
    my_wskey = wskey.Wskey(
        key=key,
        secret=secret,
        options={'services': services})

    # print(my_wskey)

    # Get an access token
    access_token = my_wskey.get_access_token_with_client_credentials(
        authenticating_institution_id=authenticating_institution_id,
        context_institution_id=context_institution_id)

    return access_token


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


class WorldcatMetadataSession(WorldcatSession):
    """
    Interface for getting full records from Worldcat and setting library holdings
    """

    def __init__(self, access_token=None):
        WorldcatSession.__init__(self)

        if not access_token:
            raise AttributeError('Must include access token.')

        self.base_url = 'https://worldcat.org/bib/data/'
        # self.base_url = 'https://worldcat.org'
        # self.base_url += '/bib/data/'
        self.access_token = access_token
        # self.headers.update({
        #     # 'Accept': 'application/xml',
        #     'Authorization': 'Bearer ' + self.access_token
        # })
        print(self.headers)
        print(self.base_url)

    def get_record(self, oclcNo):
        url = self.base_url + '{}'.format(oclcNo)
        # send request
        try:
            response = self.get(
                url, timeout=self.timeout)
            print(response.url)
            return response
        except requests.exceptions.Timeout:
            # log error
            raise
        except requests.exceptions.ConnectionError:
            # log
            raise

    def set_holdings(self):
        pass

    def prep_request(self, oclcNo):
        url = self.base_url + '{}'.format(oclcNo)
        headers = {
            'Accept': 'application/atom+json',
            'Authorization': 'Bearer {}'.format(self.access_token)}

        req = requests.Request('GET', url, headers=headers)
        prepped = req.prepare()
        print(prepped.url)
        print(prepped.headers)
        resp = self.send(prepped)
        print(resp.status_code)
        print(resp.content)


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


def evaluate_response(response):
    if response.status_code == requests.codes.ok:
        # code 200
        return response.content
    else:
        # log the error code & message
        print(response.json())  # temp
        return None
