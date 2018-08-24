# -*- coding: utf-8 -*-

import unittest
import os


from context import dedup, bibs


class TestDedup_MARC_File(unittest.TestCase):
    """
    tests deduplication process in a MARC file
    """

    def setUp(self):
        self.fh = 'dups.mrc'
        self.fh_no_dups = 'no_dups.mrc'
        self.ind = {
            0: 'bl2017023500',
            1: 'bl2017023505',
            2: 'bl2017023500',
            3: 'bl2017023500',
        }

    def tearDown(self):
        try:
            os.remove(self.fh[:-4] + '-DEDUPED.mrc')
        except WindowsError:
            pass

    def test_find_duplicates(self):
        d = {'bl2017023500': [0, 2, 3]}
        dups, skip_bibs = dedup._find_duplicates(self.ind)
        self.assertEqual(
            dups, d)
        self.assertEqual(skip_bibs, [0, 2, 3])

    def test_find_duplicates_when_001_is_None(self):
        ind1 = {
            0: 'bl2017023500',
            1: None,
            2: None,
            3: 'bl2017023500'}
        d = {'bl2017023500': [0, 3]}
        dups, skip_bibs = dedup._find_duplicates(ind1)
        self.assertEqual(
            dups, d)
        self.assertEqual(
            skip_bibs, [0, 3])

    def test_merge_bibs_combine_items(self):
        bib_list = [1, 2, 3]
        combined_barcodes = [
            '33333849044546',
            '33333846242796',
            '33333846242804',
            '33333849044553',
            '33333846242812',
            '33333846242846'
        ]
        new_record, dedup_count = dedup.merge_bibs_combine_items(
            self.fh, bib_list)
        self.assertEqual(
            dedup_count, 3)
        self.assertEqual(
            new_record['001'].data, 'bl2017023534')
        for tag in new_record.get_fields('949'):
            if tag.indicators == [' ', '1']:
                for sub in tag.get_subfields('i'):
                    self.assertIn(sub, combined_barcodes)

    def test_dedup_marc_file_no_dups_return(self):
        self.assertEqual(
            dedup.dedup_marc_file(self.fh_no_dups),
            (0, 0, None))

    def test_dedup_marc_file_detailed(self):
        dedup_count, combined_count, deduped_fh = dedup.dedup_marc_file(
            self.fh)
        dup_barcodes = [
            '33333849044538',
            '33333846242770',
            '33333846242788',
            '33333849044553',
            '33333846242812',
            '33333846242846']
        reader = bibs.read_marc21(deduped_fh)
        barcode_counter = 0

        for record in reader:
            if record['001'] == 'bl2017023500':
                for tag in record.get_fields('949'):
                    if tag.indicators == [' ', '1']:
                        barcode_counter += 1
                        self.assertIn(
                            tag['i'][0],
                            dup_barcodes)

                self.assertEqual(
                    barcode_counter, len(dup_barcodes))

            elif record['001'] == 'bl2017023534':
                other_barcodes = [
                    '33333849044546',
                    '33333846242796',
                    '33333846242804'
                ]

                barcode_counter = 0
                for tag in record.get_fields('949'):
                    if tag.indicators == [' ', '1']:
                        barcode_counter += 1
                        self.assertIn(
                            tag['i'][0],
                            other_barcodes)

                self.assertEqual(
                    barcode_counter, len(other_barcodes))
        self.assertEqual(dedup_count, 5)
        self.assertEqual(combined_count, 1)


if __name__ == '__main__':
    unittest.main()
