# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field


from context import vendors


class TestPVFvendorIndex(unittest.TestCase):
    def setUp(self):
        self.rules = '../overload/rules/vendors.xml'
        self.nypl_data = vendors.vendor_index(self.rules, 'nypl', 'cat')
        self.bpl_data = vendors.vendor_index(self.rules, 'bpl', 'cat')

    def test_vendor_index_returns_list(self):
        self.assertIs(type(self.nypl_data), dict)
        self.assertIs(type(self.bpl_data), dict)

    def test_vendor_index_elements_are_dictionaries(self):
        for vendor, data in self.nypl_data.iteritems():
            self.assertIs(type(vendor), str)
            self.assertIs(type(data), dict)
        for vendor, data in self.bpl_data.iteritems():
            self.assertIs(type(vendor), str)
            self.assertIs(type(data), dict)

    def test_vendor_index_has_correct_structure(self):
        for vendor, data in self.nypl_data.iteritems():
            self.assertIn('query', data)
            self.assertIn('identification', data)
            self.assertIn('primary', data['query'])
            for key, value in data['identification'].iteritems():
                self.assertIn('operator', value)
                self.assertIn('type', value)
                self.assertIn('value', value)

            for preference, details in data['query'].iteritems():
                self.assertIsInstance(
                    details, tuple)

        for vendor, data in self.bpl_data.iteritems():
            self.assertIn('query', data)
            self.assertIn('identification', data)
            self.assertIn('primary', data['query'])
            for key, value in data['identification'].iteritems():
                self.assertIn('operator', value)
                self.assertIn('type', value)
                self.assertIn('value', value)


class TestFindMatches(unittest.TestCase):
    def setUp(self):
        self.bib1 = Record()
        self.bib1.add_field(
            Field(
                tag='245',
                indicators=['0', '0'],
                subfields=[
                    'a', 'Test '
                ]))
        self.bib1.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'abcd'
                ]))
        self.bib1.add_field(
            Field(
                tag='001',
                data='1234'
            ))

        self.bib2 = Record()
        self.bib2.add_field(
            Field(
                tag='245',
                indicators=['0', '0'],
                subfields=[
                    'a', 'Test '
                ]))
        self.bib2.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'abcd'
                ]))

    def test_2_matches(self):
        conditions = [('901', 'a', 'abcd'), ('001', None, '1234')]
        self.assertEqual(
            vendors.find_matches(self.bib1, conditions), 2)

    def test_only_1_match(self):
        conditions = [('901', 'a', 'abcd'), ('001', None, '12345')]
        self.assertEqual(
            vendors.find_matches(self.bib1, conditions), 1)

    def test_bib_missing_tag(self):
        conditions = [('901', 'a', 'abcd'), ('001', None, '1234')]
        self.assertEqual(
            vendors.find_matches(self.bib2, conditions), 1)


class TestParseIdentificationMethod(unittest.TestCase):
    def test_retuns_tuple(self):
        self.assertIs(
            type(vendors.parse_identification_method(
                '901a', 'standard')), tuple)
        self.assertEqual(
            len(vendors.parse_identification_method(
                '001', 'control_field')), 2)

    def test_correct_parsing_of_marc_tag(self):
        self.assertEqual(
            vendors.parse_identification_method(
                '001', 'control_field'), ('001', None))
        self.assertEqual(
            vendors.parse_identification_method(
                '901a', 'standard'), ('901', 'a'))

    def test_unknown_vendor(self):
        self.assertEqual(
            vendors.parse_identification_method(
                '', 'missing'), (None, None))


class TestIdentifyVendor(unittest.TestCase):
    def setUp(self):
        self.bib1 = Record()
        self.bib1.add_field(
            Field(
                tag='245',
                indicators=['0', '0'],
                subfields=[
                    'a', 'Test1'
                ]))
        self.bib1.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'VENDOR1'
                ]))

        self.bib2 = Record()
        self.bib2.add_field(
            Field(
                tag='245',
                indicators=['0', '0'],
                subfields=[
                    'a', 'Test2'
                ]))
        self.bib2.add_field(
            Field(
                tag='947',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'VENDOR2'
                ]))

        self.bib3 = Record()
        self.bib3.add_field(
            Field(
                tag='245',
                indicators=['0', '0'],
                subfields=[
                    'a', 'Test3'
                ]))
        self.bib3.add_field(
            Field(
                tag='901',
                indicators=[' ', ' '],
                subfields=[
                    'a', 'VENDOR3'
                ]))
        self.bib3.add_field(
            Field(
                tag='001',
                data='1234'
            ))
        self.vendor_index = {
            'TEST VENDOR1': {
                'query': {
                    'primary': '020'},
                'identification': {
                    '901a': {
                        'operator': 'main',
                        'type': 'standard',
                        'value': 'VENDOR1'}}},
            'TEST VENDOR2': {
                'query': {
                    'primary': '020', 'secondary': '001'},
                'identification': {
                    '947a': {
                        'operator': 'alternative',
                        'type': 'standard',
                        'value': 'VENDOR2'},
                    '037a': {
                        'operator': 'main',
                        'type': 'standard',
                        'value': 'some other value'}}}}

    def test_positive_single_main_match(self):
        self.assertEqual(
            vendors.identify_vendor(
                self.bib1, self.vendor_index), 'TEST VENDOR1')

    def test_positive_single_alternative_match(self):
        self.assertEqual(
            vendors.identify_vendor(
                self.bib2, self.vendor_index), 'TEST VENDOR2')

    def test_unknow_vendor(self):
        self.assertEqual(
            vendors.identify_vendor(
                self.bib3, self.vendor_index), 'UNKNOWN')


if __name__ == '__main__':
    unittest.main()
