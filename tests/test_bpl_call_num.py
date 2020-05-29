# -*- coding: utf-8 -*-

import unittest


from context import (
    bibs,
    create_bpl_callnum,
    determine_cutter,
    determine_biographee_name,
    has_division_conflict,
    is_adult_division,
    valid_audience,
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


class TestIsAdultDivision(unittest.TestCase):
    """Tests if any of the locations is Central adult division"""

    def test_None(self):
        self.assertFalse(is_adult_division(None))

    def test_empty_string(self):
        self.assertFalse(is_adult_division(""))

    def test_02(self):
        self.assertFalse(is_adult_division("02jje^41jje"))

    def test_03(self):
        self.assertTrue(is_adult_division("03yfc^41afc"))

    def test_04(self):
        self.assertTrue(is_adult_division("04anf"))

    def test_11(self):
        self.assertTrue(is_adult_division("11anf"))

    def test_12(self):
        self.assertTrue(is_adult_division("12adv"))

    def test_13(self):
        self.assertTrue(is_adult_division("14abi"))

    def test_14(self):
        self.assertTrue(is_adult_division("14afc"))

    def test_16(self):
        self.assertTrue(is_adult_division("16anf"))

    def test_branches(self):
        self.assertFalse(is_adult_division("41jfc^45jfc^50jfc"))


class TestHasDivisionConflict(unittest.TestCase):
    """Test if Dewey classmark has Central Lib. division conflict"""

    def test_classmark_and_location_None(self):
        self.assertTrue(has_division_conflict(None, None, None))

    def test_location_None(self):
        self.assertFalse(has_division_conflict("947", None, None))

    def test_juv_audn_but_adult_division(self):
        self.assertTrue(has_division_conflict("947", "j", "13anf"))

    def test_juv_audn_and_juv_division(self):
        self.assertFalse(has_division_conflict("947", "j", "02jnf"))

    def test_adult_adun_and_juv_division(self):
        self.assertTrue(has_division_conflict("947", "a", "02jnf"))

    def test_adult_adun_and_adult_division(self):
        self.assertFalse(has_division_conflict("947", "a", "13anf"))

    def test_11(self):
        # not processed
        self.assertTrue(has_division_conflict("947", None, "11anf"))

    def test_13_religion(self):
        self.assertFalse(has_division_conflict("201.092", None, "13anb^41anf"))

    def test_13_history(self):
        self.assertFalse(has_division_conflict("947", None, "13anf"))

    def test_13_invalid_range(self):
        self.assertTrue(has_division_conflict("364.51", None, "13anf"))

    def test_14_000(self):
        self.assertTrue(has_division_conflict("000", None, "14anf"))

    def test_14_001(self):
        self.assertFalse(has_division_conflict("001", None, "14anf"))

    def test_14_002(self):
        self.assertFalse(has_division_conflict("002", None, "14anf"))

    def test_14_003(self):
        self.assertFalse(has_division_conflict("003", None, "14anf"))

    def test_14_004(self):
        self.assertTrue(has_division_conflict("004", None, "14anf"))

    def test_14_005(self):
        self.assertTrue(has_division_conflict("005", None, "14anf"))

    def test_14_006(self):
        self.assertTrue(has_division_conflict("006", None, "14anf"))

    def test_14_007(self):
        self.assertTrue(has_division_conflict("007", None, "14anf"))

    def test_14_008(self):
        self.assertTrue(has_division_conflict("008", None, "14anf"))

    def test_14_009(self):
        self.assertTrue(has_division_conflict("009", None, "14anf"))

    def test_14_010(self):
        self.assertFalse(has_division_conflict("010", None, "14anf"))

    def test_14_020(self):
        self.assertFalse(has_division_conflict("025", None, "14anf"))

    def test_14_030(self):
        self.assertFalse(has_division_conflict("030", None, "14anf"))

    def test_14_040(self):
        self.assertTrue(has_division_conflict("040", None, "14anf"))

    def test_14_050(self):
        self.assertFalse(has_division_conflict("050", None, "14anf"))

    def test_14_060(self):
        self.assertFalse(has_division_conflict("060", None, "14anf"))

    def test_14_070(self):
        self.assertFalse(has_division_conflict("070", None, "14anf"))

    def test_14_080(self):
        self.assertFalse(has_division_conflict("080", None, "14anf"))

    def test_14_090(self):
        self.assertFalse(has_division_conflict("090", None, "14anf"))

    def test_14_1xx(self):
        self.assertTrue(has_division_conflict("100", None, "14anf"))

    def test_14_2xx(self):
        self.assertTrue(has_division_conflict("200", None, "14anf"))

    def test_14_4xx(self):
        self.assertFalse(has_division_conflict("400", None, "14anf"))

    def test_14_5xx(self):
        self.assertTrue(has_division_conflict("500", None, "14anf"))

    def test_14_6xx(self):
        self.assertTrue(has_division_conflict("600", None, "14anf"))

    def test_14_7xx(self):
        self.assertTrue(has_division_conflict("700", None, "14anf"))

    def test_14_8xx(self):
        # during the initial stage do not process 8xx
        self.assertTrue(has_division_conflict("800", None, "14anf"))

    def test_14_9xx(self):
        self.assertTrue(has_division_conflict("900", None, "14anf"))

    def test_16_000(self):
        self.assertTrue(has_division_conflict("000", None, "16anf"))

    def test_16_001(self):
        self.assertTrue(has_division_conflict("001", None, "16anf"))

    def test_16_004(self):
        self.assertFalse(has_division_conflict("004", None, "16anf"))

    def test_16_005(self):
        self.assertFalse(has_division_conflict("005", None, "16anf"))

    def test_16_006(self):
        self.assertFalse(has_division_conflict("006", None, "16anf"))

    def test_16_010(self):
        self.assertTrue(has_division_conflict("010", None, "16anf"))

    def test_16_1xx(self):
        self.assertFalse(has_division_conflict("100", None, "16anf"))

    def test_16_2xx(self):
        self.assertTrue(has_division_conflict("200", None, "16anf"))

    def test_16_3xx(self):
        self.assertFalse(has_division_conflict("300", None, "16anf"))

    def test_16_4xx(self):
        self.assertTrue(has_division_conflict("400", None, "16anf"))

    def test_16_5xx(self):
        self.assertFalse(has_division_conflict("500", None, "16anf"))

    def test_16_6xx(self):
        self.assertFalse(has_division_conflict("600", None, "16anf"))

    def test_16_7xx(self):
        self.assertTrue(has_division_conflict("700", None, "16anf"))

    def test_16_8xx(self):
        self.assertTrue(has_division_conflict("800", None, "16anf"))

    def test_16_9xx(self):
        self.assertTrue(has_division_conflict("900", None, "16anf"))


class TestValidAudience(unittest.TestCase):
    """Tests conflicts between bib and order audience codes"""

    def test_None(self):
        self.assertIsNone(valid_audience(None, None, None))

    def test_bib_code_None(self):
        leader = "00000cam a2200000Ia 4500"
        self.assertEqual(valid_audience(leader, None, "a"), "a")

    def test_order_None(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = tag_008 = "961120s1988    nyu           000 i eng d"
        self.assertEqual(valid_audience(leader, tag_008, None), "a")

    def test_conflict(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = tag_008 = "961120s1988    nyu           000 i eng d"
        self.assertFalse(valid_audience(leader, tag_008, "j"))

    def test_adult_vs_young_adult(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = tag_008 = "961120s1988    nyu           000 1 eng d"
        self.assertEqual(valid_audience(leader, tag_008, "y"), "a")

    def test_juvenile_no_conflict(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = tag_008 = "961120s1988    nyu    a      000 1 eng d"
        self.assertEqual(valid_audience(leader, tag_008, "j"), "j")

    def test_ya_bib_and_adult_order(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = tag_008 = "961120s1988    nyu    d      000 1 eng d"
        self.assertFalse(valid_audience(leader, tag_008, "a"))


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

    def test_english_adult_dewey_no_division_conflicts_diacritics(self):
        self.tag_008 = "961120s1988    nyu           000 0 pol d"
        tag_082 = "947.53/092"
        cuttering_fields = {"100": "Łąd, Zdzichu", "245": "Ówczesny twór"}
        subject_fields = {"600": "Żeglarz, Mietek"}
        order_data = bibs.BibOrderMeta(
            system="BPL", dstLibrary="branches", locs="41awl"
        )
        callnum = create_bpl_callnum(
            self.leader_string,
            self.tag_008,
            tag_082,
            self.tag_300a,
            cuttering_fields,
            subject_fields,
            order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aPOL$a947.5309$aL")


if __name__ == "__main__":
    unittest.main()
