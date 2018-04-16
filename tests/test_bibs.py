# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field, MARCReader, JSONReader
from pymarc.exceptions import RecordLengthInvalid
import os

from context import bibs


class TestUtils(unittest.TestCase):
    """Test utilities functions used in Overload"""

    def test_parse_isbn_10_digits_only(self):
        self.assertIsNotNone(bibs.parse_isbn('83-922033-1-3'))

    def test_parse_isbn_13_digit_only(self):
        self.assertIsNotNone(bibs.parse_isbn('9788374147323'))

    def test_parse_isbn_10_digit_x(self):
        self.assertIsNotNone(bibs.parse_isbn('061543326X'))

    def test_parse_isbn_13_digit_x(self):
        self.assertIsNotNone(bibs.parse_isbn('978141049620x (hardcover)'))

    # def test_parse_incorrect_isbn(self):
    #     # make corrections to isbn parser
    #     self.assertIsNone(bibs.parse_isbn(
    #         '5060099503825'),
    #         msg='isbn parser should be able to recognize'
                # ' identificators that are not ISBNs')


class TestParseUPC(unittest.TestCase):
    """Test parsing identifier found in 024$a MARC fieled"""

    def test_parsing_good_UPC(self):
        self.assertEqual(
            bibs.parse_upc('6706878182'),
            '6706878182')

    def test_parsing_UPC_with_price(self):
        self.assertEqual(
            bibs.parse_upc('8616227633 : $19.98'),
            '8616227633')

    def test_parsing_alphanumberic_UPC(self):
        self.assertEqual(
            bibs.parse_upc('M215104174'),
            'M215104174')


class TestParseISSN(unittest.TestCase):
    """Test parsing ISSN found in 022$a MARC fieled"""

    def test_parsing_good_digit_only_ISSN(self):
        self.assertEqual(
            bibs.parse_issn('0378-5955'),
            '0378-5955')

    def test_parsing_good_digit_x_ISSN(self):
        self.assertEqual(
            bibs.parse_issn('2434-561X'),
            '2434-561X')

    def test_parsing_incorrect_ISSN(self):
        self.assertIsNone(
            bibs.parse_issn('M215104174'))


class TestParseSierraID(unittest.TestCase):
    """Test parsing Sierra bib and order id numbers"""

    def test_bib_number_parsing(self):
        self.assertIsNotNone(bibs.parse_sierra_id('.b119629811'))

    def test_order_number_parsing(self):
        self.assertIsNotNone(bibs.parse_sierra_id('.o16799069'))

    def test_wrong_id_number_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id('349876789087'))


class TestBibsUtilities(unittest.TestCase):
    """
    Tests utitlities in the bibs module responsible for reading
    and writing MARC records in various formats
    """

    def setUp(self):
        """
        create record in MARC21 format and other to simulate
        operations on them
        """
        # Test MARC record
        self.marc_bib = Record()
        self.marc_bib.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='0001-test-control_field'))
        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))
        for tag in tags:
            self.marc_bib.add_ordered_field(tag)

        # temp file
        self.fh_out = 'MARCtest.mrc'

    def tearDown(self):
        self.marc_bib = None
        try:
            os.remove(self.fh_out)
        except OSError:
            pass

    def test_write_marc21(self):
        bibs.write_marc21(self.fh_out, self.marc_bib)
        contents = open(self.fh_out).read()
        self.assertEqual(
            contents,
            u'00089nam a2200049u  45000010024000002450015000240001-test-control_field00aTest title')

    def test_read_marc21_returns_pymarc_reader(self):
        # should return an instance of pymarc reader
        reader = bibs.read_marc21('test.mrc')
        self.assertIs(type(reader), MARCReader)

    def test_count_bibs_when_not_marc_file(self):
        with self.assertRaises(RecordLengthInvalid):
            reader = bibs.count_bibs('test.json')

    def test_read_from_json_retuns_pymarc_reader(self):
        reader = JSONReader('test.json')
        self.assertIs(type(reader), JSONReader)

    def test_create_target_id_field_exceptions(self):
        with self.assertRaises(ValueError):
            bibs.create_target_id_field('nypl', '012345')

    def test_create_target_id_field_returns_instance_of_pymarc_Field(self):
        self.assertIsInstance(
            bibs.create_target_id_field('nypl', '01234567'),
            Field)

    def test_create_target_id_field_returns_correct_field_values(self):
        self.assertEqual(
            bibs.create_target_id_field('bpl', '01234567').tag,
            '907')
        self.assertEqual(
            bibs.create_target_id_field('bpl', '01234567').indicators,
            [' ', ' '])
        self.assertEqual(
            bibs.create_target_id_field('bpl', '01234567').subfields,
            ['a', '.b01234567a'])
        self.assertEqual(
            bibs.create_target_id_field('nypl', '01234567').tag,
            '945')
        self.assertEqual(
            bibs.create_target_id_field('nypl', '01234567').indicators,
            [' ', ' '])
        self.assertEqual(
            bibs.create_target_id_field('nypl', '01234567').subfields,
            ['a', '.b01234567a'])

    def test_check_sierra_id_presence(self):
        self.assertFalse(
            bibs.check_sierra_id_presence('nypl', self.marc_bib))
        self.assertFalse(
            bibs.check_sierra_id_presence('bpl', self.marc_bib))
        # add 945
        self.marc_bib.add_field(
            Field(
                tag='945',
                indicators=[' ', ' '],
                subfields=['a', '.b01234567a']))
        self.assertTrue(
            bibs.check_sierra_id_presence('nypl', self.marc_bib))
        self.marc_bib.add_field(
            Field(
                tag='907',
                indicators=[' ', ' '],
                subfields=['a', '.b01234567a']))
        self.assertTrue(
            bibs.check_sierra_id_presence('bpl', self.marc_bib))

    def test_check_sierra_format_tag_presence_False(self):
        self.assertFalse(
            bibs.check_sierra_format_tag_presence(self.marc_bib))
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=['a', "*b2=a;"]))
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['b', "*b2=a;"]))
        self.assertFalse(
            bibs.check_sierra_format_tag_presence(self.marc_bib))

    def test_check_sierra_format_tag_presence_True(self):
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', "*b2=a;"]))
        self.assertTrue(
            bibs.check_sierra_format_tag_presence(self.marc_bib))

    def test_check_sierra_format_tag_presence_exception(self):
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', '']))
        with self.assertRaises(IndexError):
            bibs.check_sierra_format_tag_presence(self.marc_bib)

    def test_bibmeta_object(self):
        meta = bibs.BibMeta(self.marc_bib, sierraId='12345678')
        self.assertIsInstance(meta, bibs.BibMeta)
        self.assertEqual(meta.t001, '0001-test-control_field')
        self.assertIsNone(meta.t005)
        self.assertEqual(meta.t020, [])
        self.assertEqual(meta.t022, [])
        self.assertEqual(meta.t024, [])
        self.assertEqual(meta.t028, [])
        self.assertEqual(meta.sierraId, '12345678')
        self.assertIsNone(meta.bCallNumber)
        self.assertEqual(meta.rCallNumber, [])

    def test_vendor_bibmeta_object(self):
        meta = bibs.VendorBibMeta(
            self.marc_bib, vendor='Amalivre', dstLibrary='rl')
        self.assertIsInstance(meta, bibs.VendorBibMeta)
        self.assertEqual(meta.t001, '0001-test-control_field')
        self.assertIsNone(meta.t005)
        self.assertEqual(meta.t020, [])
        self.assertEqual(meta.t022, [])
        self.assertEqual(meta.t024, [])
        self.assertEqual(meta.t028, [])
        self.assertIsNone(meta.bCallNumber)
        self.assertEqual(meta.rCallNumber, [])
        self.assertEqual(meta.vendor, 'Amalivre')
        self.assertEqual(meta.dstLibrary, 'rl')

    def test_vendor_bibmeta_object_when_sierra_id_is_provided(self):
        # nypl scenario
        self.marc_bib.add_field(
            Field(
                tag='945',
                indicators=[' ', ' '],
                subfields=['a', '.b01234567a']))
        meta = bibs.VendorBibMeta(self.marc_bib, vendor='BTODC', dstLibrary='branches')
        self.assertEqual(meta.sierraId, '01234567')
        # bpl scencario
        self.marc_bib.remove_fields('945')
        self.marc_bib.add_field(
            Field(
                tag='907',
                indicators=[' ', ' '],
                subfields=['a', '.b01234568a']))
        meta = bibs.VendorBibMeta(self.marc_bib, vendor='BTCLS', dstLibrary='branches')
        self.assertEqual(meta.sierraId, '01234568')


if __name__ == '__main__':
    unittest.main()
