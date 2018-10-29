# -*- coding: utf-8 -*-

import keyring
import os
import shelve
import unittest


from context import credentials
from setup_dirs import USER_DATA, GOO_CREDS, GOO_FOLDERS


class TestCredentials(unittest.TestCase):

    def setUp(self):
        self.creds = 'creds.json'
        self.key = 'some_key-0123456'
        self.encrypt_creds = 'creds.bin'
        self.app = 'myapp-test'
        self.user = 'test_user1'
        self.passw = 'test-pass'
        self.user_data = 'test_user_data'
        self.goo_folders = 'tests\\goo_folders.json'

    def tearDown(self):
        try:
            os.remove(self.encrypt_creds)
        except WindowsError:
            pass

        try:
            if os.path.exists(self.user_data):
                shelve.open(self.user_data).clear()
                os.remove(self.user_data)
        except WindowsError:
            pass
        try:
            keyring.delete_password(self.app, self.user)
        except keyring.errors.PasswordDeleteError:
            pass

    def test_locate_goo_credentials(self):
        loc = credentials.locate_goo_credentials(USER_DATA, GOO_CREDS)
        self.assertTrue(
            os.path.exists(loc))

    def test_encrypt_file_data_produces_file(self):
        credentials.encrypt_file_data(
            self.key, self.creds, self.encrypt_creds)
        self.assertTrue(
            os.path.isfile(self.encrypt_creds))

    def test_decrypt_file_data(self):
        source_file = open(self.creds, 'rb')
        source_data = source_file.read()
        credentials.encrypt_file_data(
            self.key, self.creds, self.encrypt_creds)
        decrypted_data = credentials.decrypt_file_data(
            self.key, self.encrypt_creds)
        self.assertEqual(
            source_data, decrypted_data)

    def test_storing_and_retrieving_pass_from_Windows_vault(self):
        self.assertIsNone(
            credentials.store_in_vault(
                self.app, self.user, self.passw))
        self.assertEqual(
            credentials.get_from_vault(self.app, self.user),
            self.passw)

    def test_store_goo_folder_ids_returns_False_when_update_dir_not_specified(self):
        # populate shelve with appropriate values
        u = shelve.open(self.user_data, writeback=True)
        u['paths'] = {'update_dir': ''}
        # test the structure
        self.assertIn('paths', u)
        p = u['paths']
        self.assertIn('update_dir', p)
        u.close()

        # test the main condition
        self.assertFalse(
            credentials.store_goo_folder_ids(
                self.user_data, self.goo_folders))

    def test_store_goo_folder_ids_returns_False_when_shelve_poorly_constructed(self):
        # populate shelve with appropriate values
        u = shelve.open(self.user_data, writeback=True)
        # test the structure
        self.assertNotIn('paths', u)
        u.close()

        # test the main condition
        self.assertFalse(
            credentials.store_goo_folder_ids(
                self.user_data, self.goo_folders))

    def test_store_goo_folder_ids_returns_False_when_folder_ids_json_missing(self):
        # populate shelve with appropriate values
        u = shelve.open(self.user_data, writeback=True)
        u['paths'] = {'update_dir': os.getcwd()}
        # test the structure
        self.assertIn('paths', u)
        p = u['paths']
        self.assertIn('update_dir', p)
        u.close()

        self.assertFalse(
            credentials.store_goo_folder_ids(
                self.user_data, 'missing_file.json'))

    def test_store_goo_folder_ids_returns_True(self):
        # populate shelve with appropriate values
        u = shelve.open(self.user_data, writeback=True)
        u['paths'] = {'update_dir': os.getcwd()}
        # test the structure
        self.assertIn('paths', u)
        p = u['paths']
        self.assertIn('update_dir', p)
        u.close()

        self.assertTrue(
            credentials.store_goo_folder_ids(
                self.user_data, self.goo_folders))



if __name__ == '__main__':
    unittest.main()
