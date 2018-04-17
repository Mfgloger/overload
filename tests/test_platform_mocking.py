# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from mock import patch
import requests_mock

import json
import requests
from requests.exceptions import ConnectionError, Timeout

from context import APITokenError, APITokenExpiredError
from context import AuthorizeAccess, PlatformSession


class TestAuthorizeAccessLogic(unittest.TestCase):

    def setUp(self):
        self.client_id = 'myid'
        self.client_secret = 'secret'
        self.base_url = 'https://our_platform.org/api/v0.1'
        self.oauth_server = 'https://isso.nypl.org'
        self.auth = AuthorizeAccess(
            self.client_id, self.client_secret, self.oauth_server)
        self.r = {
            'access_token': '123abcd',
            'token_type': 'Bearer',
            'expires_in': 3600,
            'id_token': '123abcd',
            'scope': 'offline_access openid api read:bib read:item'}

    def test_auth_class_initialization(self):
        self.assertEquals(self.auth.client_id, 'myid')
        self.assertEqual(self.auth.client_secret, 'secret')
        self.assertEqual(self.auth.oauth_server, 'https://isso.nypl.org')

    def test_value_error_raises_on_attrib_none(self):
        with self.assertRaises(ValueError):
            AuthorizeAccess()

    @patch('overload.connectors.platform.requests.post')
    def test_get_token_header(self, mock_post):

        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = self.r

        token = self.auth.get_token()

        self.assertIn('id', token)
        self.assertIn('expires_on', token)
        self.assertEqual(token.get('id'), '123abcd')
        expires_on = datetime.now() + timedelta(
            seconds=self.r['expires_in'] - 1)
        self.assertEqual(token.get('expires_on'), expires_on)

    # can't get it work for some reason, investigate
    @requests_mock.Mocker()
    def test_get_token_token_error(self, m):
        m.post(
            'https://isso.nypl.org/oauth/token', status_code=599,
            json=json.dumps({'error': 'error_type'}))
        with self.assertRaises(APITokenError):
            self.auth.get_token()

    @patch('overload.connectors.platform.requests.post')
    def test_get_token_connection_error(self, mock_post):
        mock_post.side_effect = ConnectionError
        with self.assertRaises(ConnectionError):
            self.auth.get_token()

    @patch('overload.connectors.platform.requests.post')
    def test_get_token_connection_timeout(self, mock_post):
        mock_post.side_effect = Timeout
        with self.assertRaises(Timeout):
            self.auth.get_token()

    def test_platform_session_invalid_attrib(self):
        with self.assertRaises(ValueError):
            PlatformSession()

    # can't make it work for some reason, investigate
    def test_validate_token_exception(self):
        expires_on = datetime.now() - timedelta(
            seconds=1)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        with self.assertRaises(APITokenExpiredError):
            PlatformSession(
                self.base_url, token)

    def test_open_session_method(self):
        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(
            self.base_url, token)
        sess.headers.update({'User-Agent': 'Overload/TESTS'})
        self.assertIsInstance(sess, requests.Session)
        self.assertEqual(
            sess.headers,
            {'Authorization': 'Bearer abc1234',
             'Connection': 'keep-alive',
             'Accept-Encoding': 'gzip, deflate',
             'Accept': '*/*',
             'User-Agent': 'Overload/TESTS',
             'Authorization': 'Bearer ' + token.get('id')})

    def test_methods_in_platform_session(self):
        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(self.base_url, token)
        self.assertEquals(
            dir(sess),
            ['__attrs__', '__class__', '__delattr__', '__dict__', '__doc__', '__enter__', '__exit__', '__format__', '__getattribute__', '__getstate__', '__hash__', '__init__', '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__', '__setstate__', '__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_validate_token', 'adapters', 'auth', 'base_url', 'cert', 'close', 'cookies', 'delete', 'get', 'get_adapter', 'get_bibItems', 'get_item', 'get_redirect_target', 'head', 'headers', 'hooks', 'max_redirects', 'merge_environment_settings', 'mount', 'options', 'params', 'patch', 'post', 'prepare_request', 'proxies', 'put', 'query_bibControlNo', 'query_bibCreatedDate', 'query_bibId', 'query_bibStandardNo', 'query_bibUpdatedDate', 'query_itemBarcode', 'query_itemBibId', 'query_itemCreatedDate', 'query_itemId', 'query_itemUpdateddDate', 'rebuild_auth', 'rebuild_method', 'rebuild_proxies', 'request', 'resolve_redirects', 'send', 'stream', 'timeout', 'token', 'trust_env', 'verify'])

    @patch('overload.connectors.platform.PlatformSession.query_bibStandardNo')
    def test_query_bibStandardNo(self, mock_query):
        # way to verify correct methods are hijacked
        assert mock_query is PlatformSession.query_bibStandardNo

        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(
            self.base_url, token)
        keywords = ['12345']
        limit = 1

        mock_query.return_value = 'bar'
        res = sess.query_bibStandardNo(keywords, limit=limit)
        self.assertEqual(res, 'bar')
        mock_query.assert_called_with(['12345'], limit=limit)

        # test exceptions are raised
        mock_query.side_effect = [Timeout, ConnectionError]
        with self.assertRaises(Timeout):
            sess.query_bibStandardNo(keywords)
            sess.query_bibStandardNo(keywords)

    @patch('overload.connectors.platform.PlatformSession.query_bibId')
    def test_query_bibId(self, mock_query):
        # way to verify correct methods are hijacked
        assert mock_query is PlatformSession.query_bibId

        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(
            self.base_url, token)
        keywords = ['12345']
        limit = 1

        mock_query.return_value = 'bar'
        res = sess.query_bibId(keywords, limit=limit)
        self.assertEqual(res, 'bar')
        mock_query.assert_called_with(['12345'], limit=limit)

        # test exceptions are raised
        mock_query.side_effect = [Timeout, ConnectionError]
        with self.assertRaises(Timeout):
            sess.query_bibId(keywords)
            sess.query_bibId(keywords)

    @patch('overload.connectors.platform.PlatformSession.query_bibCreatedDate')
    def test_query_bibId(self, mock_query):
        # way to verify correct methods are hijacked
        assert mock_query is PlatformSession.query_bibCreatedDate

        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(
            self.base_url, token)
        keywords = ['12345']
        limit = 1

        mock_query.return_value = 'bar'
        res = sess.query_bibCreatedDate(keywords, limit=limit)
        self.assertEqual(res, 'bar')
        mock_query.assert_called_with(['12345'], limit=limit)

        # test exceptions are raised
        mock_query.side_effect = [Timeout, ConnectionError]
        with self.assertRaises(Timeout):
            sess.query_bibCreatedDate(keywords)
            sess.query_bibCreatedDate(keywords)

    @patch('overload.connectors.platform.PlatformSession.query_bibUpdatedDate')
    def test_query_bibId(self, mock_query):
        # way to verify correct methods are hijacked
        assert mock_query is PlatformSession.query_bibUpdatedDate

        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(
            self.base_url, token)
        keywords = ['12345']
        limit = 1

        mock_query.return_value = 'bar'
        res = sess.query_bibUpdatedDate(keywords, limit=limit)
        self.assertEqual(res, 'bar')
        mock_query.assert_called_with(['12345'], limit=limit)

        # test exceptions are raised
        mock_query.side_effect = [Timeout, ConnectionError]
        with self.assertRaises(Timeout):
            sess.query_bibUpdatedDate(keywords)
            sess.query_bibUpdatedDate(keywords)


if __name__ == '__main__':
    unittest.main()
