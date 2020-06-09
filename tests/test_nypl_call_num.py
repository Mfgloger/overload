# -*- coding: utf-8 -*-

import unittest


from context import bibs, create_nypl_callnum


class TestCreateNYPLFictionCallNum(unittest.TestCase):
    """Test creation of NYPL fiction and picture book call numbers"""

    def setUp(self):
        self.leader_string = "00000cam a2200000Ia 4500"
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        self.tag_082 = "941.540/09"
        self.tag_300a = "1 volume (various pagings)"
        self.cuttering_fields = {"100": "Smith, John", "245": "Test title"}
        self.subject_fields = {"600": "Doe, Jane"}
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="bga0f"
        )

    def test_english_adult_fiction(self):
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aFIC$cSMITH")

    def test_world_lang_adult_fiction_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 1 pol d"
        self.cuttering_fields = {
            "100": "Łąd, Zdzichu",
            "245": "Ówczesny twór",
        }
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="bga0l"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pPOL$aFIC$cLAD")

    def test_world_lang_picture_book_with_order_data_diacritics(self):
        self.tag_008 = "961120s1988    nyu    j      000 1 pol d"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="bgj0l"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            self.tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pJ POL$aPIC$cSMITH")

    def test_world_lang_juv_fiction_with_order_data(self):
        self.tag_008 = "961120s1988    nyu    j      000 1 spa d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="agj0l,baj0l"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pJ SPA$aFIC$cSMITH")

    def test_english_young_reader_with_order_data(self):
        self.tag_008 = "961120s1988    nyu    j      000 1 eng d"
        tag_300a = "200 pages"
        cuttering_fields = {"100": "Smith-Johns, John", "245": "Test title"}
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="agj0y,baj0y", venNote="YR"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pJ$fYR$aFIC$cSMITH JOHNS")

    def test_english_juv_graphic_novel_with_order_data(self):
        self.tag_008 = "961120s1988    nyu    j      000 1 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="agj0f", venNote="g"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pJ$fGRAPHIC$aGN FIC$cSMITH")

    def test_english_adult_mystery_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0f", venNote="m"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aMYSTERY$cSMITH")

    def test_english_adult_science_fiction_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0f", venNote="s"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aSCI FI$cSMITH")

    def test_english_adult_romance_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0f", venNote="r"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aROMANCE$cSMITH")

    def test_english_adult_western_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0f", venNote="w"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aWESTERN$cSMITH")

    def test_english_adult_urban_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0f", venNote="n,u"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aURBAN$cSMITH")

    def test_english_adult_biography_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 0beng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0n", venNote="bio"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$aB$bDOE$cS")

    def test_english_juv_biography_with_order_data(self):
        self.tag_008 = "961120s1988    nyu    j      000 0beng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="agj0n", venNote="bio"
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pJ$aB$bDOE$cS")

    def test_english_adult_dewey_with_order_data(self):
        self.tag_008 = "961120s1988    nyu           000 0 eng d"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="aga0n", venNote=""
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$a941.54$cS")

    def test_english_juvenile_dewey_with_order_data(self):
        self.tag_008 = "961120s1988    nyu    j      000 0 eng d"
        tag_082 = "941.5136"
        tag_300a = "200 pages"
        self.order_data = bibs.BibOrderMeta(
            system="NYPL", dstLibrary="branches", locs="agj0n", venNote=""
        )
        callnum = create_nypl_callnum(
            self.leader_string,
            self.tag_008,
            tag_082,
            tag_300a,
            self.cuttering_fields,
            self.subject_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=091  \\\\$pJ$a941.51$cS")


if __name__ == "__main__":
    unittest.main()
