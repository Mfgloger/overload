# -*- coding: utf-8 -*-

import unittest


from context import (
    bibs,
    create_bpl_callnum,
    determine_cutter,
    determine_biographee_name,
)


class TestDetermineCutter(unittest.TestCase):
    def test_cutter_author_last_name(self):
        self.assertEqual(
            determine_cutter({"100": "Smith, John", "245": "Test title"}, "last_name"),
            "SMITH",
        )

    def test_author_first_letter(self):
        self.assertEqual(
            determine_cutter(
                {"100": "Smith, John", "245": "Test title"}, "first_letter"
            ),
            "S",
        )

    def test_author_first_letter_diacritics(self):
        self.assertEqual(
            determine_cutter(
                {"100": "Żeglarz, Bronek", "245": "Test title"}, "first_letter"
            ),
            "Z",
        )

    def test_title_first_letter_diacritics(self):
        self.assertEqual(
            determine_cutter({"245": "Żeglarz"}, "first_letter"), "Z",
        )

    def test_title_first_word_diacritics(self):
        self.assertEqual(
            determine_cutter({"245": " Żeglarz :"}, "first_word"), "ZEGLARZ",
        )

    def test_corporate_author_first_letter(self):
        self.assertEqual(
            determine_cutter(
                {"110": "Corp. Inc.", "245": " Żeglarz :"}, "first_letter"
            ),
            "C",
        )

    def test_event_author_first_letter(self):
        self.assertEqual(
            determine_cutter({"111": "Pygotham", "245": " Żeglarz :"}, "first_letter"),
            "P",
        )


class TestDetermineBiographeeName(unittest.TestCase):
    """Test creation of biographee segment of biography call number"""

    def test_None_subject_fields(self):
        self.assertIsNone(determine_biographee_name(None))

    def test_empty_dictionary(self):
        self.assertIsNone(determine_biographee_name({}))

    def test_name(self):
        self.assertEqual(determine_biographee_name({"600": "Smith, John."}), "SMITH")

    def test_name_with_diactritics(self):
        self.assertEqual(
            determine_biographee_name({"600": "Trębońska, Zdzisława"}), "TREBONSKA"
        )


class TestCreateBPLFictionCallNum(unittest.TestCase):
    """Tests creation of BPL fiction and picture book call numbers"""

    def setUp(self):
        self.leader_string = "00000cam a2200000Ia 4500"
        self.tag_008 = "961120s1988    nyu    a      000 1 eng d"
        self.tag_082 = "947.23"
        self.tag_300a = "1 volume (various pagings)"
        self.cuttering_fields = {"100": "Smith, John", "245": "Test title"}
        self.subject_fields = {
            "600": "Doe, John",
            "650": "History",
            "655": "True Crime.",
        }
        self.order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41jje"
        )

    def test_english_picture_book_with_order(self):
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aJ-E$aSMITH")

    def test_english_juv_fiction_with_order(self):
        self.tag_300a = "70 pages"
        self.tag_008 = "961120s1988    nyu    j      000 1 eng d"
        self.order_data.locs = "02jfc"
        self.order_data._determine_audience()
        self.order_data._determine_callNumber_type()
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aJ$aFIC$aSMITH")

    def test_english_young_adult_fiction_with_order(self):
        self.tag_008 = "961120s1988    nyu    d      000 1 eng d"
        self.order_data.locs = "03yfc"
        self.order_data._determine_audience()
        self.order_data._determine_callNumber_type()
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aFIC$aSMITH")

    def test_english_adult_fiction_with_order(self):
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        self.order_data.locs = "14afc"
        self.order_data._determine_audience()
        self.order_data._determine_callNumber_type()
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aFIC$aSMITH")

    def test_wl_adult_fiction_with_order(self):
        self.tag_008 = "961120s1988    nyu           000 1 spa d"
        self.leader_string = "00000cam a2200000Ia 4500"
        self.tag_300a = "1 volume (various pagings)"
        self.cuttering_fields = {"100": "Smith, John", "245": "Test title"}
        self.order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41awl"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aSPA$aFIC$aSMITH")

    def test_wl_juvenile_fiction_with_order_author_main(self):
        self.tag_008 = "961120s1988    nyu    j      000 1 spa d"
        self.leader_string = "00000cam a2200000Ia 4500"
        self.tag_300a = "300 pages"
        self.cuttering_fields = {"100": "Smith, John", "245": "Test title"}
        self.order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41jwl"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aSPA$aJ$aFIC$aSMITH")


class TestBPLBiographyCallNumber(unittest.TestCase):
    """Test creation of biography call number"""

    def setUp(self):
        self.leader_string = "00000cam a2200000Ia 4500"
        self.tag_008 = "961120s1988    nyu           000 0beng d"
        self.tag_082 = "947.23"
        self.tag_300a = "150 pages"
        self.cuttering_fields = {"100": "Smith, John", "245": "Test title"}
        self.subject_fields = {
            "600": "Doe, John",
            "650": "History",
            "655": "True Crime.",
        }
        self.order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="13abi"
        )

    def test_adult_biography(self):
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aB$aDOE$aS")

    def test_youngadult_biography(self):
        self.tag_008 = "961120s1988    nyu    d      000 0beng d"
        order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="03ybi"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aB$aDOE$aS")

    def test_juvenile_biography(self):
        self.tag_008 = "961120s1988    nyu    j      000 0beng d"
        order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="02jbi"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aJ$aB$aDOE$aS")

    def test_wl_adult_biography(self):
        self.tag_008 = "961120s1988    nyu           000 0bspa d"
        order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41awl"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aSPA$aB$aDOE$aS")

    def test_wl_juvenile_biography(self):
        self.tag_008 = "961120s1988    nyu    j      000 0bspa d"
        order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41jwl"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aSPA$aJ$aB$aDOE$aS")

    def test_biography_with_diacritics(self):
        self.tag_008 = "961120s1988    nyu           000 0apol d"
        cuttering_fields = {"100": "Łąd, Zdzichu", "245": "Ówczesny twór"}
        subject_fields = {"600": "Żeglarz, Mietek"}
        order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41awl"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            cuttering_fields,
            subject_fields,
            order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aPOL$aB$aZEGLARZ$aL")


if __name__ == "__main__":
    unittest.main()
