# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET
import unittest


from context import xml_bibs as xb


class TestGetSubjectFields(unittest.TestCase):
    """Tests parsing of subjects from marcxml"""

    def setUp(self):
        tree = ET.parse("sample_marcxml.xml")
        self.data1 = tree.getroot()

        tree = ET.parse("missing_tags_sample_marcxml.xml")
        self.data2 = tree.getroot()

    def test_none(self):
        self.assertEqual(xb.get_subject_fields(None), {})

    def test_missing_tag(self):
        self.assertEqual(xb.get_subject_fields(self.data2), {})

    def test_present_600_tag(self):
        self.assertEqual(xb.get_subject_fields(self.data1), {"600": "Elizabeth II"})


class TestGetTag082(unittest.TestCase):
    """Tests parsing 082 tag subfield a"""

    def setUp(self):
        tree = ET.parse("sample_marcxml.xml")
        self.data1 = tree.getroot()

        tree = ET.parse("missing_tags_sample_marcxml.xml")
        self.data2 = tree.getroot()

    def test_none(self):
        self.assertIsNone(xb.get_tag_082(None))

    def test_missing_tag(self):
        self.assertIsNone(xb.get_tag_082(self.data2))

    def test_found_tag(self):
        self.assertEqual(xb.get_tag_082(self.data1), "973.9/092/2")


if __name__ == "__main__":
    unittest.main()
