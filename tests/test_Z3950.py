# -*- coding: utf-8 -*-

import unittest

from context import setup_dirs
from context import z3950_query


class TestZ3950(unittest.TestCase):
    """Test Z3950 connections"""

    def test_lc_connection(self):
        """tests if module can make connection to LC Z3950"""
        target = {'host': 'z3950.loc.gov',
                  'library': 'LC',
                  'syntax': 'USMARC',
                  'port': 7090,
                  'user': None,
                  'password': None,
                  'database': 'VOYAGER'}
        self.assertTrue(z3950_query(
            target,
            keyword='8392203313',
            qualifier='(1,7)')[0])

    def test_local_connections(self):
        """test local Z3950 connections"""
        import shelve
        user_data = shelve.open(setup_dirs.USER_DATA)
        if 'Z3950s' not in user_data:
            self.assertTrue(False, msg='no Z3950s setup in user_data file')
        else:
            for key, settings in user_data['Z3950s'].iteritems():
                self.assertTrue(z3950_query(
                    settings,
                    keyword='8392203313',
                    qualifier='(1,7)')[0])
        user_data.close()

if __name__ == "__main__":
    unittest.main()
