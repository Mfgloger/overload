# -*- coding: utf-8 -*-

import unittest
from mock import MagicMock, patch
from datetime import datetime


from context import PVRReport, PVR_NYPLReport
from context import bibs


class Test_PVRReport(unittest.TestCase):

    def setUp(self):
        attrs1 = dict(
            t001='bl41266045',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[u'BTSERIES'],
            t947=[],
            sierraId=None,
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            vendor='BTSERIES',
            dstLibrary='branches',
            action='attach',)

        attrs2 = dict(
            t001='41266045',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=['BTCLSD'],
            t947=[],
            sierraId='01234569',
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')

        attrs3 = dict(
            t001='41266045',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=['INGRAM'],
            t947=[],
            sierraId='01234568',
            bCallNumber='FIC ROWLING',
            rCallNumber=['JFE 03-7401'],
            catSource='inhouse',
            ownLibrary='mixed')

        self.vendor_meta = MagicMock()
        self.vendor_meta.configure_mock(**attrs1)
        self.inhouse_meta1 = MagicMock()
        self.inhouse_meta1.configure_mock(**attrs2)
        self.inhouse_meta2 = MagicMock()
        self.inhouse_meta2.configure_mock(**attrs3)

    def test_to_dict(self):
        keys = ['inhouse_dups', 'target_sierraId', 'vendor',
                'resource_id', 'action', 'inhouse_callNo_matched',
                'callNo_match', 'updated_by_vendor']
        report = PVRReport(
            self.vendor_meta, [self.inhouse_meta1, self.inhouse_meta2])
        self.assertEqual(report.to_dict().keys(), keys)
        print report.to_dict()

    def test_determine_resource_id(self):
        # if control field
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertEqual(report.to_dict()['resource_id'], 'bl41266045')

        # if no control field
        self.vendor_meta.t001 = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertEqual(report.to_dict()['resource_id'], '0439136350')

        # if only 024 present
        self.vendor_meta.t020 = []
        self.vendor_meta.t024 = ['12345']
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertEqual(report.to_dict()['resource_id'], '12345')

    def test_determine_record_updated(self):
        # vendor bib not updated - same date in 005
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertFalse(
            report._determine_record_updated(
                self.inhouse_meta1))

        # vendor bib has newer date in 005 (updated)
        report = PVRReport(self.vendor_meta, [self.inhouse_meta2])
        self.assertTrue(
            report._determine_record_updated(
                self.inhouse_meta2))

        # if vedor bib updated and inhouse bib doesn't have 005
        self.inhouse_meta1.t005 = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertTrue(
            report._determine_record_updated(
                self.inhouse_meta1))

        # if vendor bib doesn't have 005
        self.vendor_meta.t005 = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertFalse(
            report._determine_record_updated(
                self.inhouse_meta2))

    def test_determine_callNo_match(self):
        # match
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertTrue(
            report._determine_callNo_match(
                self.inhouse_meta1))
        # no match
        self.inhouse_meta1.bCallNumber = 'J FIC ROWLING'
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertFalse(
            report._determine_callNo_match(
                self.inhouse_meta1))

        # inhouse bib lacks call number
        self.inhouse_meta1.bCallNumber = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertTrue(
            report._determine_callNo_match(
                self.inhouse_meta1))

        # vendor callNo is not provided
        self.vendor_meta.bCallNumber = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertTrue(
            report._determine_callNo_match(
                self.inhouse_meta2))

    def test_order_inhouse_meta(self):
        report = PVRReport(
            self.vendor_meta, [self.inhouse_meta1, self.inhouse_meta2])
        self.assertEqual(
            report._meta_inhouse[0].sierraId, '01234569')
        self.assertEqual(
            report._meta_inhouse[1].sierraId, '01234568')


class TestNYPL_PVRReport(unittest.TestCase):

    def setUp(self):
        attrs1 = dict(
            t001='bl41266045',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[u'BTSERIES'],
            t947=[],
            sierraId=None,
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            vendor='BTSERIES',
            dstLibrary='branches',
            action='attach',)

        attrs2 = dict(
            t001='41266045',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=['BTCLSD'],
            t947=[],
            sierraId='01234567',
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')

        attrs3 = dict(
            t001='41266045',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=['INGRAM'],
            t947=[],
            sierraId='01234568',
            bCallNumber='FIC ROWLING',
            rCallNumber=['JFE 03-7401'],
            catSource='inhouse',
            ownLibrary='mixed')

        self.vendor_meta = MagicMock()
        self.vendor_meta.configure_mock(**attrs1)
        self.inhouse_meta1 = MagicMock()
        self.inhouse_meta1.configure_mock(**attrs2)
        self.inhouse_meta2 = MagicMock()
        self.inhouse_meta2.configure_mock(**attrs3)

    # @patch('overload.bibs.bibs.VendorBibMeta')
    # def test_to_dict(self):
    #     # assert mock_vendor_meta is bibs.VendorBibMeta

    #     report = PVR_NYPLReport(
    #         'branches', 'cat', self.vendor_meta, [self.inhouse_meta1, self.inhouse_meta2])
    #     print report.to_dict()

if __name__ == '__main__':
    unittest.main()