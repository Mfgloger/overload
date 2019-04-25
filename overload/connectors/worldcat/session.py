import requests


import wskey
import user
from bibs.crosswalks import string2xml
from bibs.xml_bibs import NS


class InvalidObject(Exception):
    """Invalid argument passed"""

    def __init__(self, message):
        self.message = message


def get_wskey(key, secret, options=None):
    app_wskey = wskey.Wskey(
        key=key, secret=secret, options=options)
    return app_wskey


def get_user(authenticating_institution_id, principal_id, principal_idns):
    app_user = user.User(
        authenticating_institution_id=authenticating_institution_id,
        principal_id=principal_id,
        principal_idns=principal_idns)
    return app_user


def get_authorizaiton_header(
        app_wskey, request_url, app_user, auth_params=None):
    authorizaiton_header = app_wskey.get_hmac_signature(
        method='GET',
        request_url=request_url,
        options={
            'user': app_user,
            'auth_params': auth_params
        })
    return authorizaiton_header


def get_access_token(creds):
    """
    temp code - create own way to request token;
    for the moment use OCLC library
    """

    key = creds['key']
    secret = creds['secret']
    authenticating_institution_id = creds['authenticating_institution_id']
    context_institution_id = creds['context_institution_id']
    # services = creds['scopes']  # requires updating creds in vault

    # # Configure the wskey library object
    my_wskey = wskey.Wskey(
        key=key,
        secret=secret,
        options={'services': ['WorldCatMetadataAPI']})  # pull from creds instead?

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

    def __init__(self, creds=None):
        requests.Session.__init__(self)
        if not creds:
            raise AttributeError('Session requrires worlcat credentials')

        self.timeout = (5, 5)
        self.headers.update({
            'User-Agent': 'BookOps/Overload',

        })


class MetadataSession(WorldcatSession):
    """
    Interface for getting full records from Worldcat and
    setting library holdings
    args:
        creds: dict, Worldcat credentials
    """

    def __init__(self, creds=None):
        WorldcatSession.__init__(self, creds)

        self.base_url = 'https://worldcat.org/bib/data/'
        self.wskey = get_wskey(creds['key'], creds['secret'])
        self.user = get_user(
            creds['authenticating_institution_id'],
            creds['principal_id'],
            creds['principal_idns'])

    def prep_get_request(self, oclcNo):
        request_url = self.base_url + '{}'.format(oclcNo)
        authorization_header = get_authorizaiton_header(
            self.wskey, request_url, self.user)
        headers = {
            'Accept': 'application/atom+xml;content="application/vnd.oclc.marc21+xml"',
            'Authorization': authorization_header}

        req = requests.Request('GET', request_url, headers=headers)
        prepped_req = req.prepare()
        return prepped_req

    def get_record(self, oclcNo):
        prepped_request = self.prep_get_request(oclcNo)
        # print(prepped_request.url)
        # print(prepped_request.headers)
        # send request
        try:
            response = self.send(
                prepped_request, timeout=self.timeout)
            return response
        except requests.exceptions.Timeout:
            # log error
            raise
        except requests.exceptions.ConnectionError:
            # log
            raise

    def set_holdings(self):
        pass


class SearchSession(WorldcatSession):
    """ Interface for querying WorldCat using Search API.
        Search API uses Wskey Lite authorization method:
        https://www.oclc.org/developer/develop/authentication/wskey-lite.en.html
        args:
            wskey: str, Worldcat services key
    """

    def __init__(self, creds=None):
        WorldcatSession.__init__(self, creds)
        self.base_url = 'http://www.worldcat.org/webservices/catalog/'
        self.wskey = creds['key']
        self.headers.update({
            'Accept': 'application/xml'
        })
        self.payload = {
            'wskey': self.wskey
        }

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
        # send request
        try:
            response = self.get(
                url, params=self.payload, timeout=self.timeout)
            return response
        except requests.exceptions.Timeout:
            # log error
            raise
        except requests.exceptions.ConnectionError:
            # log
            raise

    def lookup_by_oclcNo(self, oclcNo):
        """
        Use to get a record with particular OCLC number
        args:
            oclcNo: str, OCLC number
        returns:
            response: class requests.models.Response, default
                      Worldcat format is marcxml
        """

        url = self.base_url + 'content/{}'.format(oclcNo)
        try:
            response = self.get(
                url, params=self.payload, timeout=self.timeout)
            return response
        except requests.exceptions.Timeout:
            raise
        except requests.exceptions.ConnectionError:
            raise


def is_positive_response(response):
    if response.status_code == requests.codes.ok:
        # code 200
        return True
    else:
        # log the error code & message
        print(response.content)  # temp
        return False


def no_match(response):
    response_body = string2xml(response.content)
    try:
        message = response_body[0][1].text
        if message == 'Record does not exist':
            return True
        else:
            return False
    except IndexError:
        return False


def extract_record_from_response(response):
    response_body = string2xml(response.content)
    record = response_body.find('.//atom:content/rb:response/marc:record', NS)
    return record
