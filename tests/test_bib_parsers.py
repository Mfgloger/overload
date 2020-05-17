# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field, MARCReader, JSONReader

from context import bibs, parsers


class TestUtils(unittest.TestCase):
    """Test utilities functions used in Overload"""

    def test_parse_isbn_10_digits_only(self):
        self.assertIsNotNone(parsers.parse_isbn("83-922033-1-3"))

    def test_parse_isbn_13_digit_only(self):
        self.assertIsNotNone(parsers.parse_isbn("9788374147323"))

    def test_parse_isbn_10_digit_x(self):
        self.assertIsNotNone(parsers.parse_isbn("061543326X"))

    def test_parse_isbn_13_digit_x(self):
        self.assertIsNotNone(parsers.parse_isbn("978141049620x (hardcover)"))

    # def test_parse_incorrect_isbn(self):
    #     # make corrections to isbn parser
    #     self.assertIsNone(parsers.parse_isbn(
    #         '5060099503825'),
    #         msg='isbn parser should be able to recognize'
    #             ' identificators that are not ISBNs')


class TestParseUPC(unittest.TestCase):
    """Test parsing identifier found in 024$a MARC fieled"""

    def test_parsing_good_UPC(self):
        self.assertEqual(parsers.parse_upc("6706878182"), "6706878182")

    def test_parsing_UPC_with_price(self):
        self.assertEqual(parsers.parse_upc("8616227633 : $19.98"), "8616227633")

    def test_parsing_alphanumberic_UPC(self):
        self.assertEqual(parsers.parse_upc("M215104174"), "M215104174")


class TestParseISSN(unittest.TestCase):
    """Test parsing ISSN found in 022$a MARC fieled"""

    def test_parsing_good_digit_only_ISSN(self):
        self.assertEqual(parsers.parse_issn("0378-5955"), "03785955")

    def test_parsing_good_digit_x_ISSN(self):
        self.assertEqual(parsers.parse_issn("2434-561X"), "2434561X")

    def test_parsing_incorrect_ISSN(self):
        self.assertIsNone(parsers.parse_issn("M215104174"))


class TestParseSierraID(unittest.TestCase):
    """Test parsing Sierra bib and order id numbers"""

    def test_bib_number_parsing(self):
        self.assertIsNotNone(bibs.parse_sierra_id(".b119629811"))
        self.assertEqual(bibs.parse_sierra_id(".b119629811"), "11962981")

    def test_order_number_parsing(self):
        self.assertIsNotNone(bibs.parse_sierra_id(".o16799069"))
        self.assertEqual(bibs.parse_sierra_id(".o16799069"), "1679906")

    def test_wrong_id_number_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id("349876789087"))

    def test_None_id_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id(None))

    def test_empty_string_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id(""))


class TestExtractRecordEncoding(unittest.TestCase):
    """Test parsing MARC21 leader record character endcoding"""

    def test_leader_string_is_none(self):
        self.assertIsNone(parsers.extract_record_encoding())

    def test_leader_utf8_endcoding(self):
        leader = "01451nam a2200397 i 4500"
        self.assertEqual(parsers.extract_record_encoding(leader), "a")

    def test_leader_marc8_encodign(self):
        leader = "01451nam  2200397 i 4500"
        self.assertEqual(parsers.extract_record_encoding(leader), " ")


class TestExtractRecordLvl(unittest.TestCase):
    """Test parsing MARC21 leader record fullness level"""

    def test_leader_string_is_none(self):
        self.assertIsNone(parsers.extract_record_lvl())

    def test_leader_full_lvl(self):
        leader = "01451nam  2200397 i 4500"
        self.assertEqual(parsers.extract_record_lvl(leader), " ")

    def test_leader_abbreviated_lvl(self):
        leader = "01451nam  22003973i 4500"
        self.assertEqual(parsers.extract_record_lvl(leader), "3")


class TestExtractRecordType(unittest.TestCase):
    """Test parsing MARC21 leader to determine record type used"""

    def test_leader_string_is_none(self):
        self.assertIsNone(parsers.extract_record_type())

    def test_leader_record_type_is_lang_material(self):
        leader = "01451nam  2200397 i 4500"
        self.assertEqual(parsers.extract_record_type(leader), "a")

    def test_leader_record_type_is_projected_medium(self):
        leader = "01451ngm  22003973i 4500"
        self.assertEqual(parsers.extract_record_type(leader), "g")


class TestExtractAudienceCode(unittest.TestCase):
    """Tests extraction of audience code based on leader and 008 tag"""

    def test_no_record_leader(self):
        leader = None
        t008 = r"190911s2019\\\\caua\\\\\\\\\\000\1\eng\d"
        self.assertIsNone(parsers.get_audience_code(leader, t008))

    def test_no_008_tag(self):
        leader = "01451nam  2200397 i 4500"
        t008 = None
        self.assertIsNone(parsers.get_audience_code(leader, t008))

    def test_audn_code_for_lang_material(self):
        leader = "01451nam  2200397 i 4500"
        t008 = r"190911s2019    caua          000 1 eng d"
        self.assertEqual(parsers.get_audience_code(leader, t008), " ")

    def test_audn_code_for_projected_medium(self):
        leader = "01451ngm  22003973i 4500"
        t008 = r"190916p20192018xxu156            vleng d"
        self.assertIsNone(parsers.get_audience_code(leader, t008))


class TestGetLanguageCode(unittest.TestCase):
    """Tests extraction of language code from 008 tag"""

    def test_no_008_tag(self):
        self.assertIsNone(parsers.get_language_code(None))


class TestParseLangPrefix(unittest.TestCase):
    """Test parsing tag 008 language code"""

    def test_tag_008_is_none(self):
        pass


if __name__ == "__main__":
    unittest.main()
