# -*- coding: utf-8 -*-

import unittest
from datetime import datetime, timedelta
from mock import Mock, patch
import requests


from context import AuthorizeAccess


class TestAuthServer(unittest.TestCase):

    def test_server_is_online(self):
        response = requests.get('https://isso.nypl.org')
        self.assertTrue(response.ok)


class TestAuthorizeAccess(unittest.TestCase):

    def setUp(self):
        self.client_id = 'johndoe'
        self.client_secret = 'secret'
        self.oauth_server = 'https://isso.nypl.org'
        self.auth = AuthorizeAccess(
            self.client_id, self.client_secret, self.oauth_server)

    def test_auth_class_initialization(self):
        self.assertEquals(self.auth.client_id, 'johndoe')
        self.assertEqual(self.auth.client_secret, 'secret')
        self.assertEqual(self.auth.oauth_server, 'https://isso.nypl.org')

    def test_value_error_raises_on_attrib_none(self):
        with self.assertRaises(ValueError):
            AuthorizeAccess()

    @patch('overload.connectors.platform.requests.post')
    def test_get_token_header(self, mock_post):
        r = {'access_token': '123abcd',
             'token_type': 'Bearer',
             'expires_in': 3600,
             'id_token': '123abcd',
             'scope': 'offline_access openid api read:bib read:item'}

        mock_post.return_value = Mock(status_code=200)
        mock_post.return_value.json.return_value = r

        self.assertEqual(self.auth.get_token()['id'], '123abcd')



if __name__ == '__main__':
    unittest.main()