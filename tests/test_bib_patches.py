# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field


from context import patches


class TestBibsPatches(unittest.TestCase):
    def test_nypl_branch_BT_SERIES_exception(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J B EDISON C']))
        for tag in tags:
            bib.add_ordered_field(tag)
        with self.assertRaises(AssertionError):
            patches.bib_patches(
                'nypl', 'branches', 'cat', 'BT SERIES', bib)

    def test_nypl_branch_BT_SERIES_JE_call_patch(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J E VAMPIRINA']))
        for tag in tags:
            bib.add_ordered_field(tag)
        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)

        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'a', 'E',
            'c', 'VAMPIRINA']
        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_juvenile_pic_compound_name(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J E COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'a', 'E',
            'c', 'COMPOUND NAME']
        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_Spanish_prefix(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J SPA E COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J SPA',
            'a', 'E',
            'c', 'COMPOUND NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_juvenile_fiction(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J FIC NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'a', 'FIC',
            'c', 'NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_juvenile_fic_compound_name(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'a', 'FIC',
            'c', 'COMPOUND NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_picture_book(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J PIC NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'a', 'PIC',
            'c', 'NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branches_BT_SERIES_picture_book_compound_name(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J PIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'a', 'PIC',
            'c', 'COMPOUND NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branches_BT_SERIES_Spanish_picture_book(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J SPA PIC NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J SPA',
            'a', 'PIC',
            'c', 'NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_young_reader(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J YR FIC NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'f', 'YR',
            'a', 'FIC',
            'c', 'NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branch_BT_SERIES_young_reader_compound_name(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'J YR FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'p', 'J',
            'f', 'YR',
            'a', 'FIC',
            'c', 'COMPOUND NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_fiction(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'FIC NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'a', 'FIC',
            'c', 'NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_fiction_compound_name(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'a', 'FIC',
            'c', 'COMPOUND NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_graphic_novel(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'GRAPHIC GN FIC NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'f', 'GRAPHIC',
            'a', 'GN FIC',
            'c', 'NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)

    def test_nypl_branches_BT_SERIES_YA_graphic_novel_compound_name(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'GRAPHIC GN FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'BT SERIES', bib)
        correct_indicators = [' ', ' ']
        correct_subfields = [
            'f', 'GRAPHIC',
            'a', 'GN FIC',
            'c', 'COMPOUND NAME']

        self.assertEqual(
            correct_indicators,
            mod_bib.get_fields('091')[0].indicators)
        self.assertEqual(
            correct_subfields,
            mod_bib.get_fields('091')[0].subfields)


class TestRemovingOCLCPrefix(unittest.TestCase):
    def test_remove_oclc_prefix_when_no_001_tag(self):
        changed, newControlNo = patches.remove_oclc_prefix(None)
        self.assertFalse(changed)
        self.assertIsNone(newControlNo)

    def test_remove_oclc_prefix_ocm(self):
        controlNo = 'ocm00000001'
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertTrue(changed)
        self.assertEqual(
            newControlNo,
            '00000001')

    def test_remove_oclc_prefix_ocn(self):
        controlNo = 'ocn000000001'
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertTrue(changed)
        self.assertEqual(
            newControlNo,
            '000000001')

    def test_remove_oclc_prefix_on(self):
        controlNo = 'on0000000001'
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertTrue(changed)
        self.assertEqual(
            newControlNo,
            '0000000001')

    def test_remove_oclc_prefix_not_applicable(self):
        controlNo = '0000000001'
        changed, newControlNo = patches.remove_oclc_prefix(controlNo)
        self.assertFalse(changed)
        self.assertEqual(
            newControlNo,
            '0000000001')

    def test_bib_with_removed_oclc_prefix_on(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='on000000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'GRAPHIC GN FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'Amalivre', bib)

        self.assertEqual(
            mod_bib.get_fields('001')[0].data,
            '000000001')

    def test_bib_with_removed_oclc_prefix_ocn(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocn00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'GRAPHIC GN FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'Amalivre', bib)

        self.assertEqual(
            mod_bib.get_fields('001')[0].data,
            '00000001')

    def test_bib_with_removed_oclc_prefix_ocm(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'GRAPHIC GN FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'research', 'cat', 'Amalivre', bib)

        self.assertEqual(
            mod_bib.get_fields('001')[0].data,
            '00000001')

    def test_bib_no_oclc_prefix(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='bl00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        tags.append(
            Field(tag='091',
                  indicators=[' ', ' '],
                  subfields=['a', 'GRAPHIC GN FIC COMPOUND NAME']))
        for tag in tags:
            bib.add_ordered_field(tag)

        mod_bib = patches.bib_patches(
            'nypl', 'branches', 'cat', 'Amalivre', bib)

        self.assertEqual(
            mod_bib.get_fields('001')[0].data,
            'bl00000001')

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



if __name__ == '__main__':
    unittest.main()