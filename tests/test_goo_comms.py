# -*- coding: utf-8 -*-


from datetime import date
import unittest
from mock import patch
import requests_mock
import os
import shelve
import pandas as pd

# from context import credentials
from context import goo
from context import goo_comms
from context import GAPP, GUSER
from context import setup_dirs


class TestGooCommunications(unittest.TestCase):

    def setUp(self):
        self.auth = goo.get_access_token(
            GAPP, GUSER)
        # get google folder id
        user_data = shelve.open(setup_dirs.USER_DATA)
        self.bpl_parent_id = user_data['gdrive']['bpl_folder_id']
        self.nypl_parent_id = user_data['gdrive']['nypl_folder_id']
        user_data.close()

        # set test dataframe
        self.date_today = date.today().strftime('%y-%m-%d')
        self.dup_type = 'dups'
        self.nypl_sheets = ['branches', 'research']
        self.bpl_sheets = []
        test_data = dict(
            date=[self.date_today, self.date_today],
            agency=['CAT', 'CAT'],
            vendor=['TEST', 'TEST'],
            vendor_id=['ven_test123', 'ven_test124'],
            target_id=['tar_123', None],
            dups=['tar_123, tar_234', None],
            mixed=['tar_345', None],
            other=['tar_456', 'tar_457'],
            corrected=['no', 'no'])
        testdf = pd.DataFrame.from_dict(test_data)
        testdf = testdf[[
            'date', 'agency', 'vendor', 'vendor_id', 'target_id',
            'dups', 'mixed', 'other', 'corrected']]
        self.data = testdf.values.tolist()

    # def test_send2sheet_dup_report(self):
    #     response = goo_comms.send2sheet(
    #         self.dup_type, self.date_today, self.bpl_parent_id,
    #         self.nypl_sheets[0], self.data)

    #     self.assertEqual(
    #         response['updatedRows'],
    #         len(self.data))



if __name__ == '__main__':
    unittest.main()

