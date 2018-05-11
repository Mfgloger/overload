# -*- coding: utf-8 -*-

import unittest
from mock import MagicMock
from datetime import datetime


from context import PVRReport, PVR_NYPLReport


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
            dstLibrary='branches')

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
        attrs4 = dict(
            t001='41266046',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=['Sulaiman'],
            t947=[],
            sierraId='01234510',
            bCallNumber=None,
            rCallNumber=['JFE 03-7401'],
            catSource='inhouse',
            ownLibrary='research')

        self.vendor_meta = MagicMock()
        self.vendor_meta.configure_mock(**attrs1)
        self.inhouse_meta1 = MagicMock()
        self.inhouse_meta1.configure_mock(**attrs2)
        self.inhouse_meta2 = MagicMock()
        self.inhouse_meta2.configure_mock(**attrs3)
        self.inhouse_meta3 = MagicMock()
        self.inhouse_meta3.configure_mock(**attrs4)

    def test_determine_resource_id(self):
        # if control field
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertEqual(report.vendor_id, 'bl41266045')

        # if no control field
        self.vendor_meta.t001 = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertEqual(report.vendor_id, '0439136350')

        # if only 024 present
        self.vendor_meta.t020 = []
        self.vendor_meta.t024 = ['12345']
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertEqual(report.vendor_id, '12345')

    def test_determine_vendor_callNo(self):
        self.vendor_meta.dstLibrary = 'research'
        self.vendor_meta.bCallNumber = None
        self.vendor_meta.rCallNumber = ['JEF 1234']
        self.vendor_meta.vendor = 'Sulaiman'
        report = PVRReport(self.vendor_meta, [self.inhouse_meta3])
        self.assertEquals(report.vendor_callNo, 'JEF 1234')

        # if rCallNumber is None
        self.vendor_meta.rCallNumber = []
        report = PVRReport(self.vendor_meta, [self.inhouse_meta3])
        self.assertIsNone(report.vendor_callNo)

    def test_compare_update_timestamp(self):
        # vendor bib not updated - same date in 005
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertFalse(
            report._compare_update_timestamp(
                self.inhouse_meta1))

        # vendor bib has newer date in 005 (updated)
        report = PVRReport(self.vendor_meta, [self.inhouse_meta2])
        self.assertTrue(
            report._compare_update_timestamp(
                self.inhouse_meta2))

        # if vedor bib updated and inhouse bib doesn't have 005
        self.inhouse_meta1.t005 = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertTrue(
            report._compare_update_timestamp(
                self.inhouse_meta1))

        # if vendor bib doesn't have 005
        self.vendor_meta.t005 = None
        report = PVRReport(self.vendor_meta, [self.inhouse_meta1])
        self.assertFalse(
            report._compare_update_timestamp(
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
                self.inhouse_meta1))

    def test_order_inhouse_meta(self):
        report = PVRReport(
            self.vendor_meta, [self.inhouse_meta1, self.inhouse_meta2])
        self.assertEqual(
            report._meta_inhouse[0].sierraId, '01234568')
        self.assertEqual(
            report._meta_inhouse[1].sierraId, '01234569')


class TestPVR_NYPLReport(unittest.TestCase):
    """
    details of scenarios tested: https://bit.ly/2JmgNsV
    """

    def setUp(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')

        attrs2 = dict(
            t001='01234',
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
            t001='01234',
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

        attrs4 = dict(
            t001='01235',
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
            sierraId='01234569',
            bCallNumber=None,
            rCallNumber=['JFE 03-7401'],
            catSource='inhouse',
            ownLibrary='research')

        self.vendor_meta = MagicMock()
        self.vendor_meta.configure_mock(**attrs1)
        self.inhouse_meta1 = MagicMock()
        self.inhouse_meta1.configure_mock(**attrs2)
        self.inhouse_meta2 = MagicMock()
        self.inhouse_meta2.configure_mock(**attrs3)
        self.inhouse_meta3 = MagicMock()
        self.inhouse_meta3.configure_mock(**attrs4)

        self.report = PVR_NYPLReport(
            'cat', self.vendor_meta,
            [self.inhouse_meta1, self.inhouse_meta2, self.inhouse_meta3])

    def test_group_by_library(self):
        self.assertEqual(
            self.report._matched[0].sierraId, '01234567')
        self.assertEqual(
            self.report.mixed[0], '01234568')
        self.assertEqual(
            self.report.other[0], '01234569')

    def test_to_dict(self):
        self.assertEqual(
            self.report.to_dict().keys(),
            ['inhouse_dups', 'vendor', 'vendor_id', 'updated_by_vendor',
             'target_sierraId', 'mixed', 'target_callNo', 'vendor_callNo',
             'other', 'callNo_match', 'action'])
        self.assertIsInstance(
            self.report.to_dict()['vendor_id'], str)
        self.assertIsInstance(
            self.report.to_dict()['vendor'], str)
        self.assertIsInstance(
            self.report.to_dict()['updated_by_vendor'], bool)
        self.assertIsInstance(
            self.report.to_dict()['callNo_match'], bool)
        self.assertIsInstance(
            self.report.to_dict()['inhouse_dups'], list)
        self.assertIsInstance(
            self.report.to_dict()['target_sierraId'], str)
        self.assertIsInstance(
            self.report.to_dict()['mixed'], list)
        self.assertIsInstance(
            self.report.to_dict()['target_callNo'], str)
        self.assertIsInstance(
            self.report.to_dict()['vendor_callNo'], str)
        self.assertIsInstance(
            self.report.to_dict()['other'], list)
        self.assertIsInstance(
            self.report.to_dict()['action'], str)

    def test_cat_scenario1(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='01234567',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'overlay')
        self.assertEqual(
            report.target_sierraId, '01234567')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario2(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001='1234',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='01234567',
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'attach')
        self.assertEqual(
            report.target_sierraId, '01234567')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertEqual(
            report.target_callNo, 'FIC ROWLING')
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario3(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='01234567',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        attrs3 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='01234568',
            bCallNumber=None,
            rCallNumber=['JFE 1234'],
            catSource='vendor',
            ownLibrary='research')
        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        inhouse_meta2 = MagicMock()
        inhouse_meta2.configure_mock(**attrs3)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1, inhouse_meta2])
        self.assertEqual(
            report.action, 'overlay')
        self.assertEqual(
            report.target_sierraId, '01234567')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['01234568'])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario4(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001='1234',
            t003='OCoLC',
            t005=datetime.strptime(
                '20130731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='01234567',
            bCallNumber='J FIC ROWLING',
            rCallNumber=[],
            catSource='inhouse',
            ownLibrary='branches')
        attrs3 = dict(
            t001='1235',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='01234568',
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        inhouse_meta2 = MagicMock()
        inhouse_meta2.configure_mock(**attrs3)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1, inhouse_meta2])
        self.assertEqual(
            report.action, 'attach')
        self.assertEqual(
            report.target_sierraId, '01234568')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertEqual(
            report.target_callNo, 'FIC ROWLING')
        self.assertEqual(
            report.inhouse_dups, ['01234567', '01234568'])

    def test_cat_scenario5(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        attrs3 = dict(
            t001='1235',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000002',
            bCallNumber='J FIC ROWLING',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        inhouse_meta2 = MagicMock()
        inhouse_meta2.configure_mock(**attrs3)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1, inhouse_meta2])
        self.assertEqual(
            report.action, 'overlay')
        self.assertEqual(
            report.target_sierraId, '000002')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertFalse(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertTrue(
            report.updated_by_vendor)
        self.assertEqual(
            report.target_callNo, 'J FIC ROWLING')
        self.assertEqual(
            report.inhouse_dups, ['000001', '000002'])

    def test_cat_scenario6(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001='oc0001',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            catSource='inhouse',
            ownLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'attach')
        self.assertEqual(
            report.target_sierraId, '000001')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertEqual(
            report.target_callNo, 'FIC ROWLING')
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario7(self):
        attrs1 = dict(
            t001='bl001',
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
            dstLibrary='branches')
        attrs2 = dict(
            t001='oc0001',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber='FIC ROWLING',
            rCallNumber=['JFE 00124'],
            catSource='inhouse',
            ownLibrary='mixed')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'insert')
        self.assertIsNone(
            report.target_sierraId)
        self.assertEqual(
            report.mixed, ['000001'])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTSERIES')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario8(self):
        attrs1 = dict(
            t001='bl001',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[u'BTPBP'],
            t947=[],
            sierraId=None,
            bCallNumber='FIC ROWLING',
            rCallNumber=[],
            vendor='BTPBP',
            dstLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)

        report = PVR_NYPLReport(
            'cat', vendor_meta, [])
        self.assertEqual(
            report.action, 'insert')
        self.assertIsNone(
            report.target_sierraId)
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'BTPBP')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'FIC ROWLING')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario11(self):
        attrs1 = dict(
            t001='bl001',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=[],
            t022=[],
            t024=['012345', '0123456'],
            t028=[],
            t901=[u'MWT'],
            t947=[],
            sierraId=None,
            bCallNumber='DVD M',
            rCallNumber=[],
            vendor='MWT',
            dstLibrary='branches')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['012345', '0123456'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        attrs3 = dict(
            t001='1235',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000002',
            bCallNumber=None,
            rCallNumber=['JEF 1234'],
            catSource='inhouse',
            ownLibrary='research')
        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        inhouse_meta2 = MagicMock()
        inhouse_meta2.configure_mock(**attrs3)
        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1, inhouse_meta2])
        self.assertEqual(
            report.action, 'overlay')
        self.assertEqual(
            report.target_sierraId, '000001')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['000002'])
        self.assertEqual(
            report.vendor, 'MWT')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'DVD M')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario12(self):
        attrs1 = dict(
            t001='bl001',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=['Sulaiman'],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='Sulaiman',
            dstLibrary='research')

        attrs2 = dict(
            t001='on0123',
            t003='OCoLC',
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['012345', '0123456'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber='ARA FIC B',
            rCallNumber=[],
            catSource='inhouse',
            ownLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)

        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'insert')
        self.assertIsNone(
            report.target_sierraId)
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['000001'])
        self.assertEqual(
            report.vendor, 'Sulaiman')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_cat_scenario13(self):
        attrs1 = dict(
            t001='on0123',
            t003=None,
            t005=datetime.strptime(
                '20120731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=[],
            t022=[],
            t024=[],
            t028=[],
            t901=['Sulaiman'],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='Sulaiman',
            dstLibrary='research')

        attrs2 = dict(
            t001='on0123',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=[],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=['JEF ARA 1234'],
            catSource='vendor',
            ownLibrary='research')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)

        report = PVR_NYPLReport(
            'cat', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'overlay')
        self.assertEquals(
            report.target_sierraId, '000001')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'Sulaiman')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertTrue(
            report.updated_by_vendor)
        self.assertEquals(
            report.target_callNo, 'JEF ARA 1234')
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario1(self):
        attrs1 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='INGRAM',
            dstLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [])
        self.assertEqual(
            report.action, 'insert')
        self.assertIsNone(
            report.target_sierraId)
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'INGRAM')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario2(self):
        attrs1 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='INGRAM',
            dstLibrary='branches')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'attach')
        self.assertEquals(
            report.target_sierraId, '000001')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'INGRAM')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario3(self):
        attrs1 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='INGRAM',
            dstLibrary='branches')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')
        attrs3 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000002',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='research')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        inhouse_meta2 = MagicMock()
        inhouse_meta2.configure_mock(**attrs3)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [inhouse_meta1, inhouse_meta2])
        self.assertEqual(
            report.action, 'attach')
        self.assertEquals(
            report.target_sierraId, '000001')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['000002'])
        self.assertEqual(
            report.vendor, 'INGRAM')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario4(self):
        attrs1 = dict(
            t001='wlo001',
            t003=None,
            t005=None,
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='Sentrum',
            dstLibrary='branches')
        attrs2 = dict(
            t001='on001',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=['0439136350', '9780439136358'],
            t022=[],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=['JEF 001'],
            catSource='inhouse',
            ownLibrary='research')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'insert')
        self.assertIsNone(
            report.target_sierraId)
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['000001'])
        self.assertEqual(
            report.vendor, 'Sentrum')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario7(self):
        attrs1 = dict(
            t001='MWT001',
            t003=None,
            t005=None,
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=[],
            vendor='MWT',
            dstLibrary='branches')
        attrs2 = dict(
            t001='on001',
            t003='OCoLC',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber='DVD M',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'attach')
        self.assertEqual(
            report.target_sierraId, '000001')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, [])
        self.assertEqual(
            report.vendor, 'MWT')
        self.assertTrue(
            report.callNo_match)
        self.assertIsNone(
            report.vendor_callNo)
        self.assertFalse(
            report.updated_by_vendor)
        self.assertEqual(
            report.target_callNo, 'DVD M')
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario8(self):
        attrs1 = dict(
            t001='MWT001',
            t003=None,
            t005=None,
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=['JER DVD'],
            vendor='MWT',
            dstLibrary='research')
        attrs2 = dict(
            t001=None,
            t003=None,
            t005=None,
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber=None,
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [inhouse_meta1])
        self.assertEqual(
            report.action, 'insert')
        self.assertIsNone(
            report.target_sierraId)
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['000001'])
        self.assertEqual(
            report.vendor, 'MWT')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'JER DVD')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertIsNone(
            report.target_callNo)
        self.assertEqual(
            report.inhouse_dups, [])

    def test_sel_scenario9(self):
        attrs1 = dict(
            t001='MWT001',
            t003=None,
            t005=None,
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId=None,
            bCallNumber=None,
            rCallNumber=['JER DVD'],
            vendor='MWT',
            dstLibrary='research')
        attrs2 = dict(
            t001='oc0001',
            t003='MWT',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000001',
            bCallNumber='DVD M',
            rCallNumber=[],
            catSource='vendor',
            ownLibrary='branches')

        attrs3 = dict(
            t001='oc0002',
            t003='MWT',
            t005=datetime.strptime(
                '20100731084140.9',
                '%Y%m%d%H%M%S.%f'),
            t020=[],
            t022=['0439136350', '9780439136358'],
            t024=[],
            t028=[],
            t901=[],
            t947=[],
            sierraId='000002',
            bCallNumber=None,
            rCallNumber=['JER DVD'],
            catSource='vendor',
            ownLibrary='research')

        vendor_meta = MagicMock()
        vendor_meta.configure_mock(**attrs1)
        inhouse_meta1 = MagicMock()
        inhouse_meta1.configure_mock(**attrs2)
        inhouse_meta2 = MagicMock()
        inhouse_meta2.configure_mock(**attrs3)

        report = PVR_NYPLReport(
            'sel', vendor_meta, [inhouse_meta1, inhouse_meta2])
        self.assertEqual(
            report.action, 'attach')
        self.assertEqual(
            report.target_sierraId, '000002')
        self.assertEqual(
            report.mixed, [])
        self.assertEqual(
            report.other, ['000001'])
        self.assertEqual(
            report.vendor, 'MWT')
        self.assertTrue(
            report.callNo_match)
        self.assertEqual(
            report.vendor_callNo, 'JER DVD')
        self.assertFalse(
            report.updated_by_vendor)
        self.assertEqual(
            report.target_callNo, 'JER DVD')
        self.assertEqual(
            report.inhouse_dups, [])



if __name__ == '__main__':
    unittest.main()