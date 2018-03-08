# -*- coding: utf-8 -*-

import unittest

from context import md5


class TestStringDigest(unittest.TestCase):
    """Tests scrambling for security stored strings"""

    def test_md5_digest(self):
        import hashlib
        hash_md5 = hashlib.md5('shrubbery'.encode('utf-8'))
        self.assertEqual(hash_md5.hexdigest(), md5('shrubbery'))



if __name__ == '__main__':
    unittest.main()
