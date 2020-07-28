# -*- coding: utf-8 -*-

import unittest
from mock import Mock


from context import construct_sru_query, holdings_responses


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

    def test_mat_type_any(self):
        self.assertEqual(construct_sru_query("foo", mat_type="any"), "foo")

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

    def test_cat_source_any(self):
        self.assertEqual(construct_sru_query("foo", cat_source="any"), "foo")

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


class TestHoldingResponses(unittest.TestCase):
    """Tests holdings responses returned from Metadata API service"""

    def setUp(self):
        returned = {
            "extensions": [
                {
                    "attributes": {"xmlns:os": "http://a9.com/-/spec/opensearch/1.1/"},
                    "name": "os:totalResults",
                    "children": ["5"],
                },
                {
                    "attributes": {"xmlns:os": "http://a9.com/-/spec/opensearch/1.1/"},
                    "name": "os:startIndex",
                    "children": ["1"],
                },
                {
                    "attributes": {"xmlns:os": "http://a9.com/-/spec/opensearch/1.1/"},
                    "name": "os:itemsPerPage",
                    "children": ["5"],
                },
            ],
            "entries": [
                {
                    "content": {
                        "currentOclcNumber": "850939586",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939586",
                        "requestedOclcNumber": "850939586",
                        "institution": "NYP",
                    },
                    "updated": "2020-05-17T02:07:30.653Z",
                    "title": "850939586",
                },
                {
                    "content": {
                        "currentOclcNumber": "850939587",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939587",
                        "requestedOclcNumber": "850939587",
                        "institution": "NYP",
                    },
                    "updated": "2020-05-17T02:07:30.653Z",
                    "title": "850939587",
                },
                {
                    "content": {
                        "currentOclcNumber": "850939588",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939588",
                        "requestedOclcNumber": "850939588",
                        "institution": "NYP",
                    },
                    "updated": "2020-05-17T02:07:30.653Z",
                    "title": "850939588",
                },
                {
                    "content": {
                        "currentOclcNumber": "850939589",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939589",
                        "requestedOclcNumber": "850939589",
                        "institution": "NYP",
                    },
                    "updated": "2020-05-17T02:07:30.653Z",
                    "title": "850939589",
                },
                {
                    "content": {
                        "currentOclcNumber": "850939590",
                        "status": "HTTP 409 Conflict",
                        "institution": "NYP",
                        "detail": "Holding is already set for institution",
                        "requestedOclcNumber": "850939590",
                        "id": "http://worldcat.org/oclc/850939590",
                    },
                    "updated": "2020-05-17T02:07:30.654Z",
                    "title": "850939590",
                },
            ],
        }

        mock = Mock()
        attrs = {"status_code": 207, "json.return_value": returned}
        mock.configure_mock(**attrs)
        self.responses = [mock]

    def test_returns_dictionary(self):
        self.assertIsInstance(holdings_responses(self.responses), dict)

    def test_returned_dictionary(self):
        self.assertEqual(
            holdings_responses(self.responses),
            {
                "850939586": (
                    "set",
                    {
                        "currentOclcNumber": "850939586",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939586",
                        "requestedOclcNumber": "850939586",
                        "institution": "NYP",
                    },
                ),
                "850939587": (
                    "set",
                    {
                        "currentOclcNumber": "850939587",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939587",
                        "requestedOclcNumber": "850939587",
                        "institution": "NYP",
                    },
                ),
                "850939588": (
                    "set",
                    {
                        "currentOclcNumber": "850939588",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939588",
                        "requestedOclcNumber": "850939588",
                        "institution": "NYP",
                    },
                ),
                "850939589": (
                    "set",
                    {
                        "currentOclcNumber": "850939589",
                        "status": "HTTP 200 OK",
                        "id": "http://worldcat.org/oclc/850939589",
                        "requestedOclcNumber": "850939589",
                        "institution": "NYP",
                    },
                ),
                "850939590": (
                    "exists",
                    {
                        "currentOclcNumber": "850939590",
                        "status": "HTTP 409 Conflict",
                        "institution": "NYP",
                        "detail": "Holding is already set for institution",
                        "requestedOclcNumber": "850939590",
                        "id": "http://worldcat.org/oclc/850939590",
                    },
                ),
            },
        )


if __name__ == "__main__":
    unittest.main()
