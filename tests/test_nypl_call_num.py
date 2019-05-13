# -*- coding: utf-8 -*-

import unittest


from context import bibs, create_nypl_fiction_callnum


class TestCreateNYPLFictionCallNum(unittest.TestCase):
    """Test creation of NYPL fiction and picture book call numbers"""

    def setUp(self):
        self.leader_string = '00000cam a2200000Ia 4500'
        self.tag_008 = '961120s1988    nyu           000 1 eng d'
        self.tag_300a = '1 volume (various pagings)'
        self.cuttering_fields = {'100': 'Smith, John', '245': 'Test title'}
        self.order_data = bibs.BibOrderMeta(system='NYPL', dstLibrary='branches')

    def test_english_adult_fiction(self):
        callnum = create_nypl_fiction_callnum(
            self.leader_string, self.tag_008, self.tag_300a,
            self.cuttering_fields, self.order_data)
        self.assertEqual(str(callnum), '=091  \\\\$aFIC$cSMITH')

    def test_world_lang_adult_fiction_no_order_data(self):
        self.tag_008 = '961120s1988    nyu           000 0 spa d'
        callnum = create_nypl_fiction_callnum(
            self.leader_string, self.tag_008, self.tag_300a,
            self.cuttering_fields, self.order_data)
        self.assertEqual(str(callnum), '=091  \\\\$pSPA$aFIC$cSMITH')

    def test_world_lang_picture_book_no_order_data(self):
        self.tag_008 = '961120s1988    nyu    j      000 0 spa d'
        callnum = create_nypl_fiction_callnum(
            self.leader_string, self.tag_008, self.tag_300a,
            self.cuttering_fields, self.order_data)
        self.assertEqual(str(callnum), '=091  \\\\$pJ SPA$aPIC$cSMITH')

    def test_world_lang_adult_fiction_with_order_data(self):
        self.tag_008 = '961120s1988    nyu           000 1 spa d'
        self.order_data = bibs.BibOrderMeta(
            system='NYPL', dstLibrary='branches',
            locs='aga0l,baa0l')
        callnum = create_nypl_fiction_callnum(
            self.leader_string, self.tag_008, self.tag_300a,
            self.cuttering_fields, self.order_data)
        self.assertEqual(str(callnum), '=091  \\\\$pSPA$aFIC$cSMITH')

    def test_english_juvenile_fiction_with_order_data(self):
        self.tag_008 = '961120s1988    nyu    j      000 0 spa d'
        self.order_data = bibs.BibOrderMeta(
            system='NYPL', dstLibrary='branches',
            locs='agj0f,baj0f')
        callnum = create_nypl_fiction_callnum(
            self.leader_string, self.tag_008, self.tag_300a,
            self.cuttering_fields, self.order_data)
        self.assertEqual(str(callnum), '=091  \\\\$pJ$aFIC$cSMITH')


if __name__ == '__main__':
    unittest.main()

