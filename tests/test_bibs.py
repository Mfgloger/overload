# -*- coding: utf-8 -*-

import unittest
from pymarc import Record, Field, MARCReader, JSONReader
import os

from context import bibs, sierra_dicts
from context import OverloadError


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
            '03785955')

    def test_parsing_good_digit_x_ISSN(self):
        self.assertEqual(
            bibs.parse_issn('2434-561X'),
            '2434561X')

    def test_parsing_incorrect_ISSN(self):
        self.assertIsNone(
            bibs.parse_issn('M215104174'))


class TestParseSierraID(unittest.TestCase):
    """Test parsing Sierra bib and order id numbers"""

    def test_bib_number_parsing(self):
        self.assertIsNotNone(bibs.parse_sierra_id('.b119629811'))
        self.assertEqual(
            bibs.parse_sierra_id('.b119629811'),
            '11962981')

    def test_order_number_parsing(self):
        self.assertIsNotNone(bibs.parse_sierra_id('.o16799069'))
        self.assertEqual(
            bibs.parse_sierra_id('.o16799069'),
            '1679906')

    def test_wrong_id_number_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id('349876789087'))

    def test_None_id_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id(None))

    def test_empty_string_parsing(self):
        self.assertIsNone(bibs.parse_sierra_id(''))


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

        tags.append(
            Field(tag='949',
                  indicators=[' ', '1'],
                  subfields=['i', '33333818132462',
                             'l', 'fea0f',
                             'p', '9.99',
                             't', '102',
                             'v', 'AMALIVRE']))
        tags.append(
            Field(tag='949',
                  indicators=[' ', '1'],
                  subfields=['i', '33333818132464',
                             'l', 'fea0f',
                             'p', '9.99',
                             't', '102',
                             'v', 'AMALIVRE']))

        tags.append(
            Field(tag='960',
                  indicators=[' ', ' '],
                  subfields=['i', '33333818132466',
                             'l', 'fea0f',
                             'p', '9.99',
                             't', '102',
                             'v', 'AMALIVRE']))
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
            u'00266nam a2200085u  4500001002400000245001500024949004700039949004700086960004700133\x1e0001-test-control_field\x1e00\x1faTest title\x1e 1\x1fi33333818132462\x1flfea0f\x1fp9.99\x1ft102\x1fvAMALIVRE\x1e 1\x1fi33333818132464\x1flfea0f\x1fp9.99\x1ft102\x1fvAMALIVRE\x1e  \x1fi33333818132466\x1flfea0f\x1fp9.99\x1ft102\x1fvAMALIVRE\x1e\x1d')

    def test_read_marc21_returns_pymarc_reader(self):
        # should return an instance of pymarc reader
        reader = bibs.read_marc21('test.mrc')
        self.assertIs(type(reader), MARCReader)

    # def test_count_bibs_when_not_marc_file(self):
    #     with self.assertRaises(OverloadError):
    #         bibs.count_bibs('test.json')

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

    def test_check_sierra_command_tag_presence_False(self):
        self.assertFalse(
            bibs.sierra_command_tag(self.marc_bib))
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
            bibs.sierra_command_tag(self.marc_bib))

    def test_check_sierra_command_tag_presence_True(self):
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', "*b2=a;"]))
        self.assertTrue(
            bibs.sierra_command_tag(self.marc_bib))

    def test_check_sierra_command_tag_presence_exception(self):
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', '']))
        with self.assertRaises(IndexError):
            bibs.sierra_command_tag(self.marc_bib)

    def test_create_field_from_template(self):
        template = dict(
            option='skip',
            tag='949',
            ind1=None,
            ind2='1',
            subfields={'a': 'foo', 'b': 'bar'}
        )
        field = bibs.create_field_from_template(template)
        self.assertIsInstance(field, Field)
        self.assertEqual(field.tag, '949')
        self.assertEqual(field.indicators, [' ', '1'])
        self.assertEqual(field['a'], 'foo')
        self.assertEqual(field['b'], 'bar')

    def test_set_nypl_sierra_bib_default_location_for_branches_new(self):
        # test when no command line present
        bib = bibs.set_nypl_sierra_bib_default_location('branches', self.marc_bib)
        for field in bib.get_fields('949'):
            if field.indicators == [' ', ' ']:
                command = field
        self.assertEqual(
            str(command), '=949  \\\\$a*bn=zzzzz;')

    def test_set_nypl_sierra_bib_default_location_for_branches_present(self):
        # test adding location skipped when "bn=" command already present
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', '*recs=a;bn=xxx;']))
        bib = bibs.set_nypl_sierra_bib_default_location('branches', self.marc_bib)
        for field in bib.get_fields('949'):
            if field.indicators == [' ', ' ']:
                command = field
        self.assertEqual(
            str(command), '=949  \\\\$a*recs=a;bn=xxx;')

    def test_set_nypl_sierra_bib_default_location_for_branches_other_command_present(self):
        # simulate command line with other parameters present
        self.marc_bib.add_field(
            Field(
                tag='949',
                indicators=[' ', ' '],
                subfields=['a', '*recs=a']))
        bib = bibs.set_nypl_sierra_bib_default_location('branches', self.marc_bib)
        for field in bib.get_fields('949'):
            if field.indicators == [' ', ' ']:
                command = field
        self.assertEqual(
            str(command),
            '=949  \\\\$a*recs=a;bn=zzzzz;')

    def test_set_nypl_sierra_bib_default_location_for_research_new(self):
        # test when no command line present
        bib = bibs.set_nypl_sierra_bib_default_location('research', self.marc_bib)
        for field in bib.get_fields('949'):
            if field.indicators == [' ', ' ']:
                command = field
        self.assertEqual(
            str(command), '=949  \\\\$a*bn=xxx;')


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
        self.marc_bib.add_field(
            Field(
                tag='945',
                indicators=[' ', ' '],
                subfields=['a', '.b01234569a']))
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
        self.assertEqual(meta.sierraId, '01234569')
        self.assertEqual(meta.barcodes, ['33333818132462', '33333818132464', '33333818132466'])

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


class TestTemplate_to_960(unittest.TestCase):
    """
    Tests of creation of order fixed fields in 960 MARC tag
    """

    def setUp(self):
        class template:
            pass

        self.temp = template()
        self.temp.acqType = None
        self.temp.claim = None
        self.temp.code1 = None
        self.temp.code2 = None
        self.temp.code3 = None
        self.temp.code4 = None
        self.temp.form = None
        self.temp.orderNote = None
        self.temp.orderType = None
        self.temp.status = '1'
        self.temp.vendor = None
        self.temp.lang = None
        self.temp.country = None

    def test_vendor_960_is_None(self):
        field = bibs.db_template_to_960(self.temp, None)
        self.assertIsInstance(
            field, Field)
        self.assertEqual(
            field['m'], '1')
        self.assertEqual(
            str(field),
            '=960  \\\\$m1')

    def test_no_vendor960_but_at_least_one_template_attr_set(self):
        self.temp.vendor = 'TEST'
        field = bibs.db_template_to_960(self.temp, None)
        self.assertEqual(
            str(field),
            '=960  \\\\$m1$vTEST')
        self.temp.internalNote = None
        self.temp.vendor = None

    def test_template_None_keeps_vendor_subfields(self):
        vfield = Field(
            tag='960',
            indicators=[' ', ' '],
            subfields=[
                'a', '1',
                'b', '2',
                'c', '3',
                'd', '4',
                'e', '5',
                'f', '6',
                'g', '7',
                'h', '8',
                'i', '9',
                'm', '10',
                'v', '11',
                'w', '12',
                'x', '13'
            ])

        field = bibs.db_template_to_960(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=960  \\\\$a1$b2$c3$d4$e5$f6$g7$h8$i9$m1$v11$w12$x13')

    def test_template_overwrites_vendor(self):
        self.temp.acqType = 'a'
        self.temp.claim = 'b'
        self.temp.code1 = 'c'
        self.temp.code2 = 'd'
        self.temp.code3 = 'e'
        self.temp.code4 = 'f'
        self.temp.form = 'g'
        self.temp.orderNote = 'h'
        self.temp.orderType = 'i'
        self.temp.status = 'm'
        self.temp.vendor = 'v'
        self.temp.lang = 'w'
        self.temp.country = 'x'

        vfield = Field(
            tag='960',
            indicators=[' ', ' '],
            subfields=[
                'a', '1',
                'b', '2',
                'c', '3',
                'd', '4',
                'e', '5',
                'f', '6',
                'g', '7',
                'h', '8',
                'i', '9',
                'm', '10',
                'v', '11',
                'w', '12',
                'x', '13'
            ])

        field = bibs.db_template_to_960(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=960  \\\\$aa$bb$cc$dd$ee$ff$gg$hh$ii$mm$vv$ww$xx')

    def test_mixed_template_vendor_subfields(self):
        self.temp.acqType = 'a'
        self.temp.code2 = 'd'
        self.temp.code3 = 'e'
        self.temp.orderType = 'i'
        self.temp.status = 'm'
        self.temp.vendor = 'v'

        vfield = Field(
            tag='960',
            indicators=[' ', ' '],
            subfields=[
                'a', '1',
                's', '9.99',
                'u', '2'
            ])
        field = bibs.db_template_to_960(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=960  \\\\$s9.99$u2$aa$dd$ee$ii$mm$vv')


class TestTemplate_to_961(unittest.TestCase):
    """
    Tests of creation of order varied fields in 961 MARC tag
    """

    def setUp(self):
        class template:
            pass

        self.temp = template()
        self.temp.identity = None
        self.temp.generalNote = None
        self.temp.internalNote = None
        self.temp.oldOrdNo = None
        self.temp.selector = None
        self.temp.venAddr = None
        self.temp.venNote = None
        self.temp.blanketPO = None
        self.temp.venTitleNo = None
        self.temp.paidNote = None
        self.temp.shipTo = None
        self.temp.requestor = None

    def tearDown(self):
        self.temp.identity = None
        self.temp.generalNote = None
        self.temp.internalNote = None
        self.temp.oldOrdNo = None
        self.temp.selector = None
        self.temp.venAddr = None
        self.temp.venNote = None
        self.temp.blanketPO = None
        self.temp.venTitleNo = None
        self.temp.paidNote = None
        self.temp.shipTo = None
        self.temp.requestor = None

    def test_vendor_subfields_None_return_None(self):
        field = bibs.db_template_to_961(self.temp, None)
        self.assertIsNone(field)

    def test_no_vendor961_but_at_least_one_template_attr_set(self):
        self.temp.internalNote = 'TEST'
        field = bibs.db_template_to_961(self.temp, None)
        self.assertEqual(
            str(field),
            '=961  \\\\$dTEST')
        self.temp.internalNote = None

    def test_retuns_None_if_all_template_attr_not_None(self):
        field = bibs.db_template_to_961(self.temp, None)
        self.assertIsNone(field)

    def test_returns_Field_obj_when_template_None_but_field_exists(self):
        vfield = Field(
            tag='961',
            indicators=[' ', ' '],
            subfields=['a', '1', 'b', '2'])
        field = bibs.db_template_to_961(self.temp, vfield)
        self.assertIsInstance(field, Field)
        self.assertEqual(
            str(field),
            '=961  \\\\$b2$a1')

    def test_if_template_overwrites_vendor_subfields(self):
        self.temp.identity = 'a'
        self.temp.generalNote = 'c'
        self.temp.internalNote = 'd'
        self.temp.oldOrdNo = 'e'
        self.temp.selector = 'f'
        self.temp.venAddr = 'g'
        self.temp.venNote = 'h'
        self.temp.blanketPO = 'm'
        self.temp.venTitleNo = 'i'
        self.temp.paidNote = 'j'
        self.temp.shipTo = 'k'
        self.temp.requestor = 'l'

        vfield = Field(
            tag='961',
            indicators=[' ', ' '],
            subfields=[
                'a', '1',
                'c', '3',
                'd', '4',
                'e', '5',
                'f', '6',
                'g', '7',
                'i', '8',
                'j', '9',
                'k', '10',
                'l', '11',
                'm', '12',
                'h', '13',
            ])
        field = bibs.db_template_to_961(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=961  \\\\$aa$cc$dd$ee$ff$gg$hh$mm$ii$jj$kk$ll')

    def test_template_attr_None_keeps_vendor_subfields(self):
        vfield = Field(
            tag='961',
            indicators=[' ', ' '],
            subfields=[
                'a', '1',
                'c', '2',
                'd', '3',
                'e', '4',
                'f', '5',
                'g', '6',
                'i', '7',
                'j', '8',
                'k', '9',
                'l', '10',
                'm', '11',
                'h', '12',
            ])
        field = bibs.db_template_to_961(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=961  \\\\$a1$c2$d3$e4$f5$g6$h12$m11$i7$j8$k9$l10')

    def test_mixed_vendor_template_field(self):
        vfield = Field(
            tag='961',
            indicators=[' ', ' '],
            subfields=[
                'a', '1',
                'h', '1',])

        self.temp.identity = 'a'
        self.temp.blanketPO = 'm'
        field = bibs.db_template_to_961(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=961  \\\\$aa$h1$mm')

    def test_1(self):
        vfield = Field(
            tag='961',
            indicators=[' ', ' '],
            subfields=['h', 'g'])
        field = bibs.db_template_to_961(self.temp, vfield)
        self.assertEqual(
            str(field),
            '=961  \\\\$hg')


class TestInhouseBibMeta(unittest.TestCase):
    """
    Inhouse meta analysis tests
    """

    def setUp(self):
        # Test MARC record

        # NYPL bib
        self.n_marc = Record()
        self.n_marc.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='o1234'))
        tags.append(
            Field(tag='003', data='OCoLC'))
        tags.append(
            Field(
                tag='049',
                indicators=[' ', ' '],
                subfields=['a', 'NYPP']))

        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))

        for tag in tags:
            self.n_marc.add_ordered_field(tag)

        # BPL bib
        self.b_marc = Record()
        self.b_marc.leader = '00000nam a2200000u  4500'
        tags = []
        tags.append(
            Field(tag='001', data='o1234'))
        tags.append(
            Field(tag='003', data='OCoLC'))
        tags.append(
            Field(
                tag='049',
                indicators=[' ', ' '],
                subfields=['a', 'BKL']))

        tags.append(
            Field(tag='245',
                  indicators=['0', '0'],
                  subfields=['a', 'Test title']))

        for tag in tags:
            self.b_marc.add_ordered_field(tag)

    def tearDown(self):
        # Test MARC record

        # NYPL bib
        self.n_marc = Record()

        # BPL bib
        self.b_marc = Record()

    def test_nypl_ownLibrary_no_locations(self):
        locs = []

        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertIsNone(meta.ownLibrary)

    def test_nypl_ownLibrary_xxx(self):
        locs = ['xxx']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'research')

    def test_nypl_ownLibrary_zzzzz(self):
        locs = ['zzzzz']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'branches')

    def test_nypl_ownLibrary_mixed_order(self):
        locs = ['zzzzz', 'xxx']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_nypl_ownLibrary_mixed_explicit_my(self):
        locs = ['mya0f', 'myd']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_nypl_ownLibrary_mixed_explicit_ma(self):
        locs = ['mya0n', 'mal']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_nypl_ownLibrary_branch_locs_only(self):
        locs = sierra_dicts.NYPL_BRANCHES.keys()
        locs.remove('ma')
        locs.remove('sc')
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'branches')

    def test_nypl_ownLibrary_research_my_locs(self):
        locs = ['myd', 'myh', 'mym', 'myt']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'research')

    def test_nypl_ownLibrary_branches_my_locs(self):
        locs = ['mya0n', 'mya0v', 'myj0f']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'branches')

    def test_nypl_ownLibrary_resarch_ma_loc(self):
        locs = ['mal']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'research')

    def test_nypl_ownLibrary_research_sc_loc(self):
        locs = ['sc']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'research')

    def test_nypl_branch_full_no_order(self):
        tag = Field(
            tag='091',
            indicators=[' ', ' '],
            subfields=['f', 'FIC', 'a', 'ADAMS'])
        self.n_marc.add_ordered_field(tag)
        meta = bibs.InhouseBibMeta(self.n_marc)
        self.assertEqual(meta.ownLibrary, 'branches')

    def test_nypl_research_full_no_order(self):
        tag = Field(
            tag='852',
            indicators=['8', ' '],
            subfields=['h', 'ReCAP 0001'])
        self.n_marc.add_ordered_field(tag)
        meta = bibs.InhouseBibMeta(self.n_marc)
        self.assertEqual(meta.ownLibrary, 'research')

    def test_nypl_mixed_full_no_order(self):
        tag = Field(
            tag='852',
            indicators=['8', ' '],
            subfields=['h', 'ReCAP 0001'])
        self.n_marc.add_ordered_field(tag)

        tag = Field(
            tag='091',
            indicators=[' ', ' '],
            subfields=['f', 'FIC', 'a', 'ADAMS'])
        self.n_marc.add_ordered_field(tag)

        meta = bibs.InhouseBibMeta(self.n_marc)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_nypl_mixed_branch_full_research_order(self):
        tag = Field(
            tag='091',
            indicators=[' ', ' '],
            subfields=['f', 'FIC', 'a', 'ADAMS'])
        self.n_marc.add_ordered_field(tag)
        locs = ['xxx']
        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_nypl_mixed_research_full_branch_order(self):
        tag = Field(
            tag='852',
            indicators=['8', ' '],
            subfields=['h', 'ReCAP 0001'])
        self.n_marc.add_ordered_field(tag)

        locs = ['zzzzz']

        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_nypl_mixed_research_full_branch_order_explicit(self):
        tag = Field(
            tag='852',
            indicators=['8', ' '],
            subfields=['h', 'ReCAP 0001'])
        self.n_marc.add_ordered_field(tag)
        self.assertFalse('091' in self.n_marc)

        locs = ['mya0n']

        meta = bibs.InhouseBibMeta(self.n_marc, locations=locs)
        self.assertEqual(meta.ownLibrary, 'mixed')

    def test_bpl_ownLibrary_order(self):
        meta = bibs.InhouseBibMeta(self.b_marc)
        self.assertIsNone(meta.ownLibrary)

    def test_bpl_ownLibrary_full(self):
        tag = Field(
            tag='099',
            indicators=[' ', ' '],
            subfields=['a', 'FIC', 'a', 'ADAMS'])
        self.b_marc.add_ordered_field(tag)
        meta = bibs.InhouseBibMeta(self.b_marc)
        self.assertEqual(meta.ownLibrary, 'branches')


if __name__ == '__main__':
    unittest.main()
