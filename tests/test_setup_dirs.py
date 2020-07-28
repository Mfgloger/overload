# -*- coding: utf-8 -*-

import os
import unittest

from context import setup_dirs as sd


class TestPaths(unittest.TestCase):
    """Test Overload related directories"""

    def test_USER_NAME(self):
        self.assertEqual(os.environ["USERNAME"], sd.USER_NAME)

    def test_APP_DIR(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"], "BookOps Apps\\Overload"),
            sd.APP_DIR)

    def test_LOG_DIR(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\changesLog"),
            sd.LOG_DIR)

    def test_PATCHING_RECORD(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\changesLog\\patching_record.txt"),
            sd.PATCHING_RECORD)

    def test_MY_DOCS(self):
        self.assertEqual(
            os.path.join(os.environ["USERPROFILE"], "Documents"),
            sd.MY_DOCS)

    def test_TEMP_DIR(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"], "BookOps Apps\\Overload\\temp"),
            sd.TEMP_DIR)

    def test_BARCODES(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\batch_barcodes.txt"),
            sd.BARCODES)

    def test_USER_DATA(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\user_data"),
            sd.USER_DATA)

    def test_DATASTORE(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\datastore.db"),
            sd.DATASTORE)

    def test_BATCH_STATS(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\batch_stats"),
            sd.BATCH_STATS)

    def test_BATCH_META(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\batch_meta"),
            sd.BATCH_META)

    def test_GETBIB_REP(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\getbib-report.csv"),
            sd.GETBIB_REP)

    def test_W2S_MULTI_ORD(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\w2s-multi-orders.csv"),
            sd.W2S_MULTI_ORD)

    def test_W2S_SKIPPED_ORD(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\w2s-skipped-orders.csv"),
            sd.W2S_SKIPPED_ORD)

    def test_WORLDCAT_CREDS(self):
        self.assertEqual(
            "Overload Creds/Worldcat",
            sd.WORLDCAT_CREDS)

    def test_GOO_CREDS(self):
        self.assertEqual(
            "Overload Creds\\Google\\goo_credentials.bin",
            sd.GOO_CREDS)

    def test_GOO_FOLDERS(self):
        self.assertEqual(
            "Overload Creds\\Google\\goo_folders.json",
            sd.GOO_FOLDERS)

    def test_MVAL_REP(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\marcedit_validation_report.txt"),
            sd.MVAL_REP)

    def test_CVAL_REP(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\combined_validation_report.txt"),
            sd.CVAL_REP)

    def test_LSPEC_REP(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\local_specs_report.txt"),
            sd.LSPEC_REP)

    def test_DVAL_REP(self):
        self.assertEqual(
            os.path.join(
                os.environ["USERPROFILE"],
                "BookOps Apps\\Overload\\temp\\default_validation_report.txt"),
            sd.DVAL_REP)


if __name__ == "__main__":
    unittest.main()
