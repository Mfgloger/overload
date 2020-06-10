# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field


from context import patches


class TestBibsPatches(unittest.TestCase):
    def test_nypl_branch_BT_SERIES_exception(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "J B EDISON C"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)
        with self.assertRaises(AssertionError):
            patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)

    def test_nypl_branch_BT_SERIES_JE_call_patch(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "J E VAMPIRINA"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)
        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)

        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "a", "E", "c", "VAMPIRINA"]
        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_juvenile_pic_compound_name(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091", indicators=[" ", " "], subfields=["a", "J E COMPOUND NAME"]
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "a", "E", "c", "COMPOUND NAME"]
        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_Spanish_prefix(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "J SPA E COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J SPA", "a", "E", "c", "COMPOUND NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_juvenile_fiction(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "J FIC NAME"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "a", "FIC", "c", "NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_juvenile_fic_compound_name(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091", indicators=[" ", " "], subfields=["a", "J FIC COMPOUND NAME"]
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "a", "FIC", "c", "COMPOUND NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_picture_book(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "J PIC NAME"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "a", "PIC", "c", "NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branches_BT_SERIES_picture_book_compound_name(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091", indicators=[" ", " "], subfields=["a", "J PIC COMPOUND NAME"]
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "a", "PIC", "c", "COMPOUND NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branches_BT_SERIES_Spanish_picture_book(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "J SPA PIC NAME"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J SPA", "a", "PIC", "c", "NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_young_reader(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "J YR FIC NAME"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "f", "YR", "a", "FIC", "c", "NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branch_BT_SERIES_young_reader_compound_name(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "J YR FIC COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["p", "J", "f", "YR", "a", "FIC", "c", "COMPOUND NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_fiction(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(tag="091", indicators=[" ", " "], subfields=["a", "FIC NAME"])
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["a", "FIC", "c", "NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_fiction_compound_name(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091", indicators=[" ", " "], subfields=["a", "FIC COMPOUND NAME"]
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["a", "FIC", "c", "COMPOUND NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_graphic_novel(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091", indicators=[" ", " "], subfields=["a", "GRAPHIC GN FIC NAME"]
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["f", "GRAPHIC", "a", "GN FIC", "c", "NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_graphic_novel_compound_name(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "GRAPHIC GN FIC COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "BT SERIES", bib)
        correct_indicators = [" ", " "]
        correct_subfields = ["f", "GRAPHIC", "a", "GN FIC", "c", "COMPOUND NAME"]

        self.assertEqual(correct_indicators, mod_bib.get_fields("091")[0].indicators)
        self.assertEqual(correct_subfields, mod_bib.get_fields("091")[0].subfields)


class TestRemovingOCLCPrefix(unittest.TestCase):
    def test_remove_oclc_prefix_when_no_001_tag(self):
        changed, newControlNo = patches.remove_oclc_prefix(None)
        self.assertFalse(changed)
        self.assertIsNone(newControlNo)

    def test_remove_oclc_prefix_ocm(self):
        controlNo = "ocm00000001"
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertTrue(changed)
        self.assertEqual(newControlNo, "00000001")

    def test_remove_oclc_prefix_ocn(self):
        controlNo = "ocn000000001"
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertTrue(changed)
        self.assertEqual(newControlNo, "000000001")

    def test_remove_oclc_prefix_on(self):
        controlNo = "on0000000001"
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertTrue(changed)
        self.assertEqual(newControlNo, "0000000001")

    def test_remove_oclc_prefix_not_applicable(self):
        controlNo = "0000000001"
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertFalse(changed)
        self.assertEqual(newControlNo, "0000000001")

    def test_bib_with_removed_oclc_prefix_on(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="on000000001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "GRAPHIC GN FIC COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "Amalivre", bib)

        self.assertEqual(mod_bib.get_fields("001")[0].data, "000000001")

    def test_bib_with_removed_oclc_prefix_ocn(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="ocn00000001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "GRAPHIC GN FIC COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "Amalivre", bib)

        self.assertEqual(mod_bib.get_fields("001")[0].data, "00000001")

    def test_bib_with_removed_oclc_prefix_ocm(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="ocm00000001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "GRAPHIC GN FIC COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "research", "cat", "Amalivre", bib)

        self.assertEqual(mod_bib.get_fields("001")[0].data, "00000001")

    def test_bib_no_oclc_prefix(self):
        bib = Record()
        bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="bl00000001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        tags.append(
            Field(
                tag="091",
                indicators=[" ", " "],
                subfields=["a", "GRAPHIC GN FIC COMPOUND NAME"],
            )
        )
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches("nypl", "branches", "cat", "Amalivre", bib)

        self.assertEqual(mod_bib.get_fields("001")[0].data, "bl00000001")

    # def test_bib_no_control_tag(self):
    #     bib = Record()
    #     bib.leader = '00000nam a2200000u  4500'
    #     tags = []
    #     tags.append(
    #         Field(tag='245',
    #               indicators=['0', '0'],
    #               subfields=['a', 'Test title']))
    #     tags.append(
    #         Field(tag='091',
    #               indicators=[' ', ' '],
    #               subfields=['a', 'GRAPHIC GN FIC COMPOUND NAME']))
    #     for tag in tags:
    #         bib.add_ordered_field(tag)

    #     self.assertIsNone(patches.bib_patches(
    #         'nypl', 'branches', 'cat', 'Amalivre', bib))


class TestRemoveUnsupportedSubjectHeadings(unittest.TestCase):
    """Tests removal from bib unwanted subject headings"""

    def setUp(self):
        self.bib = Record()
        self.bib.leader = "00000nam a2200000u  4500"
        tags = []
        tags.append(Field(tag="001", data="0001"))
        tags.append(
            Field(tag="245", indicators=["0", "0"], subfields=["a", "Test title"])
        )
        for tag in tags:
            self.bib.add_ordered_field(tag)

    def test_None(self):
        self.assertIsNone(patches.remove_unsupported_subject_headings("NYPL", None))

    def test_removal_of_local_subject_fields(self):
        tags = []
        tags.append(Field(tag="650", indicators=["0", "0"], subfields=["a", "term"]))
        tags.append(Field(tag="653", indicators=[" ", " "], subfields=["a", "term"]))
        tags.append(Field(tag="654", indicators=[" ", " "], subfields=["a", "term"]))
        tags.append(Field(tag="690", indicators=[" ", " "], subfields=["a", "term"]))
        tags.append(Field(tag="691", indicators=[" ", " "], subfields=["a", "term"]))
        tags.append(Field(tag="696", indicators=[" ", " "], subfields=["a", "term"]))
        tags.append(Field(tag="697", indicators=[" ", " "], subfields=["a", "term"]))
        tags.append(Field(tag="699", indicators=[" ", " "], subfields=["a", "term"]))
        for tag in tags:
            self.bib.add_ordered_field(tag)

        patches.remove_unsupported_subject_headings("NYPL", self.bib)
        self.assertTrue("650" in self.bib)
        self.assertFalse("653" in self.bib)
        self.assertFalse("654" in self.bib)
        self.assertFalse("690" in self.bib)
        self.assertFalse("691" in self.bib)
        self.assertFalse("696" in self.bib)
        self.assertFalse("697" in self.bib)
        self.assertFalse("698" in self.bib)
        self.assertFalse("699" in self.bib)

    def test_preserve_lc_subjects(self):
        tags = []
        tags.append(
            Field(tag="600", indicators=["0", "0"], subfields=["a", "Smith, John"])
        )
        tags.append(Field(tag="610", indicators=["2", "0"], subfields=["a", "Inc."]))
        tags.append(Field(tag="611", indicators=[" ", "0"], subfields=["a", "Event"]))
        tags.append(Field(tag="630", indicators=[" ", "0"], subfields=["a", "Title"]))
        tags.append(Field(tag="650", indicators=[" ", "0"], subfields=["a", "Subject"]))
        tags.append(Field(tag="655", indicators=[" ", "0"], subfields=["a", "Genre"]))
        for tag in tags:
            self.bib.add_ordered_field(tag)

        patches.remove_unsupported_subject_headings("BPL", self.bib)

        self.assertTrue("600" in self.bib)
        self.assertTrue("610" in self.bib)
        self.assertTrue("611" in self.bib)
        self.assertTrue("630" in self.bib)
        self.assertTrue("650" in self.bib)
        self.assertTrue("655" in self.bib)

    def test_preserve_specific_vocabularies(self):
        tags = []
        tags.append(
            Field(
                tag="600", indicators=[" ", "7"], subfields=["a", "Genre", "2", "fast"]
            )
        )
        tags.append(
            Field(
                tag="630", indicators=[" ", "1"], subfields=["a", "Children's subject"]
            )
        )
        tags.append(
            Field(
                tag="650", indicators=[" ", "7"], subfields=["a", "Genre", "2", "gsafd"]
            )
        )
        tags.append(
            Field(
                tag="651", indicators=[" ", "7"], subfields=["a", "Genre", "2", "lcgft"]
            )
        )
        tags.append(
            Field(
                tag="655", indicators=[" ", "7"], subfields=["a", "Genre", "2", "gmgpc"]
            )
        )
        for tag in tags:
            self.bib.add_ordered_field(tag)

        patches.remove_unsupported_subject_headings("NYPL", self.bib)

        self.assertTrue("600" in self.bib)
        self.assertTrue("630" in self.bib)
        self.assertTrue("650" in self.bib)
        self.assertTrue("651" in self.bib)
        self.assertTrue("655" in self.bib)

    def test_removal_of_unsupported_vocabularies_nypl(self):
        tags = []
        tags.append(
            Field(tag="600", indicators=["0", "7"], subfields=["a", "Smith, John"])
        )
        tags.append(
            Field(
                tag="610", indicators=["2", "7"], subfields=["a", "Inc.", "2", "biasac"]
            )
        )
        tags.append(Field(tag="650", indicators=[" ", "4"], subfields=["a", "Event"]))
        tags.append(
            Field(
                tag="630",
                indicators=[" ", "7"],
                subfields=["a", "Title", "2", "rbgenr"],
            )
        )
        tags.append(
            Field(
                tag="655", indicators=[" ", "7"], subfields=["a", "Genre", "2", "att"]
            )
        )
        for tag in tags:
            self.bib.add_ordered_field(tag)

        patches.remove_unsupported_subject_headings("NYPL", self.bib)

        self.assertFalse("600" in self.bib)
        self.assertFalse("610" in self.bib)
        self.assertFalse("650" in self.bib)
        self.assertFalse("630" in self.bib)
        self.assertFalse("655" in self.bib)

    def test_removal_of_unsupported_vocabularies_bpl(self):
        tags = []
        tags.append(
            Field(tag="600", indicators=["0", "7"], subfields=["a", "Smith, John"])
        )
        tags.append(
            Field(
                tag="610", indicators=["2", "7"], subfields=["a", "Inc.", "2", "biasac"]
            )
        )
        tags.append(Field(tag="650", indicators=[" ", "4"], subfields=["a", "Event"]))
        tags.append(
            Field(
                tag="630",
                indicators=[" ", "7"],
                subfields=["a", "Title", "2", "rbgenr"],
            )
        )
        tags.append(
            Field(tag="650", indicators=[" ", "1"], subfields=["a", "Children's"])
        )
        tags.append(
            Field(
                tag="655", indicators=[" ", "7"], subfields=["a", "Genre", "2", "att"]
            )
        )
        for tag in tags:
            self.bib.add_ordered_field(tag)

        patches.remove_unsupported_subject_headings("BPL", self.bib)

        self.assertFalse("600" in self.bib)
        self.assertFalse("610" in self.bib)
        self.assertFalse("630" in self.bib)
        self.assertFalse("650" in self.bib)
        self.assertFalse("655" in self.bib)


if __name__ == "__main__":
    unittest.main()
