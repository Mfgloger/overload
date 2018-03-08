import requests
import logging
import json
import datetime

from errors import APISettingsError


class AuthorizeAccess:
    """
    authorizes requests to NYPL Platform
    returns: token
    """
    def __init__(self, client_id=None, client_secret=None,
                 oauth_server=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_server = oauth_server

        for value in self.__dict__.values():
            if value is None:
                raise APISettingsError(
                    'Platform API settings are missing required parameters')

    def get_token(self):

        token_url = '/'.join([self.oauth_server, 'oauth/token'])
        headers = {'user-agent': 'overload/0.0.2'}
        auth = (self.client_id, self.client_secret)
        data = {'grant_type': 'client_credentials'}
        req = requests.post(
            token_url, auth=auth, headers=headers, data=data)
        if req.status_code == requests.codes.ok:

        else:
            # log and raise

class PlatformSession():
    """
    NYPL Platform wrapper
    """
    def __init__(self, authorization_url=None, token_url=None, base_url=None,
            client_id=None, client_secret=None):

        # set up logger
        self.module_logger_main = logging.getLogger('tests')
        self.module_logger_request = logging.getLogger('api_request')
        self.module_logger_response = logging.getLogger('api_response')

        self.authorization_url = authorization_url
        self.token_url = token_url
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.timeout = (5, 5)

    def get_token(self):
        """authorizes and obtains platform token"""
        s = Session()
        
        # r = requests.post(self.token_url, data={self.client_id: self.client_secret},
        #     headers=headers)
        req = Request('POST', self.token_url, auth=auth, headers=headers, data=data)
        prepped = req.prepare()
        # print prepped.__dict__.keys()
        print 'body: ', prepped.body
        print 'url: ', prepped.url
        print 'headers: ', prepped.headers
        print 'method: ', prepped.method
        res = s.send(prepped)
        return res


    def open_session(self):
        self.session = Session()
        # self.session.headers = {'user-agent': 'overload/0.0.2'}
        self.session.headers = {'grant_type': 'client_credentials'}
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        token_req = oauth.fetch_token(
            token_url=self.token_url, auth=auth, timeout=self.timeout)
        return token_req
