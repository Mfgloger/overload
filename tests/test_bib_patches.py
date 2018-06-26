# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field


from context import patches


class TestBibsPatches(unittest.TestCase):
    def setUp(self):
        # Test MARC record
        self.bib1 = Record()
        self.bib1.leader = '00000nam a2200000u  4500'
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
            self.bib1.add_ordered_field(tag)

    def test_nypl_branch_BT_SERIES_patch(self):
        bib = patches.patches(
            'nypl', 'branches', 'cat', 'BT SERIES', self.bib1)
        self.assertEqual(
            bib.get_fields('091')[0].value(),
            'J E VAMPIRINA')


if __name__ == '__main__':
    unittest.main()