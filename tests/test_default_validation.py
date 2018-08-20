# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field
import os


from context import default
from context import bibs


class TestDefaultValidation(unittest.TestCase):
    """
    Tests default, mandatory validation of each batch of records
    """

    def setUp(self):
        self.fh1 = 'barcode1_dup_test.mrc'
        self.fh2 = 'barcode2_dup_test.mrc'

    def tearDown(self):
        try:
            os.remove(self.fh1)
            os.remove(self.fh2)
        except:
            pass

    def test_barcodes_duplicates_in_two_nypl_files(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000003'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title 1']))
        tags.append(
            Field(tag='949',
                  indicators=[' ', '1'],
                  subfields=['i', '33333849044539',
                             'l', 'moa0f',
                             'p', '14.95',
                             't', '102',
                             'v', 'BTURBN']))
        for tag in tags:
            bib.add_ordered_field(tag)

        bibs.write_marc21(self.fh1, bib)

        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title 1']))
        tags.append(
            Field(tag='949',
                  indicators=[' ', '1'],
                  subfields=['i', '33333849044538',
                             'l', 'moa0f',
                             'p', '14.95',
                             't', '102',
                             'v', 'BTURBN']))
        for tag in tags:
            bib.add_ordered_field(tag)

        bibs.write_marc21(self.fh1, bib)

        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title 1']))
        tags.append(
            Field(tag='949',
                  indicators=[' ', '1'],
                  subfields=['i', '33333849044538',
                             'l', 'moa0f',
                             'p', '14.95',
                             't', '102',
                             'v', 'BTURBN']))
        for tag in tags:
            bib.add_ordered_field(tag)

        bibs.write_marc21(self.fh2, bib)

        self.assertEqual(
            default.barcode_duplicates([self.fh1, self.fh2], 'nypl'),
            {u'33333849044538': [('barcode1_dup_test.mrc', 2), ('barcode2_dup_test.mrc', 1)]})

    def test_barcodes_duplicates_in_two_bpl_files(self):
        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000003'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title 1']))
        tags.append(
            Field(tag='960',
                  indicators=[' ', ' '],
                  subfields=['i', '34444849044539',
                             'l', '14afc',
                             'p', '14.95',
                             't', '100',
                             'v', 'BTURBN']))
        for tag in tags:
            bib.add_ordered_field(tag)

        bibs.write_marc21(self.fh1, bib)

        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title 1']))
        tags.append(
            Field(tag='960',
                  indicators=[' ', ' '],
                  subfields=['i', '34444849044538',
                             'l', '14afc',
                             'p', '14.95',
                             't', '100',
                             'v', 'BTURBN']))
        for tag in tags:
            bib.add_ordered_field(tag)

        bibs.write_marc21(self.fh1, bib)

        bib = Record()
        bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='ocm00000001'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title 1']))
        tags.append(
            Field(tag='960',
                  indicators=[' ', ' '],
                  subfields=['i', '34444849044538',
                             'l', '14afc',
                             'p', '14.95',
                             't', '100',
                             'v', 'BTURBN']))
        for tag in tags:
            bib.add_ordered_field(tag)

        bibs.write_marc21(self.fh2, bib)

        self.assertEqual(
            default.barcode_duplicates([self.fh1, self.fh2], 'bpl'),
            {u'34444849044538': [('barcode1_dup_test.mrc', 2), ('barcode2_dup_test.mrc', 1)]})


if __name__ == '__main__':
    unittest.main()
