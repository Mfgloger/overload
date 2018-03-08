import requests
from oauthlib.oauth2 import BackendApplicationClient, MissingTokenError
from requests.auth import HTTPBasicAuth
from requests_oauthlib import OAuth2Session
from datetime import datetime, timedelta
from time import sleep
import logging
import json

from errors import APISettingsError, APICriticalError, \
    ExceededLimitsError, APITimeoutError, UnhandledException, APITokenError


class SierraSession():
    """
    A Sierra API wrapper
    In addition to making Sierra API calls it interprets received results 
    and runs subsequent queries if needed

    :client_id param: Sierra client id
    :client_secret param: Sierra client secret
    :base_url param: library Sierra API url: https://example-library.edu/iii/sierra-api/v4
    """

    def __init__(self, client_id=None, client_secret=None, base_url=None):
        """
        initiate connection variables and verify needed parameters are present;
        open Session connection
        """
        self.module_main_logger = logging.getLogger('tests')
        self.module_request_logger = logging.getLogger('api_request')
        self.module_response_logger = logging.getLogger('api_response')

        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url
        self.timeout = (5, 5)
        self.token = None
        self.wait_time = 0
        self.wait_time_step = 10
        self.wait_time_limit = 120  # in seconds
        self.stop_all_codes = range(109, 145)  # Sierra API codes

        if self.client_id is None:
            self.module_main_logger.critical('settings: API client id missing')
            raise APISettingsError('API client id missing')

        if self.client_secret is None:
            self.module_main_logger.critical('settings: API client secret missing')
            raise APISettingsError('API client secret missing')

        if self.base_url is None:
            self.module_main_logger.critical('settings: base API URL missing')
            raise APISettingsError('base API URL missing')

        # open connection to Sierra API
        self.module_main_logger.info('opening Siera API connection')
        self.open_connection(self.get_token())

    def open_connection(self, token):
        """
        opens requests module Session object and persist
        headers with authorization token for all subsequent Sierra API requests
        raises MissingTokenError if token not obtained
        """

        if token is not None:
            self.session = requests.Session()
            self.session.headers = {'Authorization': 'Bearer ' + self.token}
        else:
            self.module_main_logger.error('access token NOT obtained')

    def get_token(self):
        """
        obtains Sierra token authorizing subsequent queries
        returns: token string or None if failed to obtain it
        """

        self.token_url = self.base_url + '/token'
        auth = HTTPBasicAuth(self.client_id, self.client_secret)
        client = BackendApplicationClient(client_id=self.client_id)
        oauth = OAuth2Session(client=client)
        try:
            token_req = oauth.fetch_token(
                token_url=self.token_url, auth=auth, timeout=self.timeout)
            self.token = token_req['access_token']
            self.token_expiration_time = datetime.utcfromtimestamp(
                token_req['expires_at'])
            self.module_main_logger.info('new token obtained')

        except requests.exceptions.Timeout:
            self.module_main_logger.critical(
                'TimeoutError on: %s', self.token_url)
            raise APITimeoutError('API server not responsive')
        except MissingTokenError:
            self.module_main_logger.critical(
                'MissingTokenError on: %s', self.token_url)
            raise APITokenError('Not able to obtain API access token')
        except Exception as e:
            # capture unnamed exception
            self.module_main_logger.exception(
                'unnamed exception on get_token', exc_info=True)
            raise UnhandledException(
                'Unhandled exception encountered. Aborting.')
        else:
            return self.token

    def validate_token(self):
        """
        checks if token is expired, obtains new one and opens
        new Session if required
        """

        # here enter code to slow down requests if needed

        # reuse tokens unless they expired
        call_time = datetime.utcnow() + timedelta(seconds=60)
        if call_time > self.token_expiration_time:
            self.module_main_logger.info('token expired')
            # request new token and open new Session
            self.open_connection(self.get_token())
        else:
            self.module_main_logger.debug('token valid')

    def get_bib_by_id(self, bib_id):
        """
        query type: GET /v4/bibs/{id}
        retuns: response as json or None
        """

        self.validate_token()

        # prepare request
        endpoint = self.base_url + '/bibs/{}'.format(bib_id)
        payload = dict(fields='default,varFields')

        req = requests.Request('get', endpoint, params=payload)
        prepped = self.session.prepare_request(req)

        # sending request to Sierr API
        self.module_request_logger.debug(
            'get_bib_by_id request',
            extra={'req_url': prepped.url,
                   'req_body': prepped.body,
                   'req_head': prepped.headers})
        try:
            response = self.session.send(
                prepped,
                timeout=self.timeout)
        except requests.exceptions.Timeout:
            self.session.close()
            self.module_request_logger.critical(
                'TimeoutError on get_bib_by_id',
                extra={
                    'req_url': prepped.url,
                    'req_body': prepped.body,
                    'req_head': prepped.headers})
            raise APITimeoutError('server not responsive')
        except Exception as e:
            # capture unnamed exception
            self.session.close()
            self.module_request_logger.critical(
                'unnamed exception caught on get_bib_by_id',
                extra={
                    'req_url': prepped.url,
                    'req_body': prepped.body,
                    'req_head': prepped.headers}, exc_info=True)
            raise UnhandledException(
                'Unhandled exception encountered. Aborting.')
        if response.status_code == requests.codes.ok:
            # verify the correct type of resource is retrieved
            if 'materialType' in response.json():
                self.module_response_logger.debug(
                    'resource received',
                    extra={
                        'req_url': prepped.url,
                        'req_body': prepped.body,
                        'req_head': prepped.headers,
                        'response': response.json()
                    })
                return response.json()
            else:
                self.module_response_logger.warning(
                    'resource suspicious',
                    extra={
                        'req_url': prepped.url,
                        'req_body': prepped.body,
                        'req_head': prepped.headers,
                        'response': response.json()
                    })
                return None
        else:
            retry = self.eval_error(response, prepped)
            if retry:
                self.get_biby_by_id(bib_id)
            else:
                return None

    def get_bib_by_order_id(self, order_id):
        """
        request type: POST /v4/bibs/query
        posts order id query then requests the actual bib resource
        returns response in json or None
        """

        self.validate_token()

        # prepare request
        endpoint = self.base_url + '/bibs/query'
        order_id = 'o' + order_id
        json_query = {u'expr': {
                      u'operands': [order_id, u''], u'op': u'equals'},
                      u'target': {u'record': {u'type': u'order'}, u'id': 81}}
        json_query = json.dumps(json_query)
        payload = dict(
            offset=0,
            limit=1)
        req = requests.Request(
            'post', endpoint, params=payload, data=json_query)
        prepped = self.session.prepare_request(req)
        prepped.headers['Accept'] = 'application/json'

        # send request to Sierra API
        self.module_request_logger.debug(
            'get_bib_by_order_id request',
            extra={
                'req_url': prepped.url,
                'req_body': json.loads(prepped.body),
                'req_head': prepped.headers})
        try:
            response = self.session.send(
                prepped,
                timeout=20)
        except requests.exceptions.Timeout:
            self.session.close()
            self.module_request_logger.critical(
                'TimeoutError on get_bib_by_order_id',
                extra={
                    'req_url': prepped.url,
                    'req_body': json.loads(prepped.body),
                    'req_head': prepped.headers
                })
            raise APITimeoutError('server not responsive')
        except Exception as e:
            # capture unnamed exception
            self.session.close()
            self.module_request_logger.critical(
                'unnamed exception caught on get_bib_by_id',
                extra={
                    'req_url': prepped.url,
                    'req_body': json.loads(prepped.body),
                    'req_head': prepped.headers}, exc_info=True)
            raise UnhandledException(
                'Unhandled exception encountered. Aborting.')

        # interpret the response and decide what next
        if response.status_code == requests.codes.ok:
            if 'entries' in response.json():
                if response.json()['total'] == 0:
                    # JSON query endpoint does not return API error when
                    # no resouces are found, instead response includes
                    # empty data
                    self.module_response_logger.warning(
                        'resource NOT obtained but was expected',
                        extra={
                            'req_url': prepped.url,
                            'req_body': json.loads(prepped.body),
                            'req_head': prepped.headers,
                            'response': response.json()
                        })
                    return None
                else:
                    id = response.json()['entries'][0]['link'].split('/')[-1]
                    self.module_response_logger.debug(
                        'resource received',
                        extra={
                            'req_url': prepped.url,
                            'req_body': json.loads(prepped.body),
                            'req_head': prepped.headers,
                            'response': response.json()
                        })
                    # retrieve bib resource from retrieved link
                    bib_response = self.get_bib_by_id(id)
                    return bib_response
            else:
                self.module_response_logger.warning(
                    'resource suspicious',
                    extra={
                        'req_url': prepped.url,
                        'req_body': json.loads(prepped.body),
                        'req_head': prepped.headers,
                        'response': response.json()
                    })
                return None
        else:
            retry = self.eval_error(response, prepped.url)
            if retry:
                self.get_bib_from_order(order_id)
            else:
                return None

    def get_marc(self, bib_id):
        """
        request type: GET /v4/bibs/{id}/marc
        returns response in JSON or None
        """

        self.validate_token()

        # prepare request
        endpoint = self.base_url + \
            '/bibs/{}/marc'.format(bib_id)

        req = requests.Request('get', endpoint)
        prepped = self.session.prepare_request(req)
        prepped.headers['Accept'] = 'application/marc-in-json'

        # send request
        self.module_request_logger.debug(
            'get_marc request',
            extra={
                'req_url': prepped.url,
                'req_head': prepped.headers,
                'req_body': prepped.body})
        try:
            response = self.session.send(
                prepped,
                timeout=self.timeout)
        except requests.exceptions.Timeout:
            self.session.close()
            self.module_request_logger.critical(
                'TimeoutError on get_marc',
                extra={
                    'req_url': prepped.url,
                    'req_head': prepped.headers,
                    'req_body': prepped.body})
            raise APITimeoutError('server not responsive')
        except Exception as e:
            self.session.close()
            # capture unnamed exception
            self.module_request_logger.critical(
                'unnamed exception caught on get_bib_by_id',
                extra={
                    'req_url': prepped.url,
                    'req_head': prepped.headers,
                    'req_body': prepped.body},
                exc_info=True)
            raise UnhandledException(
                'Unhandled exception encountered. Aborting.')
        if response.status_code == requests.codes.ok:
            if 'leader' in response.json():
                self.module_response_logger.debug(
                    'resource received',
                    extra={
                        'req_url': prepped.url,
                        'req_head': prepped.headers,
                        'req_body': prepped.body,
                        'response': response.json()})
                return response.text
            else:
                self.module_response_logger.warning(
                    'resource suspicious',
                    extra={
                        'req_url': prepped.url,
                        'req_body': prepped.body,
                        'req_head': prepped.headers,
                        'response': response.json()})
                return None
        else:
            if self.retry(response, prepped.url):
                self.get_marc(bib_id)
            else:
                return None

    def get_bib_by_isbn(self, isbn):
        """
        request type: get /v4/bibs/search
        isbn param: 10 or 13 digit as str type
        returns response in json or None
        """

        self.validate_token()

        # prepare request
        endpoint = self.base_url + '/bibs/search'
        payload = dict(
            limit=10,
            index='isbn',
            text=isbn,
            fields='default,varFields')
        req = requests.Request('get', endpoint, params=payload)
        prepped = self.session.prepare_request(req)

        # send request
        self.module_request_logger.debug(
            'get_bib_by_isbn request',
            extra={
                'req_url': prepped.url,
                'req_head': prepped.headers,
                'req_body': prepped.body})
        try:
            response = self.session.send(
                prepped,
                timeout=self.timeout)
        except requests.exceptions.Timeout:
            self.session.close()
            self.module_request_logger.critical(
                'Timeouterror on get_bib_by_isbn',
                extra={
                    'req_url': prepped.url,
                    'req_head': prepped.headers,
                    'req_body': prepped.body})
            raise APITimeoutError('server not responsive')
        except Exception as e:
            self.session.close()
            # capture unnamed exception
            self.module_request_logger.critical(
                'unnamed exception caught on get_bib_by_isbn',
                extra={
                    'req_url': prepped.url,
                    'req_heaa': prepped.headers,
                    'req_body': prepped.body},
                exc_info=True)
            raise UnhandledException(
                'Unhandled exception encountered. Aborting.')

        # analyze response
        if response.status_code == requests.codes.ok:
            if 'total' in response.json():
                if response.json()['total'] == 0:
                    # response includes empty data
                    self.module_response_logger.debug(
                        'resource received: zero',
                        extra={
                            'req_url': prepped.url,
                            'req_head': prepped.headers,
                            'req_body': prepped.body,
                            'response': response.json()})
                    return None
                elif response.json()['total'] == 1:
                    self.module_response_logger.debug(
                        'resource received: one',
                        extra={
                            'req_url': prepped.url,
                            'req_head': prepped.headers,
                            'req_body': prepped.body,
                            'response': response.json()})
                    return response.json()
                else:
                    self.module_response_logger.debug(
                        'resource received: multi',
                        extra={
                            'req_url': prepped.url,
                            'req_head': prepped.headers,
                            'req_body': prepped.body,
                            'response': response.json()})
                    return response.json()
            else:
                self.module_response_logger.warning(
                    'resource suspicious',
                    extra={
                        'req_url': prepped.url,
                        'req_head': prepped.headers,
                        'req_body': prepped.body,
                        'response': response.json()})
                return None
        else:
            # is it OK to do?
            if self.retry(response):
                self.search_isbn_index(isbn)
            else:
                return None

    def eval_error(self, response, prepped_req):

        """
        evaluates response error messages
        returns: boolean to retry request or move on to next one
        raises critical errors that stop all requests
        """

        response = response.json()
        self.module_response_logger.warning(
            'resource NOT obtained',
            extra={
                'req_url': prepped_req.url,
                'req_body': prepped_req.body,
                'req_head': prepped_req.headers,
                'response': response
            })
        if response['code'] == '138':
            if self.wait_time < self.wait_time_limit:
                # exceeded API rate
                sleep(self.wait_time_step)
                self.wait_time += self.wait_time_step
                self.module_main_logger.info(
                    'waited %s sec. and retrying',
                    self.wait_time_step)
                return True
            else:
                self.session.close()
                self.module_main_logger.critical(
                    'ExceededLimitsError: waited %s seconds',
                    self.wait_time_limit)
                raise ExceededLimitsError(
                    'API error: exceeded endpoint response '
                    'wait limits of {}'.format(self.wait_time_limit))
        else:
            if response['code'] in self.stop_all_codes:
                self.session.close()
                self.module_main_logger.critical(
                    'StopAllError: API code: %s - stopping all requests',
                    response['code'])
                raise APICriticalError(
                    'API error: stopping requests: critical err code '
                    '{} - {}'.format(
                        response['code'], response['description']))
            else:
                self.module_main_logger.info(
                    'no panic, continuing subsequent requests')
                return False
