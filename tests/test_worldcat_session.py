# -*- coding: utf-8 -*-

import unittest

from context import construct_sru_query


class TestConstructSruQuery(unittest.TestCase):
    """test sru_query constructor"""

    def test_keyword_none(self):
        with self.assertRaises(TypeError):
            construct_sru_query(None)

    def test_keyword_type_isbn(self):
        self.assertEqual(
            construct_sru_query("1234", keyword_type="ISBN"), 'srw.bn = "1234"'
        )

    def test_keyword_type_upc(self):
        self.assertEqual(
            construct_sru_query("1234", keyword_type="UPC"), 'srw.sn = "1234"'
        )

    def test_keyword_type_issn(self):
        self.assertEqual(
            construct_sru_query("1234", keyword_type="ISSN"), 'srw.in = "1234"'
        )

    def test_keyword_type_oclc_no(self):
        self.assertEqual(
            construct_sru_query("1234", keyword_type="OCLC #"), 'srw.no = "1234"'
        )

    def test_keyword_type_lccn(self):
        self.assertEqual(
            construct_sru_query("1234", keyword_type="LCCN"), 'srw.dn = "1234"'
        )

    def test_mat_type_print(self):
        self.assertEqual(
            construct_sru_query("foo", mat_type="print"), 'foo AND srw.mt = "bks"'
        )

    def test_mat_type_large_print(self):
        self.assertEqual(
            construct_sru_query("foo", mat_type="large print"), 'foo AND srw.mt = "lpt"'
        )

    def test_mat_type_dvd(self):
        self.assertEqual(
            construct_sru_query("foo", mat_type="dvd"), 'foo AND srw.mt = "dvv"'
        )

    def test_mat_type_bluray(self):
        self.assertEqual(
            construct_sru_query("foo", mat_type="bluray"), 'foo AND srw.mt = "bta"'
        )

    def test_cat_source_dlc(self):
        self.assertEqual(
            construct_sru_query("foo", cat_source="DLC"), 'foo AND srw.pc = "dlc"'
        )

    def test_complex_query(self):
        self.assertEqual(
            construct_sru_query(
                'srw.kw = "foo"', mat_type="large print", cat_source="DLC"
            ),
            'srw.kw = "foo" AND srw.mt = "lpt" AND srw.pc = "dlc"',
        )


if __name__ == "__main__":
    unittest.main()
