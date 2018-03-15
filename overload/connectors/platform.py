import requests
from requests.exceptions import ConnectionError, ConnectTimeout, ReadTimeout
from datetime import datetime, timedelta

from errors import APITokenError, APITokenExpiredError, \
    APITimeoutError


class AuthorizeAccess:
    """
    authorizes requests to NYPL Platform
    args:
        client_id, client_secret, oauth_server
    return:
        token {id: id, expires_on: timestamp}
    """
    def __init__(self, client_id=None, client_secret=None,
                 oauth_server=None):

        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_server = oauth_server
        self.timeout = (5, 5)

        for value in self.__dict__.values():
            if value is None:
                raise ValueError(
                    'Required Platform settings parameter is missing')

    def get_token(self):
        """
        fetches access token
        return:
            token dict
        """
        token_url = '/'.join([self.oauth_server, 'oauth/token'])
        headers = {'user-agent': 'overload/0.0.2'}
        auth = (self.client_id, self.client_secret)
        data = {'grant_type': 'client_credentials'}
        try:
            req = requests.post(
                token_url, auth=auth, headers=headers,
                data=data, timeout=self.timeout)
            if req.status_code == requests.codes.ok:
                req = req.json()
                return dict(
                    id=req['id_token'],
                    expires_on=datetime.now() +
                    timedelta(seconds=req['expires_in'] - 1))
            else:
                raise APITokenError(
                    'Not able to obtain access token '
                    'from Platform auth server')
        except ConnectionError:
            raise ConnectionError(
                'not able to connect to Platform auth server')
        except ConnectTimeout:
            raise ConnectTimeout(
                'request timed out while trying to connect '
                'to Platform auth server')
        except ReadTimeout:
            raise ReadTimeout(
                'Platform auth server did not send any data'
                'in the allotted amount of time')


class PlatformSession:
    """
    NYPL Platform wrapper
    """
    def __init__(self, base_url=None, token=None):
        self.base_url = base_url
        self.token = token
        self.timeout = (5, 5)

        if base_url is None or token is None:
            raise ValueError(
                'Required Platform setting parameter is missing')

        self._validate_token()
        self._open_session()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.session.close()

    def _validate_token(self):
        if self.token.get('expires_on') < datetime.now():
            raise APITokenExpiredError(
                'Platform access token expired')

    def _open_session(self):
        print 'attempting to open session'
        self.session = requests.Session()
        self.session.headers = {
            'user-agent': 'overload/0.1.0',
            'Authorization': 'Bearer ' + self.token.get('id')}

    def query_standardNo(self, keywords=[], source='sierra-nypl', limit=20):
        """
        performs standar number query
        args:
            keywords list
            source str
            limit int
        return:
            results in json format
        """
        self._validate_token()

        # prep request
        endpoint = self.base_url + '/bibs'
        payload = dict(
            nyplSource=source,
            limit=limit,
            standardNumber=','.join(keywords))
        try:
            response = self.session.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except ConnectTimeout:
            raise ConnectTimeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ReadTimeout:
            raise ReadTimeout(
                'Platform endpoint ({}) did not send any data'
                'in the allotted amount of time'.format(
                    endpoint))

    def query_bibId(self, keywords=[], source='sierra-nypl', limit=20):
        """
        performs bib ID query
        args:
            keywords list
            source str
            limit int
        return:
            response in json format
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs'
        payload = dict(
            nyplSource=source,
            limit=limit,
            id=','.join(keywords))
        try:
            response = self.session.get(
                endpoint, params=payload, timeout=self.timeout)
            return response.json()
        except ConnectTimeout:
            raise ConnectTimeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ReadTimeout:
            raise ReadTimeout(
                'Platform endpoint ({}) did not send any data'
                'in the allotted amount of time'.format(
                    endpoint))

    def query_createdDate(
            self, start_date, end_date, limit, source='sierra-nypl'):
        """
        performs dateCreated query
        args:
            start_date str (format: 2013-09-03T13:17:45Z)
            end_date str (format: 2013-09-03T13:17:45Z)
            limit int
        return:
            results in json format
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs'
        payload = dict(
            createdDate='[{},{}]'.format(start_date, end_date),
            nyplSource=source,
            limit=limit)
        try:
            response = self.session.get(
                endpoint, params=payload, timeout=self.timeout)
            return response.json()
        except ConnectTimeout:
            raise ConnectTimeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ReadTimeout:
            raise ReadTimeout(
                'Platform endpoint ({}) did not send any data'
                'in the allotted amount of time'.format(
                    endpoint))

    def query_updatedDate(
            self, start_date, end_date, limit, source='sierra-nypl'):
        """
        performs updatedCreated query
        args:
            start_date str (format: 2013-09-03T13:17:45Z)
            end_date str (format: 2013-09-03T13:17:45Z)
            limit int
        return:
            results in json format
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs'
        payload = dict(
            updatedDate='[{},{}]'.format(start_date, end_date),
            nyplSource=source,
            limit=limit)
        try:
            response = self.session.get(
                endpoint, params=payload, timeout=self.timeout)
            return response.json()
        except ConnectTimeout:
            raise ConnectTimeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ReadTimeout:
            raise ReadTimeout(
                'Platform endpoint ({}) did not send any data'
                'in the allotted amount of time'.format(
                    endpoint))

    def get_bibItems(self, keyword, source='sierra-nypl'):
        """
        requests item data for particular id
        args:
            keyword str (id)
            sources str
        return:
            response in json format
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs/{}/{}/items'.format(
            source, keyword)
        try:
            response = self.session.get(
                endpoint, timeout=self.timeout)
            return response.json()
        except ConnectTimeout:
            raise ConnectTimeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ReadTimeout:
            raise ReadTimeout(
                'Platform endpoint ({}) did not send any data'
                'in the allotted amount of time'.format(
                    endpoint))

    def close(self):
        self.session.close()
