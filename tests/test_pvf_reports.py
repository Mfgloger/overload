# -*- coding: utf-8 -*-

import unittest
import shelve
import pandas as pd

from context import reports


class Test_Reports(unittest.TestCase):
    def setUp(self):
        d = {
            '1': {
                'vendor_id': 'ven0001',
                'vendor': 'TEST VENDOR1',
                'updated_by_vendor': False,
                'callNo_match': True,
                'target_callNo': 'TEST CALL',
                'vendor_callNo': 'TEST CALL',
                'inhouse_dups': [],
                'target_sierraId': 'b0001',
                'mixed': ['b0003'],
                'other': ['b0004'],
                'action': 'attach'},
            '2': {
                'vendor_id': 'ven0002',
                'vendor': 'TEST VENDOR2',
                'updated_by_vendor': True,
                'callNo_match': False,
                'target_callNo': 'TEST CALL A',
                'vendor_callNo': 'TEST CALL B',
                'inhouse_dups': [],
                'target_sierraId': 'b0002',
                'mixed': [],
                'other': [],
                'action': 'overlay'},
        }
        stats_shelf = shelve.open('temp')
        for key, value in d.iteritems():
            stats_shelf[key] = value
        stats_shelf.close()

    def cleanUp(self):
        stats_shelf = shelve.open('temp')
        stats_shelf.clear()
        stats_shelf.close()

    def test_shelf2dataframe(self):
        df = reports.shelf2dataframe('temp')
        self.assertIsInstance(
            df, pd.DataFrame)
        self.assertEqual(
            list(df.columns.values),
            ['action', 'callNo_match', 'inhouse_dups', 'mixed', 'other', 'target_callNo', 'target_sierraId', 'updated_by_vendor', 'vendor', 'vendor_callNo', 'vendor_id'])
        self.assertEqual(
            df.shape, (2, 11))
        # check if replaces empty strings with np.NaN values
        self.assertEqual(
            df.index[df['mixed'].isnull()].tolist(),
            [2])

    def test_create_nypl_stats(self):
        df = reports.shelf2dataframe('temp')
        stats = reports.create_stats('nypl', df)
        self.assertEqual(
            stats.shape, (2, 7))
        self.assertEqual(
            stats.columns.tolist(),
            ['vendor', 'attach', 'insert', 'update', 'total', 'mixed', 'other'])
        self.assertEqual(
            stats.iloc[0]['attach'], 1)
        self.assertEqual(
            stats.iloc[0]['vendor'], 'TEST VENDOR1')
        self.assertEqual(
            stats.iloc[0]['insert'], 0)
        self.assertEqual(
            stats.iloc[0]['update'], 0)
        self.assertEqual(
            stats.iloc[0]['total'], 1)
        self.assertEqual(
            stats.iloc[0]['mixed'], 1)
        self.assertEqual(
            stats.iloc[0]['other'], 1)
        self.assertEqual(
            stats.iloc[1]['attach'], 0)
        self.assertEqual(
            stats.iloc[1]['vendor'], 'TEST VENDOR2')
        self.assertEqual(
            stats.iloc[1]['insert'], 0)
        self.assertEqual(
            stats.iloc[1]['update'], 1)
        self.assertEqual(
            stats.iloc[1]['total'], 1)
        self.assertEqual(
            stats.iloc[1]['mixed'], 0)
        self.assertEqual(
            stats.iloc[1]['other'], 0)

    def test_create_bpl_stats(self):
        df = reports.shelf2dataframe('temp')
        stats = reports.create_stats('bpl', df)
        self.assertEqual(
            stats.shape, (2, 5))
        self.assertEqual(
            stats.columns.tolist(),
            ['vendor', 'attach', 'insert', 'update', 'total'])
        self.assertEqual(
            stats.iloc[0]['attach'], 1)
        self.assertEqual(
            stats.iloc[0]['vendor'], 'TEST VENDOR1')
        self.assertEqual(
            stats.iloc[0]['insert'], 0)
        self.assertEqual(
            stats.iloc[0]['update'], 0)
        self.assertEqual(
            stats.iloc[0]['total'], 1)
        self.assertEqual(
            stats.iloc[1]['attach'], 0)
        self.assertEqual(
            stats.iloc[1]['vendor'], 'TEST VENDOR2')
        self.assertEqual(
            stats.iloc[1]['insert'], 0)
        self.assertEqual(
            stats.iloc[1]['update'], 1)
        self.assertEqual(
            stats.iloc[1]['total'], 1)

    def test_report_dups(self):
        df = reports.shelf2dataframe('temp')
        dups = reports.report_dups('NYPL', 'branches', df)
        self.assertEqual(
            dups.index.tolist(), [1])

    def test_callNo_issues(self):
        df = reports.shelf2dataframe('temp')
        callNo = reports.report_callNo_issues(df)
        self.assertEqual(
            list(callNo.columns.values),
                ['vendor', 'vendor_id', 'target_id', 'vendor_callNo', 'target_callNo', 'duplicate bibs'])
        self.assertEqual(
            callNo.index.tolist(),[2])


if __name__ == '__main__':
    unittest.main()
