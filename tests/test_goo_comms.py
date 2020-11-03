# -*- coding: utf-8 -*-


from datetime import date, datetime
import unittest
from mock import patch
import requests_mock
import os
import shelve
import pandas as pd

# from context import credentials
from context import goo
from context import goo_comms as gc
from context import GAPP, GUSER
from context import setup_dirs



class TestNamingSheets(unittest.TestCase):
    """Test naming convention for google sheets"""

    def test_positive_1st_quarter(self):
        test_dates = [
            "2020-07-01",
            "2020-07-31",
            "2020-08-15",
            "2020-08-31",
            "2020-09-01",
            "2020-09-30"
        ]
        for td in test_dates:
            test_date = datetime.strptime(td, "%Y-%m-%d").date()
            self.assertEqual(gc.determine_quarter(test_date), "1Q")

    def test_invalid_1st_quarter(self):
        test_date = datetime.strptime("2020-06-30", "%Y-%m-%d").date()
        self.assertNotEqual(gc.determine_quarter(test_date), "1Q")

    def test_2nd_quarter(self):
        test_dates = [
            "2020-10-01",
            "2020-10-31",
            "2020-11-15",
            "2020-11-30",
            "2020-12-01",
            "2020-12-31"
        ]
        for td in test_dates:
            test_date = datetime.strptime(td, "%Y-%m-%d").date()
            self.assertEqual(gc.determine_quarter(test_date), "2Q")

    def test_3rd_quarter(self):
        test_dates = [
            "2020-01-01",
            "2020-01-31",
            "2020-02-15",
            "2020-02-28",
            "2020-03-01",
            "2020-03-31"
        ]
        for td in test_dates:
            test_date = datetime.strptime(td, "%Y-%m-%d").date()
            self.assertEqual(gc.determine_quarter(test_date), "3Q")

    def test_4rd_quarter(self):
        test_dates = [
            "2020-04-01",
            "2020-04-30",
            "2020-05-15",
            "2020-05-31",
            "2020-06-01",
            "2020-06-30"
        ]
        for td in test_dates:
            test_date = datetime.strptime(td, "%Y-%m-%d").date()
            self.assertEqual(gc.determine_quarter(test_date), "4Q")

    def test_fiscal_year_of_1st_and_2nd_quarter(self):
        td = datetime.strptime("2020-07-01", "%Y-%m-%d").date()
        self.assertEqual(gc.determine_fiscal_year(td, "1Q"), "2020/21")
        self.assertNotEqual(gc.determine_fiscal_year(td, "3Q"), "2020/21")

    def test_fiscal_year_of_3rd_and_4th_quarter(self):
        td = datetime.strptime("2021-03-01", "%Y-%m-%d").date()
        self.assertEqual(gc.determine_fiscal_year(td, "3Q"), "2020/21")
        self.assertNotEqual(gc.determine_fiscal_year(td, "1Q"), "2020/21")



# class TestGooCommunications(unittest.TestCase):

#     def setUp(self):
#         self.auth = goo.get_access_token(
#             GAPP, GUSER)
#         # get google folder id
#         user_data = shelve.open(setup_dirs.USER_DATA)
#         self.bpl_parent_id = user_data['gdrive']['bpl_folder_id']
#         self.nypl_parent_id = user_data['gdrive']['nypl_folder_id']
#         user_data.close()

#         # set test dataframe
#         self.date_today = date.today().strftime('%y-%m-%d')
#         self.dup_type = 'dups'
#         self.nypl_sheets = ['branches', 'research']
#         self.bpl_sheets = []
#         test_data = dict(
#             date=[self.date_today, self.date_today],
#             agency=['CAT', 'CAT'],
#             vendor=['TEST', 'TEST'],
#             vendor_id=['ven_test123', 'ven_test124'],
#             target_id=['tar_123', None],
#             dups=['tar_123, tar_234', None],
#             mixed=['tar_345', None],
#             other=['tar_456', 'tar_457'],
#             corrected=['no', 'no'])
#         testdf = pd.DataFrame.from_dict(test_data)
#         testdf = testdf[[
#             'date', 'agency', 'vendor', 'vendor_id', 'target_id',
#             'dups', 'mixed', 'other', 'corrected']]
#         self.data = testdf.values.tolist()

    # def test_send2sheet_dup_report(self):
    #     response = gc.send2sheet(
    #         self.dup_type, self.date_today, self.bpl_parent_id,
    #         self.nypl_sheets[0], self.data)

    #     self.assertEqual(
    #         response['updatedRows'],
    #         len(self.data))


if __name__ == '__main__':
    unittest.main()
