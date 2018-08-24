# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field
import os


from context import local_specs
from context import bibs


class TestLocalSpecsParser(unittest.TestCase):
    """
    Tests parsing of the vendor_specs.xml file
    """

    def setUp(self):
        self.rules = '../overload/rules/vendor_specs.xml'
        self.ncl = local_specs.local_specs('nypl', 'cat', self.rules)
        self.bcl = local_specs.local_specs('bpl', 'cat', self.rules)

    def test_incorrect_attributes_passed(self):
        with self.assertRaises(AttributeError):
            local_specs.local_specs('qpl', 'cat', self.rules)
        with self.assertRaises(AttributeError):
            local_specs.local_specs('nypl', 'sea', self.rules)

    def test_list_of_dict_returned(self):
        # NYPL specs
        self.assertIs(type(self.ncl), list)
        for i in self.ncl:
            self.assertIs(type(i), dict)

            # make sure all keys present
            self.assertIn('ind', i)
            self.assertIn('subfields', i)
            self.assertIn('repeatable', i)
            self.assertIn('mandatory', i)
            self.assertIn('tag', i)

            # subfields are list of dicts
            self.assertIs(type(i['subfields']), list)

            # make sure all subfields in list are properly formed
            for s in i['subfields']:
                self.assertIs(type(s), dict)
                self.assertIn('code', s)
                self.assertIn('repeatable', s)
                self.assertIn('mandatory', s)
                self.assertIn('check', s)
                self.assertIn('value', s)

                self.assertIn(
                    s['check'],
                    [None, 'list', 'barcode', 'location', 'price'])

        # BPL specs
        self.assertIs(type(self.bcl), list)
        for i in self.bcl:
            self.assertIs(type(i), dict)

            # make sure all keys present
            self.assertIn('ind', i)
            self.assertIn('subfields', i)
            self.assertIn('repeatable', i)
            self.assertIn('mandatory', i)
            self.assertIn('tag', i)

            # subfields are list of dicts
            self.assertIs(type(i['subfields']), list)

            # make sure all subfields in list are properly formed
            for s in i['subfields']:
                self.assertIs(type(s), dict)
                self.assertIn('code', s)
                self.assertIn('repeatable', s)
                self.assertIn('mandatory', s)
                self.assertIn('check', s)
                self.assertIn('value', s)

                self.assertIn(
                    s['check'],
                    [None, 'list', 'barcode', 'location', 'price'])


class Test_Branch_Validation(unittest.TestCase):
    """
    tests location_check function
    """

    def test_nypl_midmanhattan_branche(self):
        self.assertTrue(
            local_specs.location_check('nypl', 'mm'))

    def test_nypl_incorrect_branch(self):
        self.assertFalse(
            local_specs.location_check('nypl', ''))

    def test_bpl_central_02_location(self):
        self.assertTrue(
            local_specs.location_check('bpl', '02'))

    def test_bpl_obsolete_95_location(self):
        self.assertFalse(
            local_specs.location_check('bpl', '95'))


class Test_Price_Subfield_Validation(unittest.TestCase):
    """
    tests price format
    """

    def test_empty_subfield(self):
        self.assertFalse(
            local_specs.price_check(''))

    def test_None_in_subfield(self):
        self.assertFalse(
            local_specs.price_check(None))

    def test_inocorrect_format(self):
        self.assertFalse(
            local_specs.price_check('999'))

    def test_incorrect_data(self):
        self.assertFalse(
            local_specs.price_check('abc'))

    def test_correct_format(self):
        self.assertTrue(
            local_specs.price_check('0.99'))


class Test_NYPL_CAT_Specs(unittest.TestCase):
    """
    testing if NYPL cat specs are being correctly identified
    """

    def setUp(self):
        self.rules = '../overload/rules/vendor_specs.xml'
        self.ncl = local_specs.local_specs('nypl', 'cat', self.rules)

    def tearDown(self):
        os.remove('specs_test.mrc')

    def test_091_not_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='091',
                indicators=[' ', ' '],
                subfields=['a', 'TEST']))
        b.add_field(
            Field(
                tag='091',
                indicators=[' ', ' '],
                subfields=['a', 'TEST2']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"091  " is not repeatable',
            report)

    def test_091_subfields(self):
        b = Record()
        b.add_field(
            Field(
                tag='091',
                indicators=[' ', ' '],
                subfields=[
                    'p', 'TEST',
                    'p', 'TEST',
                    'c', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"091": tag occurance 1:\n\t"p" subfield is not repeatable.',
            report)
        self.assertIn(
            '"a" subfield is mandatory.',
            report)

    def test_901_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='245',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"901  " mandatory tag not found.',
            report)

    def test_901_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST2']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"901  " is not repeatable',
            report)

    def test_901_mandatory_subfield_a(self):
        b = Record()
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'c', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is mandatory.',
            report)

    def test_901_nonrepeatable_subfield_a(self):
        b = Record()
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST',
                    'a', 'TEST1']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is not repeatable.',
            report)

    def test_901_incorrect_subfield_a_value(self):
        b = Record()
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield has incorrect value',
            report)

    def test_949_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='245',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"949  " mandatory tag not found.',
            report)

    def test_949_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"949  " is not repeatable',
            report)

    def test_949_repeatable_diff_indicators(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertNotIn(
            '"949  " is not repeatable',
            report)

    def test_949_subfield_a_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[]))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is mandatory.',
            report)

    def test_949_subfield_a_nonrepeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST',
                    'a', 'TEST1']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is not repeatable.',
            report)

    def test_949_subfield_a_incorrect_value(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'b2=a;']))  # missing * in the begining
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield has incorrect value',
            report)

    def test_949_items_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"949 1" mandatory tag not found.',
            report)

    def test_949_items_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST2']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertNotIn(
            '"949 1" is not repeatable.',
            report)

    def test_949_items_mandatory_subfields(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield is mandatory.',
            report)
        self.assertIn(
            '"l" subfield is mandatory.',
            report)
        self.assertIn(
            '"p" subfield is mandatory.',
            report)
        self.assertIn(
            '"t" subfield is mandatory.',
            report)
        self.assertIn(
            '"v" subfield is mandatory.',
            report)

    def test_949_items_nonrepeatable_subfields(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', 'TEST',
                    'i', 'TEST',
                    'l', 'TEST',
                    'l', 'TEST',
                    'p', '9.99',
                    'p', '9.99',
                    't', 'TEST',
                    't', 'TEST',
                    'o', 'TEST',
                    'o', 'TEST',
                    'u', 'TEST',
                    'u', 'TEST',
                    'm', 'TEST',
                    'm', 'TEST',
                    'v', 'TEST',
                    'v', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield is not repeatable.',
            report)
        self.assertIn(
            '"l" subfield is not repeatable.',
            report)
        self.assertIn(
            '"p" subfield is not repeatable.',
            report)
        self.assertIn(
            '"t" subfield is not repeatable.',
            report)
        self.assertIn(
            '"o" subfield is not repeatable.',
            report)

    def test_949_items_barcode_not_digits(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_949_items_short_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '3444498765432']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_nypl_949_items_with_bpl_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '34444987654328']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_949_items_letter_in_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '34444987l54328']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_949_items_good_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '33333987954328']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertNotIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_949_items_incorrect_location(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'l', '23anf']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertFalse(passed)
        self.assertIn(
            '"l" subfield has incorrect location code.',
            report)

    def test_949_items_empty_location(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'l', '']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertIn(
            '"l" subfield has incorrect location code.',
            report)

    def test_949_items_empty_price_subfield(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'p', '']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_949_items_incorrect_price_subfield(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'p', '9999']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_949_items_correct_price_format(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'p', '9.99']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertNotIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_949_items_stat_code_empty(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    't', '']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertIn(
            '"t" subfield has incorrect value.',
            report)

    def test_949_items_stat_code_incorrect(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    't', '600']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertIn(
            '"t" subfield has incorrect value.',
            report)

    def test_dvd_case1(self):
        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '33333306093499',
                    'l', 'mya0v',
                    'p', '24.99',
                    't', '111',
                    'v', 'Midwest',
                    'n', 'o24643440',
                    'q', '10001']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '33333306093481',
                    'l', 'bta0v',
                    'p', '24.99',
                    't', '111',
                    'v', 'Midwest',
                    'n', 'o24643440',
                    'q', '10001']))
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=['a', 'Midwest']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', '*b2=v;']))

        bibs.write_marc21('specs_test.mrc', b)

        b = Record()
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '33333306093457',
                    'l', 'mya0v',
                    'p', '14.99',
                    't', '206',
                    'v', 'Midwest',
                    'n', 'o24643282',
                    'q', '10001']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', '1'],
                subfields=[
                    'i', '33333306093432',
                    'l', 'bca0v',
                    'p', '14.99',
                    't', '206',
                    'v', 'Midwest',
                    'n', 'o24643282',
                    'q', '10001']))
        b.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=['a', 'Midwest']))
        b.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', '*b2=v;']))

        bibs.write_marc21('specs_test.mrc', b)

        passed, report = local_specs.local_specs_validation(
            'nypl', ['specs_test.mrc'], self.ncl)
        self.assertTrue(passed)


class Test_BPL_CAT_Specs(unittest.TestCase):
    """
    testing if NYPL cat specs are being correctly identified
    """

    def setUp(self):
        self.rules = '../overload/rules/vendor_specs.xml'
        self.bcl = local_specs.local_specs('bpl', 'cat', self.rules)

    def tearDown(self):
        os.remove('specs_test.mrc')

    def test_091_not_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='099',
                indicators=[' ', ' '],
                subfields=['a', 'TEST']))
        b.add_field(
            Field(
                tag='0099',
                indicators=[' ', ' '],
                subfields=['a', 'TEST2']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"099  " is not repeatable',
            report)

    def test_091_subfields(self):
        b = Record()
        b.add_field(
            Field(
                tag='099',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST',
                    'a', 'TEST2']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertNotIn(
            '"099  ": tag occurance 1:\n\t"p" subfield is not repeatable.',
            report)

    def test_091_no_subfield_a(self):
        b = Record()
        b.add_field(
            Field(
                tag='099',
                indicators=[' ', ' '],
                subfields=[
                    'p', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is mandatory.',
            report)

    def test_901_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='245',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"947  " mandatory tag not found.',
            report)

    def test_947_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='947',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='947',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST2']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"947  " is not repeatable',
            report)

    def test_947_mandatory_subfield_a(self):
        b = Record()
        b.add_field(
            Field(
                tag='947',
                indicators=[' ', ' '],
                subfields=[
                    'c', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is mandatory.',
            report)

    def test_947_nonrepeatable_subfield_a(self):
        b = Record()
        b.add_field(
            Field(
                tag='947',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST',
                    'a', 'TEST1']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield is not repeatable.',
            report)

    def test_947_incorrect_subfield_a_value(self):
        b = Record()
        b.add_field(
            Field(
                tag='947',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"a" subfield has incorrect value',
            report)

    def test_960_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='245',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"960  " mandatory tag not found.',
            report)

    def test_960_repeatable(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertNotIn(
            '"960 1" is not repeatable',
            report)

    def test_960_repeatable_diff_indicators(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertNotIn(
            '"960 1" is not repeatable',
            report)

    def test_960_items_mandatory(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"960  " mandatory tag not found.',
            report)

    def test_960_items_mandatory_subfields(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield is mandatory.',
            report)
        self.assertIn(
            '"l" subfield is mandatory.',
            report)
        self.assertIn(
            '"p" subfield is mandatory.',
            report)
        self.assertIn(
            '"q" subfield is mandatory.',
            report)
        self.assertNotIn(
            '"o" subfield is mandatory.',
            report)
        self.assertIn(
            '"t" subfield is mandatory.',
            report)
        self.assertIn(
            '"r" subfield is mandatory.',
            report)
        self.assertIn(
            '"s" subfield is mandatory.',
            report)
        self.assertIn(
            '"v" subfield is mandatory.',
            report)
        self.assertIn(
            '"n" subfield is mandatory.',
            report)

    def test_960_items_nonrepeatable_subfields(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'i', 'TEST',
                    'i', 'TEST',
                    'l', 'TEST',
                    'l', 'TEST',
                    'p', '9.99',
                    'p', '9.99',
                    'q', 'TEST',
                    'q', 'TEST',
                    'o', 'TEST',
                    'o', 'TEST',
                    't', 'TEST',
                    't', 'TEST',
                    'r', 'TEST',
                    'r', 'TEST',
                    's', 'TEST',
                    's', 'TEST',
                    'v', 'TEST',
                    'v', 'TEST',
                    'n', 'TEST',
                    'n', 'TEST',
                    'v', 'TEST',
                    'v', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield is not repeatable.',
            report)
        self.assertIn(
            '"l" subfield is not repeatable.',
            report)
        self.assertIn(
            '"p" subfield is not repeatable.',
            report)
        self.assertIn(
            '"q" subfield is not repeatable.',
            report)
        self.assertIn(
            '"o" subfield is not repeatable.',
            report)
        self.assertIn(
            '"t" subfield is not repeatable.',
            report)
        self.assertIn(
            '"r" subfield is not repeatable.',
            report)
        self.assertIn(
            '"s" subfield is not repeatable.',
            report)
        self.assertIn(
            '"v" subfield is not repeatable.',
            report)
        self.assertIn(
            '"n" subfield is not repeatable.',
            report)

    def test_960_items_barcode_not_digits(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'i', 'TEST']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_960_items_short_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'i', '3333398765432']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_960_items_with_nypl_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'i', '33333987654328']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_60_items_letter_in_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'i', '34444987l54328']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_960_items_good_barcode(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'i', '34444987954328']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertNotIn(
            '"i" subfield has incorrect barcode.',
            report)

    def test_960_items_incorrect_location(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'l', 'mma0l']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertFalse(passed)
        self.assertIn(
            '"l" subfield has incorrect location code.',
            report)

    def test_960_items_empty_location(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'l', '']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertIn(
            '"l" subfield has incorrect location code.',
            report)

    def test_960_items_empty_price_subfield(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'p', '']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_960_items_incorrect_price_subfield(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'p', '9999']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_960_items_correct_price_format(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'p', '9.99']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertNotIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_960_items_midwest_price_format(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', '1'],
                subfields=[
                    'p', r'$20.99']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertNotIn(
            '"p" subfield has incorrect price format.',
            report)

    def test_960_items_stat_code_empty(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'q', '']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertIn(
            '"q" subfield has incorrect value.',
            report)

    def test_960_items_stat_code_incorrect(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'q', '999']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertIn(
            '"q" subfield has incorrect value.',
            report)

    def test_960_items_incorrect_format(self):
        b = Record()
        b.add_field(
            Field(
                tag='960',
                indicators=[' ', ' '],
                subfields=[
                    'r', 'z']))
        bibs.write_marc21('specs_test.mrc', b)
        passed, report = local_specs.local_specs_validation(
            'bpl', ['specs_test.mrc'], self.bcl)
        self.assertIn(
            '"r" subfield has incorrect value.',
            report)


if __name__ == '__main__':
    unittest.main()
