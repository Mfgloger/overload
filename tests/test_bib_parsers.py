# -*- coding: utf-8 -*-

import unittest

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

    def test_audn_code_for_print(self):
        leader = "01451nam  22003973i 4500"
        t008 = r"961120s1988    nyu    a      000 1 eng d"
        self.assertEqual(parsers.get_audience_code(leader, t008), "a")


class TestGetLanguageCode(unittest.TestCase):
    """Tests extraction of language code from 008 tag"""

    def test_no_008_tag(self):
        self.assertIsNone(parsers.get_language_code(None))


class TestHasBiographyCode(unittest.TestCase):
    """Tests if bibliographic record is coded as biography in fixed fields"""

    def test_no_leader(self):
        self.assertFalse(parsers.has_biography_code(None, None))

    def test_empty_strings(self):
        self.assertFalse(parsers.has_biography_code("", ""))

    def test_autobiography(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 0aeng d"
        self.assertTrue(parsers.has_biography_code(leader, tag_008))

    def test_biography(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 0beng d"
        self.assertTrue(parsers.has_biography_code(leader, tag_008))

    def test_partial_biography(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 0deng d"
        self.assertTrue(parsers.has_biography_code(leader, tag_008))


class TestIsBiography(unittest.TestCase):
    """Tests if overall bibliographic record qualifies as biography"""

    def test_arguments_None(self):
        self.assertFalse(parsers.is_biography(None, None, None))

    def test_empty_strings_and_dict(self):
        self.assertFalse(parsers.is_biography("", "", {}))

    def test_bib_without_600(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 0aeng d"
        self.assertFalse(parsers.is_biography(leader, tag_008, {"650": "History"}))

    def test_bib_with_600(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 0aeng d"
        self.assertTrue(parsers.is_biography(leader, tag_008, {"600": "Smith, John"}))


class TestIsDewey(unittest.TestCase):
    """Tests if bibliographic record qualifies as non-fic"""

    def test_arguments_None(self):
        self.assertFalse(parsers.is_dewey(None, None))

    def test_empty_strings(self):
        self.assertFalse(parsers.is_dewey("", ""))

    def test_tag_008_code_0(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 0 eng d"
        self.assertTrue(parsers.is_dewey(leader, tag_008))

    def test_tag_008_code_d(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 d eng d"
        self.assertTrue(parsers.is_dewey(leader, tag_008))

    def test_tag_008_code_e(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 e eng d"
        self.assertTrue(parsers.is_dewey(leader, tag_008))

    def test_tag_008_code_h(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 h eng d"
        self.assertTrue(parsers.is_dewey(leader, tag_008))

    def test_tag_008_code_i(self):
        leader = "00000cam a2200000Ia 4500"
        tag_008 = "961120s1988    nyu    a      000 i eng d"
        self.assertTrue(parsers.is_dewey(leader, tag_008))


class TestParseFirstLetter(unittest.TestCase):
    """Tests parsing of the first letter to be used for a cutter"""

    def test_empty_string(self):
        self.assertIsNone(parsers.parse_first_letter(""), None)

    def test_None(self):
        self.assertIsNone(parsers.parse_first_letter(None), None)

    def test_first_number(self):
        self.assertEqual(parsers.parse_first_letter("365 days"), None)

    def test_white_space_removed(self):
        self.assertEqual(parsers.parse_first_letter(" War and Peace"), "W")

    def test_lower_case_changed_to_upper(self):
        self.assertEqual(parsers.parse_first_letter(" war and Peace"), "W")

    def test_diacritics_replaced(self):
        self.assertEqual(parsers.parse_first_letter("Łapsze"), "L")


class TestParseFirstWord(unittest.TestCase):
    """Test parsing of the first word to be used for a cutter"""

    def test_empty_string(self):
        self.assertIsNone(parsers.parse_first_word(""), None)

    def test_None(self):
        self.assertIsNone(parsers.parse_first_word(None), None)

    def test_first_number(self):
        self.assertEqual(parsers.parse_first_word("365 days"), None)

    def test_white_space_removed(self):
        self.assertEqual(parsers.parse_first_word(" War and Peace"), "WAR")

    def test_lower_case_changed_to_upper(self):
        self.assertEqual(parsers.parse_first_word(" war and Peace"), "WAR")

    def test_diacritics_replaced(self):
        self.assertEqual(parsers.parse_first_word("Łapsze"), "LAPSZE")


class TestParseLastName(unittest.TestCase):
    """Test parsing of the last name to be used for a cutter"""

    def test_empty_string(self):
        self.assertIsNone(parsers.parse_last_name(""), None)

    def test_None(self):
        self.assertIsNone(parsers.parse_last_name(None), None)

    def test_name_with_number(self):
        self.assertEqual(parsers.parse_last_name("4Chan"), "4CHAN")

    def test_white_space_removed(self):
        self.assertEqual(parsers.parse_last_name(" Smith, John"), "SMITH")

    def test_diacritics_replaced(self):
        self.assertEqual(parsers.parse_last_name("Łopuszańska, Bożena"), "LOPUSZANSKA")

    def test_compound_last_name_with_hyphen(self):
        self.assertEqual(parsers.parse_last_name("Smith-Johns, John"), "SMITH-JOHNS")

    def test_compound_last_name(self):
        self.assertEqual(parsers.parse_last_name("Smith Johns, John"), "SMITH JOHNS")

    def test_single_name(self):
        self.assertEqual(parsers.parse_last_name(" Prince. "), "PRINCE")


if __name__ == "__main__":
    unittest.main()
