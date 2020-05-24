# -*- coding: utf-8 -*-

import unittest


from context import bibs, create_bpl_fiction_callnum


class TestCreateBPLFictionCallNum(unittest.TestCase):
    """Tests creation of BPL fiction and picture book call numbers"""

    def setUp(self):
        self.leader_string = "00000cam a2200000Ia 4500"
        self.tag_008 = "961120s1988    nyu           000 1 eng d"
        self.tag_300a = "1 volume (various pagings)"
        self.cuttering_fields = {"100": "Smith, John", "245": "Test title"}
        self.order_data = bibs.BibOrderMeta(system="BPL", dstLibrary="branches")

    def test_english_adult_fiction(self):
        callnum = create_bpl_fiction_callnum(
            self.leader_string,
            self.tag_008,
            self.tag_300a,
            self.cuttering_fields,
            self.order_data,
        )
        self.assertEqual(str(callnum), "=099  \\\\$aFIC$aSMITH")


if __name__ == "__main__":
    unittest.main()