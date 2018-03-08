# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field, MARCReader, JSONReader
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


    # def test_writing_marc_bibs_with_pymarc(self):
    #     bibs.write_bib(self.fh_out, self.marc_bib)
    #     contents = open(self.fh_out).read()
    #     self.assertEqual(
    #         contents,
    #         u'00089nam a2200049u  45000010024000002450015000240001-test-control_field00aTest title')

    # def test_read_from_marc_file_returns_pymarc_reader(self):
    #     # should return an instance of pymarc reader
    #     bibs.write_bib(self.fh_out, self.marc_bib)
    #     reader = bibs.read_from_marc_file(self.fh_out)
    #     self.assertIs(type(reader), MARCReader)

    # def test_read_from_json_retuns_pymarc_reader(self):
    #     reader = JSONReader('test.json')
    #     self.assertIs(type(reader), JSONReader)

    # def test_read_from_marc_IO_returns_pymarc_reader(self):
    #     bibs.write_bib(self.fh_out, self.marc_bib)
    #     reader = MARCReader(self.fh_out)
    #     self.assertIs(type(reader), MARCReader)

    # def test_meta_from_marc(self):
    #     # WIP
    #     pass

    # def test_meta_from_json(self):
    #     # WIP
    #     pass

    # def test_api_results_parser(self):
    #     # WIP
    #     self.assertIs(type(bibs.api_results_parser(None)), list)

    # def test_create_target_id_field(self):
    #     id = '11648181'
    #     for lib in ['BPL', 'NYPL']:
    #         field = bibs.create_target_id_field(lib, id)
    #         self.assertIs(type(field), Field)

    #         if lib == 'BPL':
    #             self.assertEqual(field.tag, '907')
    #         else:
    #             self.assertEqual(field.tag, '945')

    #         self.assertEqual(field.indicators, [' ', ' '])
    #         self.assertEqual(field['a'], '.b{}a'.format(id))

    # def test_create_sierra_format_field(self):
    #     field = bibs.create_sierra_format_field('a')
    #     self.assertIs(type(field), Field)
    #     self.assertEqual(field.tag, '949')
    #     self.assertEqual(field.indicators, [' ', ' '])
    #     self.assertEqual(field['a'], '*b2=a;')

    # def test_count_bibs(self):
        # self.assertEqual(bibs.count_bibs('test.mrc'), 5)


if __name__ == '__main__':
    unittest.main()
