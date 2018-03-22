# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from mock import MagicMock, patch
import json
import requests
from requests.exceptions import ConnectionError, Timeout

from context import errors
from context import AuthorizeAccess, PlatformSession
from context import setup_dirs


class TestAuthorizeAccessLogic(unittest.TestCase):

    def setUp(self):
        self.client_id = 'johndoe'
        self.client_secret = 'secret'
        self.base_url = 'https://platform.org'
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
        self.assertEquals(self.auth.client_id, 'johndoe')
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

    @patch('overload.connectors.platform.requests.post')
    def test_get_token_token_error(self, mock_post):
        mock_post = MagicMock(
            spec=['status_code'],
            return_value=json.dumps({'error': 'error_type'}),
            status_code=401)
        with self.assertRaises(errors.APITokenError):
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

    def test_validate_token_exception(self):
        expires_on = datetime.now() - timedelta(
            seconds=1)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        with self.assertRaises(errors.APITokenExpiredError):
            PlatformSession(
                self.base_url, token)

    def test_open_session_method(self):
        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        sess = PlatformSession(
            self.base_url, token)
        self.assertIsInstance(sess.session, requests.Session)
        self.assertEqual(
            sess.session.headers,
            {'user-agent': 'overload/0.1.0',
             'Authorization': 'Bearer ' + token.get('id')})

    @patch('overload.connectors.platform.requests.session')
    def test_query_bibStandardNo(self, session_mock):
        expires_on = datetime.now() + timedelta(
            seconds=5)
        token = {'expires_on': expires_on, 'id': 'abc1234'}
        session_mock.return_value = MagicMock(get=MagicMock(return_value='bar'))
        sess = PlatformSession(
            self.base_url, token)
        keywords = ['12345']
        payload = {
            'nyplSource': 'sierra-nypl',
            'limit': 1,
            'standardNumber': '12345'}
        self.assertEqual(sess.query_bibStandardNo(keywords, limit=1), 'bar')
        mock_get.assert_called_with(
            self.base_url + '/bibs',
            payload, (5, 5))

if __name__ == '__main__':
    unittest.main()
