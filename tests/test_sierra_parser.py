# -*- coding: utf-8 -*-

import unittest

from context import (
    sierra_export_data,
    find_order_field,
    find_latest_full_order,
    parse_order_data,
    parse_NYPL_order_export,
)


class TestSplitingRepeatedSubfields(unittest.TestCase):
    def setUp(self):
        self.fields = [
            "o20696541^o20713575",
            "n^n",
            "",
            "",
            "a^a",
            "-^-",
            "27anf^28anf^29anf^30anf^31anf^32anf^multi^14anb",
            "b^b",
            "bt1^bt1",
            "o^o",
        ]

    def test_order_ids(self):
        self.assertEqual(find_order_field(self.fields, 0, 0), "o20696541")
        self.assertEqual(find_order_field(self.fields, 0, 1), "o20713575")

    def test_status(self):
        self.assertEqual(find_order_field(self.fields, 9, 0), "o")
        self.assertEqual(find_order_field(self.fields, 9, 1), "o")

    def test_empty_fields(self):
        self.assertEqual(find_order_field(self.fields, 2, 0), "")
        self.assertEqual(find_order_field(self.fields, 2, 1), "")


class TestFindLatestFullOrder(unittest.TestCase):
    """Test finding fully coded location orders"""

    def test_empty_list_nypl(self):
        self.assertIsNone(find_latest_full_order("NYPL", []))

    def test_empty_list_bpl(self):
        self.assertIsNone(find_latest_full_order("BPL", []))

    def test_one_order_basic_location_nypl(self):
        self.assertIsNone(find_latest_full_order("NYPL", [{"locs": "sn"}]))

    def test_one_order_basic_location_with_qty_nypl(self):
        self.assertIsNone(find_latest_full_order("NYPL", [{"locs": "wf(2)"}]))

    def test_one_order_full_location_nypl(self):
        self.assertEqual(
            find_latest_full_order("NYPL", [{"locs": "wfa0f"}]), {"locs": "wfa0f"}
        )

    def test_one_order_full_location_with_single_digit_qty_nypl(self):
        self.assertEqual(
            find_latest_full_order("NYPL", [{"locs": "wfa0f(2)"}]), {"locs": "wfa0f(2)"}
        )

    def test_one_order_full_location_with_double_digit_qty_nypl(self):
        self.assertEqual(
            find_latest_full_order("NYPL", [{"locs": "wfa0f(99)"}]),
            {"locs": "wfa0f(99)"},
        )

    def test_multi_order_full_location_with_single_digit_qty_nypl(self):
        self.assertEqual(
            find_latest_full_order(
                "NYPL", [{"locs": "wf,sn"}, {"locs": "wfa0f(2),sna0f"}]
            ),
            {"locs": "wfa0f(2),sna0f"},
        )

    def test_multi_order_latest_brief_nypl(self):
        self.assertEqual(
            find_latest_full_order(
                "NYPL", [{"locs": "wfa0f(2),sna0f"}, {"locs": "wf(2),sn"}]
            ),
            {"locs": "wfa0f(2),sna0f"},
        )

    def test_one_order_basic_location_bpl(self):
        self.assertIsNone(find_latest_full_order("BPL", [{"locs": "14"}]))

    def test_one_order_basic_location_with_qty_bpl(self):
        self.assertIsNone(find_latest_full_order("BPL", [{"locs": "13(2)"}]))

    def test_one_order_full_location_bpl(self):
        self.assertEqual(
            find_latest_full_order("BPL", [{"locs": "13anf"}]), {"locs": "13anf"}
        )

    def test_one_order_full_location_with_single_digit_qty_bpl(self):
        self.assertEqual(
            find_latest_full_order("BPL", [{"locs": "13anf(2)"}]), {"locs": "13anf(2)"}
        )

    def test_one_order_full_location_with_double_digit_qty_bpl(self):
        self.assertEqual(
            find_latest_full_order("BPL", [{"locs": "14afc(99)"}]),
            {"locs": "14afc(99)"},
        )

    def test_multi_order_full_location_with_single_digit_qty_bpl(self):
        self.assertEqual(
            find_latest_full_order("BPL", [{"locs": "14^41^50afc(2)^51afc"}]),
            {"locs": "50afc(2),14,41,51afc"},
        )

    def test_multi_order_latest_brief_bpl(self):
        self.assertEqual(
            find_latest_full_order("BPL", [{"locs": "50afc(2)^51afc^14(2)^41"}]),
            {"locs": "50afc(2),51afc,14(2),41"},
        )


class TestParsingExportsFromSierraForNYPLRL(unittest.TestCase):
    """Tests Sierra parser"""

    def setUp(self):
        fh = "sierra_export_RL_sample.txt"
        system = "NYPL"
        library = "research"
        self.data = sierra_export_data(fh, system, library)

    def test_generator(self):
        for meta, single in self.data:
            # print(meta, single_order)
            self.assertEqual(meta.__class__.__name__, "BibOrderMeta")
            self.assertTrue(single)


class TestParsingExportsFromSierraForNYPLBL(unittest.TestCase):
    """Tests Sierra parser"""

    def setUp(self):
        fh = "sierra_export-BL-sample.txt"
        system = "NYPL"
        library = "branches"
        self.data = sierra_export_data(fh, system, library)

    def test_parse_nypl_order_export(self):
        ord_list = [
            "o24598574",
            "o26228087",
            "o27310450",
            "bio",
            "",
            "",
            "",
            "",
            "",
            "7/23/18/AREC/WC",
            "08/02/2019/AREC/PR",
            "SNFL ODC",
            "c",
            "c",
            "c",
            "-",
            "j",
            "n",
            "whj0f,stj0f,yvj0f,wtj0f,woj0f(2)",
            "agj0f,alj0f,baj0f(2),bcj0f(3),bej0f,brj0f",
            "snj0f",
            "b",
            "b",
            "b",
            "0012 ",
            "0035 ",
            "o118 ",
            "a",
            "a",
            "a",
        ]

        parsed_ord = parse_NYPL_order_export(ord_list)
        self.assertEqual(
            parsed_ord[0],
            {
                "oid": "o24598574",
                "note": "",
                "venNote": "bio",
                "intNote": "7/23/18/AREC/WC",
                "code2": "c",
                "code4": "-",
                "locs": "whj0f,stj0f,yvj0f,wtj0f,woj0f(2)",
                "oFormat": "b",
                "vendor": "0012 ",
            },
        )

    def test_parsing_record_with_no_orders(self):
        meta, single = next(self.data)
        self.assertEqual(meta.__class__.__name__, "BibOrderMeta")
        self.assertIsNone(single)

    def test_parsing_record_with_multiple_orders(self):
        _, _ = next(self.data)
        meta, single = next(self.data)
        self.assertFalse(single)

        # check if the last record selected
        self.assertEqual(meta.oid, "o27310450")
        self.assertEqual(meta.callType, "fic")
        self.assertEqual(meta.audnType, "j")
        self.assertIsNone(meta.callLabel)


class TestParsingExportsFromSierraForBPL(unittest.TestCase):
    """Tests Sierra parser"""

    def setUp(self):
        fh = "sierra_export_BPL_sample.txt"
        system = "BPL"
        library = "branches"
        self.data = sierra_export_data(fh, system, library)

    def test_parser_flags_multiple_orders(self):
        meta, single_order = next(self.data)
        self.assertEqual(meta.__class__.__name__, "BibOrderMeta")
        self.assertFalse(single_order)

    def test_parser_identifies_single_orders(self):
        _, _ = next(self.data)  # skip multi order in the generator
        _, single_order = next(self.data)
        self.assertTrue(single_order)
        _, single_order = next(self.data)
        self.assertTrue(single_order)

    def test_parser_identifies_cancelled_orders(self):
        _, _ = next(self.data)
        _, _ = next(self.data)
        _, _ = next(self.data)

        # check 4th row
        meta, single = next(self.data)
        self.assertIsNone(single)
        self.assertIsNone(meta.oid)

    def test_parser_idendifies_ISBNs(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.t020, list)
        self.assertEqual(meta.t020, ["9781646040056", "1646040058"])

    def test_parser_identifies_bibNos(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.sierraId, str)
        self.assertEqual(meta.sierraId, "12261555")

    def test_parser_identifies_005(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.t005, str)
        self.assertEqual(meta.t005, "20200113144233.0")

    def test_parser_identifies_010(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.t010, str)
        self.assertEqual(meta.t010, "BL 99793722")

    def test_parser_returns_None_when_no_010(self):
        _, _ = next(self.data)
        meta, _ = next(self.data)
        self.assertIsNone(meta.t010)

    def test_parser_identifes_024(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.t024, list)
        self.assertEqual(meta.t024, ["1234"])

    def test_parser_returns_empty_list_when_no_024(self):
        _, _ = next(self.data)
        meta, _ = next(self.data)
        self.assertEqual(meta.t024, [])

    def test_parser_returns_None_when_no_035(self):
        meta, _ = next(self.data)
        self.assertIsNone(meta.t001)

    def test_parsers_identifies_t001(self):
        _, _ = next(self.data)
        meta, _ = next(self.data)
        self.assertEqual(meta.t001, "ocn1234")

    def test_parser_identifies_title(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.title, str)
        self.assertEquals(meta.title, "Build Your Own Romantic Comedy :")

    def test_parser_identifies_last_orderNo_on_multi_order(self):
        meta, _ = next(self.data)
        self.assertIsInstance(meta.oid, str)
        self.assertEquals(meta.oid, "o20713575")

    def test_parser_identifies_last_orderNo_on_single_order(self):
        _, _ = next(self.data)
        meta, _ = next(self.data)
        self.assertIsInstance(meta.oid, str)
        self.assertEquals(meta.oid, "o20703934")


if __name__ == "__main__":
    unittest.main()
