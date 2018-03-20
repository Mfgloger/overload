# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from mock import Mock, patch

from context import errors
from context import AuthorizeAccess, PlatformSession
from context import setup_dirs


class TestAuthorizeAccessMock(unittest.TestCase):

    def setUp(self):
        self.client_id = 'johndoe'
        self.client_secret = 'secret'
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

        mock_post.return_value = Mock(status_code=200)
        mock_post.return_value.json.return_value = self.r
        token = self.auth.get_token()

        self.assertIn('id', token)
        self.assertIn('expires_on', token)
        self.assertEqual(token.get('id'), '123abcd')
        expires_on = datetime.now() + timedelta(seconds=3600 - 1)
        self.assertEqual(token.get('expires_on'), expires_on)

    @patch('overload.connectors.platform.requests.post')
    def test_get_token_exceptions(self, mock_post):
        e = {'error': 'error_type'}
        mock_post.return_value = Mock(status_code=401)
        mock_post.return_value.json.return_value = e
        with self.assertRaises(errors.APITokenError):
            self.auth.get_token()





if __name__ == '__main__':
    unittest.main()
