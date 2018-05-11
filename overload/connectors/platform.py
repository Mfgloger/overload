import requests
from requests.exceptions import ConnectionError, Timeout
from datetime import datetime, timedelta

from errors import APITokenError, APITokenExpiredError


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
                    'One of required Platform authorization '
                    'settings parameter is missing')

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
                    id=req['access_token'],
                    expires_on=datetime.now() +
                    timedelta(seconds=req['expires_in'] - 1))
            else:
                raise APITokenError(
                    'Not able to obtain access token '
                    'from Platform auth server. Error: {}'.format(
                        req.json()['error']))
        except ConnectionError:
            raise ConnectionError(
                'not able to connect to Platform auth server, '
                'verify auth server url')
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform auth server')


class PlatformSession(requests.Session):
    """
    NYPL Platform wrapper
    args:
        base_url str
        token (dict token obj {id: token_id, expires_on: datetime}
    creates requests.Session object tailored to NYPL Platform
    """
    def __init__(self, base_url=None, token=None):
        requests.Session.__init__(self)
        self.base_url = base_url
        self.token = token
        self.timeout = (5, 5)

        if base_url is None or token is None:
            raise ValueError(
                'Required Platform setting parameter is missing')

        self.headers.update({
            'User-Agent': 'BookOps-Overload/0.1.0',
            'Authorization': 'Bearer ' + self.token.get('id')})

        self._validate_token()

    def _validate_token(self):
        if self.token.get('expires_on') < datetime.now():
            raise APITokenExpiredError(
                'Platform access token expired')

    def query_bibStandardNo(
            self, keywords=[], source='sierra-nypl', deleted=False, limit=20):
        """
        performs standar number query
        args:
            keywords list
            source str
            limit int
        return:
            results
        """
        self._validate_token()

        # prep request
        endpoint = self.base_url + '/bibs'
        payload = dict(
            nyplSource=source,
            limit=limit,
            deleted=deleted,
            standardNumber=','.join(keywords))
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_bibControlNo(
            self, keywords=[], source='sierra-nypl', deleted=False, limit=20):
        """
        performs control number query (field 001)
        args:
            keywords list
            source str
            limit int
        return:
            results
        """
        self._validate_token()

        # prep request
        endpoint = self.base_url + '/bibs'
        payload = dict(
            nyplSource=source,
            limit=limit,
            deleted=deleted,
            controlNumber=','.join(keywords))
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_bibId(
            self, keywords=[], source='sierra-nypl', deleted=False, limit=20):
        """
        performs bib ID query
        args:
            keywords list
            source str
            limit int
        return:
            response
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs'
        payload = dict(
            nyplSource=source,
            limit=limit,
            deleted=deleted,
            id=','.join(keywords))
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_bibCreatedDate(
            self, start_date, end_date,
            source='sierra-nypl', deleted=False, limit=10):
        """
        performs dateCreated query
        args:
            start_date str (format: 2013-09-03T13:17:45Z)
            end_date str (format: 2013-09-03T13:17:45Z)
            limit int (default 10)
        return:
            results
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs'
        payload = dict(
            createdDate='[{},{}]'.format(start_date, end_date),
            nyplSource=source,
            deleted=False,
            limit=limit)
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_bibUpdatedDate(
            self, start_date, end_date,
            deleted=False, source='sierra-nypl', limit=10):
        """
        performs updatedCreated query
        args:
            start_date str (format: 2013-09-03T13:17:45Z)
            end_date str (format: 2013-09-03T13:17:45Z)
            limit int (default 10)
        return:
            results
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs'
        payload = dict(
            updatedDate='[{},{}]'.format(start_date, end_date),
            nyplSource=source,
            deleted=False,
            limit=limit)
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def get_bibItems(self, keyword, source='sierra-nypl'):
        """
        requests item data for particular bib id
        args:
            keyword str ( bib id)
            source str
        return:
            response
        """
        self._validate_token()
        endpoint = self.base_url + '/bibs/{}/{}/items'.format(
            source, keyword)
        try:
            response = self.get(
                endpoint, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_itemId(
            self, keywords=[],
            source='sierra-nypl', deleted=False, limit=10):
        """
        requests item data for particular item id
        args:
            keyword list (list of item ids)
            source str
            limit int
        return:
            response
        """
        self._validate_token()
        endpoint = self.base_url + '/items'
        payload = dict(
            nyplSource=source,
            deleted=deleted,
            limit=limit,
            id=','.join(keywords))
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_itemBarcode(
            self, keyword, source='sierra-nypl',
            deleted=False, limit=10):
        """
        requests item data for particular barcode
        args:
            keywords list (list of barcodes)
            source str
            limit int
        return:
            response
        """
        self._validate_token()
        endpoint = self.base_url + '/items'
        payload = dict(
            nyplSource=source,
            deleted=deleted,
            limit=limit,
            barcode=keyword)
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_itemBibId(
            self, keyword, source='sierra-nypl',
            deleted=False, limit=10):
        """
        requests item data for particular bib id
        args:
            keyword str (bib id)
            source str
            limit int
        return:
            response
        """
        self._validate_token()
        endpoint = self.base_url + '/items'
        payload = dict(
            nyplSource=source,
            deleted=deleted,
            limit=limit,
            bibId=keyword)
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_itemCreatedDate(
            self, start_date, end_date, source='sierra-nypl',
            deleted=False, limit=10):
        """
        requests items created between two dates
        args:
            start_date str (format: 2013-09-03T13:17:45Z)
            end_date str (format: 2013-09-03T13:17:45Z)
            limit int (default 10)
            source str
        return:
            results
        """
        self._validate_token()
        endpoint = self.base_url + '/items'
        payload = dict(
            createdDate='[{},{}]'.format(start_date, end_date),
            nyplSource=source,
            deleted=deleted,
            limit=limit)
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def query_itemUpdateddDate(
            self, start_date, end_date, source='sierra-nypl',
            deleted=False, limit=10):
        """
        requests items updated between two dates
        args:
            start_date str (format: 2013-09-03T13:17:45Z)
            end_date str (format: 2013-09-03T13:17:45Z)
            limit int (default 10)
            source str
        return:
            results
        """
        self._validate_token()
        endpoint = self.base_url + '/items'
        payload = dict(
            updatedDate='[{},{}]'.format(start_date, end_date),
            nyplSource=source,
            deleted=deleted,
            limit=limit)
        try:
            response = self.get(
                endpoint, params=payload, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')

    def get_item(self, keyword, source='sierra-nypl'):
        """
        requests item data for particular bib id
        args:
            keyword str (id)
            sources str
        return:
            response
        """
        self._validate_token()
        endpoint = self.base_url + '/items/{}/{}'.format(
            source, keyword)
        try:
            response = self.get(
                endpoint, timeout=self.timeout)
            return response
        except Timeout:
            raise Timeout(
                'request timed out while trying to connect '
                'to Platform endpoint ({})'.format(endpoint))
        except ConnectionError:
            raise ConnectionError(
                'unable to connect to Platform')
