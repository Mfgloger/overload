# -*- coding: utf-8 -*-

# run after test_platform, so the logic is validated first
# requires dev platform authorization named "Platform DEV" in USER_DATA

import unittest
import shelve
import base64
import requests


from context import AuthorizeAccess, PlatformSession
from context import setup_dirs


class TestPlatformMethodsOnDev(unittest.TestCase):

    def setUp(self):

        response = requests.get('https://isso.nypl.org')
        self.assertTrue(response.ok)

        user_data = shelve.open(setup_dirs.USER_DATA)
        api_params = user_data['PlatformAPIs']['Platform DEV']
        self.client_id = base64.b64decode(api_params['client_id'])
        self.client_secret = base64.b64decode(api_params['client_secret'])
        self.oauth_server = 'https://isso.nypl.org'
        self.base_url = api_params['host']
        user_data.close()
        self.auth = AuthorizeAccess(
            self.client_id, self.client_secret, self.oauth_server)
        self.token = self.auth.get_token()
        self.sess = PlatformSession(self.base_url, self.token)

    def tearDown(self):
        self.sess.close()

    def test_query_bibStandardNo(self):
        res = self.sess.query_bibStandardNo(keywords=['9781302905620'])
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 1)

    def test_query_bibId(self):
        res = self.sess.query_bibId(keywords=['21310805'])
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 1)

    def test_query_bibCreatedDate(self):
        res = self.sess.query_bibCreatedDate(
            '2013-09-03T13:17:45Z', '2014-09-03T13:17:45Z',
            limit=1)
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 1)

    def test_bibUpdatedDate(self):
        res = self.sess.query_bibUpdatedDate(
            '2013-09-03T13:17:45Z', '2014-09-03T13:17:45Z',
            limit=1)
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 1)

    def test_get_bibItems(self):
        res = self.sess.get_bibItems('21310805')
        self.assertTrue(res.status_code in (200, 404))

    def query_itemId(self):
        res = self.sess.query_itemId(keywords=['35366967, 35366972'])
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 2)

    def query_itemBarcode(self):
        res = self.sess.query_itemBarcode(keyword='33333844889317')
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 1)

    def query_itemBibId(self):
        res = self.sess.queryBibId(keyword='21310805', limit=5)
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 5)

    def query_itemCreatedDate(self):
        res = self.sess.query_itemCreatedDate(
            '2013-09-03T13:17:45Z', '2014-09-03T13:17:45Z',
            limit=5)
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 5)

    def query_itemUpdatedDate(self):
        res = self.sess.query_itemUpdatedDate(
            '2013-09-03T13:17:45Z', '2014-09-03T13:17:45Z',
            limit=5)
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 5)

    def get_item(self):
        res = self.sess.get_item(keyword='35362061')
        self.assertTrue(res.status_code in (200, 404))
        self.assertLessEqual(res.json()['count'], 1)

if __name__ == '__main__':
    unittest.main()