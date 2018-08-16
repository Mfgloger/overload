# -*- coding: utf-8 -*-

import unittest
import os

from context import md5
from context import remove_files


class TestStringDigest(unittest.TestCase):
    """Tests scrambling for security stored strings"""

    def test_md5_digest(self):
        import hashlib
        hash_md5 = hashlib.md5('shrubbery'.encode('utf-8'))
        self.assertEqual(hash_md5.hexdigest(), md5('shrubbery'))


class TestDeleteFile(unittest.TestCase):
    """Tests deletion of a files"""

    def setUp(self):
        self.fh1 = 't1.csv'
        self.fh2 = 't2.csv'
        fh1 = open(self.fh1, 'w')
        fh1.close()
        fh2 = open(self.fh2, 'w')
        fh2.close()

    def tearDown(self):
        try:
            if os.path.isfile(self.fh1):
                os.remove(self.fh1)
            if os.path.isfile(self.fh2):
                os.remove(self.fh2)
        except Exception as e:
            print(e)

    def test_None(self):
        self.assertFalse(remove_files(None))

    def test_single_file(self):
        self.assertTrue(remove_files(self.fh1))
        self.assertFalse(os.path.isfile(self.fh1))

    def test_multi_files(self):
        self.assertTrue(remove_files([self.fh1, self.fh2]))
        self.assertFalse(os.path.isfile(self.fh1))
        self.assertFalse(os.path.isfile(self.fh2))

    def test_single_non_existent(self):
        self.assertTrue(remove_files('some_fh.csv'))

    def test_multi_mixed(self):
        self.assertTrue(remove_files([self.fh1, 'some_fh.csv']))
        self.assertFalse(os.path.isfile(self.fh1))


if __name__ == '__main__':
    unittest.main()
