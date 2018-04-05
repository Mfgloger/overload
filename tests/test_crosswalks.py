# -*- coding: utf-8 -*-

import unittest
import json

from context import crosswalks
from context import bibs


class TestPlatform2PymarcObj(unittest.TestCase):
    """Tests conversion from Platform bib data to pymarc obj"""
    def setUp(self):
        self.data = {u'varFields': [
            {u'marcTag': u'100', u'ind1': u'1', u'ind2': u' ', u'content': None, u'fieldTag': u'a', u'subfields': [{u'content': u'Rowling, J. K.', u'tag': u'a'}]},
            {u'marcTag': u'091', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'c', u'subfields': [{u'content': u'FIC', u'tag': u'a'}, {u'content': u'ROWLING', u'tag': u'c'}]},
            {u'marcTag': u'600', u'ind1': u'1', u'ind2': u'0', u'content': None, u'fieldTag': u'd', u'subfields': [{u'content': u'Potter, Harry', u'tag': u'a'}, {u'content': u'(Fictitious character)', u'tag': u'c'}, {u'content': u'Juvenile fiction.', u'tag': u'v'}]},
            {u'marcTag': u'655', u'ind1': u' ', u'ind2': u'7', u'content': None, u'fieldTag': u'd', u'subfields': [{u'content': u'Fantasy fiction', u'tag': u'a'}, {u'content': u'Juvenile.', u'tag': u'v'}, {u'content': u'gsafd', u'tag': u'2'}]},
            {u'marcTag': u'020', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'i', u'subfields': [{u'content': u'0439136350 (hc)', u'tag': u'a'}]},
            {u'marcTag': u'020', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'i', u'subfields': [{u'content': u'9780439136358 (hc)', u'tag': u'a'}]},
            {u'marcTag': u'010', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'l', u'subfields': [{u'content': u'   99023982', u'tag': u'a'}]},
            {u'marcTag': u'035', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'l', u'subfields': [{u'content': u'(OCoLC)41266045', u'tag': u'a'}, {u'content': u'(OCoLC)308560027', u'tag': u'z'}, {u'content': u'(OCoLC)519740398', u'tag': u'z'}]},
            {u'marcTag': u'001', u'ind1': u' ', u'ind2': u' ', u'content': u'41266045', u'fieldTag': u'o', u'subfields': None},
            {u'marcTag': u'260', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'p', u'subfields': [{u'content': u'New York :', u'tag': u'a'}, {u'content': u'Arthur A. Levine Books,', u'tag': u'b'}, {u'content': u'1999.', u'tag': u'c'}]},
            {u'marcTag': u'300', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'r', u'subfields': [{u'content': u'ix, 435 p. :', u'tag': u'a'}, {u'content': u'ill. ;', u'tag': u'b'}, {u'content': u'24 cm.', u'tag': u'c'}]},
            {u'marcTag': u'245', u'ind1': u'1', u'ind2': u'0', u'content': None, u'fieldTag': u't', u'subfields': [{u'content': u'Harry Potter and the prisoner of Azkaban /', u'tag': u'a'}, {u'content': u'by J.K. Rowling.', u'tag': u'c'}]},
            {u'marcTag': u'995', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'v', u'subfields': [{u'content': u'1483934', u'tag': u'a'}]},
            {u'marcTag': u'995', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'v', u'subfields': [{u'content': u'2701169', u'tag': u'a'}]},
            {u'marcTag': u'003', u'ind1': u' ', u'ind2': u' ', u'content': u'OCoLC', u'fieldTag': u'y', u'subfields': None},
            {u'marcTag': u'005', u'ind1': u' ', u'ind2': u' ', u'content': u'20120731084140.9', u'fieldTag': u'y', u'subfields': None},
            {u'marcTag': u'008', u'ind1': u' ', u'ind2': u' ', u'content': u'990408s1999    nyua   c      000 1 eng dcam a ', u'fieldTag': u'y', u'subfields': None},
            {u'marcTag': u'019', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'308560027', u'tag': u'a'}, {u'content': u'519740398', u'tag': u'a'}]},
            {u'marcTag': u'040', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'DLC', u'tag': u'a'}, {u'content': u'DLC', u'tag': u'c'}, {u'content': u'BAKER', u'tag': u'd'}, {u'content': u'GK8', u'tag': u'd'}, {u'content': u'XY4', u'tag': u'd'}, {u'content': u'YDXCP', u'tag': u'd'}, {u'content': u'BTCTA', u'tag': u'd'}, {u'content': u'LSH', u'tag': u'd'}, {u'content': u'CRU', u'tag': u'd'}, {u'content': u'SJE', u'tag': u'd'}, {u'content': u'Z87', u'tag': u'd'}, {u'content': u'SADPL ', u'tag': u'd'}, {u'content': u'TXBXL', u'tag': u'd'}, {u'content': u'MNW', u'tag': u'd'}, {u'content': u'EYP', u'tag': u'd'}, {u'content': u'CTN', u'tag': u'd'}, {u'content': u'TnLvILS', u'tag': u'd'}]},
            {u'marcTag': u'996', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'(OCoLC)47947275', u'tag': u'a'}, {u'content': u'(OCoLC)81149323', u'tag': u'z'}]},
            {u'marcTag': u'908', u'ind1': u' ', u'ind2': u'4', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'PR6068.O94', u'tag': u'a'}, {u'content': u'H27 2001', u'tag': u'b'}]},
            {u'marcTag': u'908', u'ind1': u'1', u'ind2': u'4', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'PZ7.R79835', u'tag': u'a'}, {u'content': u'Ham 2001 (juv)', u'tag': u'b'}]},
            {u'marcTag': u'901', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'BTCLSD110408A', u'tag': u'a'}]},
            {u'marcTag': u'901', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'vlr', u'tag': u'a'}]},
            {u'marcTag': u'901', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'INGRAM120809C', u'tag': u'a'}]},
            {u'marcTag': u'945', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'.o15621455', u'tag': u'a'}]},
            {u'marcTag': u'901', u'ind1': u' ', u'ind2': u' ', u'content': None, u'fieldTag': u'y', u'subfields': [{u'content': u'rbf', u'tag': u'a'}]},
            {u'marcTag': None, u'ind1': None, u'ind2': None, u'content': u'00000cam  2200637 a 4500', u'fieldTag': u'_', u'subfields': None}],
            u'materialType': {u'code': u'a', u'value': u'BOOK/TEXT'},
            u'locations': [{u'code': u'fwy', u'name': u'Fort Washington Young Adult'}, {u'code': u'tvy', u'name': u'Tottenville Young Adult'}],
            u'standardNumbers': [u'0439136350', u'9780439136358'],
            u'id': u'17409211',
            u'author': u'Rowling, J. K.',
            u'normAuthor': u'rowling j k',
            u'deletedDate': None,
            u'normTitle': u'harry potter and the prisoner of azkaban',
            u'nyplSource': u'sierra-nypl',
            u'deleted': False,
            u'createdDate': u'2008-12-23T14:52:00-05:00',
            u'suppressed': False,
            u'publishYear': 1999,
            u'lang': {u'code': u'eng', u'name': u'English'},
            u'catalogDate': u'2012-08-09',
            u'fixedFields': {u'24': {u'display': u'English', u'value': u'eng', u'label': u'Language'}, u'25': {u'display': None, u'value': u'0', u'label': u'Skip'}, u'26': {u'display': None, u'value': u'multi', u'label': u'Location'}, u'27': {u'display': None, u'value': u'3', u'label': u'COPIES'}, u'31': {u'display': None, u'value': u'a', u'label': u'Bib Code 3'}, u'30': {u'display': u'BOOK/TEXT', u'value': u'a', u'label': u'Material Type'}, u'28': {u'display': None, u'value': u'2012-08-09', u'label': u'Cat. Date'}, u'29': {u'display': u'MONOGRAPH', u'value': u'm', u'label': u'Bib Level'}, u'98': {u'display': None, u'value': u'2016-11-25T16:24:40Z', u'label': u'PDATE'}, u'89': {u'display': u'New York (State)', u'value': u'nyu', u'label': u'Country'}, u'83': {u'display': None, u'value': u'2008-12-23T14:52:00Z', u'label': u'Created Date'}, u'80': {u'display': None, u'value': u'b', u'label': u'Record Type'}, u'81': {u'display': None, u'value': u'17409211', u'label': u'Record Number'}, u'86': {u'display': None, u'value': u'1', u'label': u'Agency'}, u'107': {u'display': None, u'value': u' ', u'label': u'MARC Type'}, u'84': {u'display': None, u'value': u'2016-12-05T19:33:51Z', u'label': u'Updated Date'}, u'85': {u'display': None, u'value': u'1617', u'label': u'No. of Revisions'}},
            u'country': {u'code': u'nyu', u'name': u'New York (State)'},
            u'nyplType': u'bib',
            u'updatedDate': u'2016-12-05T19:33:51-05:00',
            u'title': u'Harry Potter and the prisoner of Azkaban',
            u'bibLevel': {u'code': u'm', u'value': u'MONOGRAPH'}}

    def test_raise_AttribError_if_None(self):
        with self.assertRaises(AttributeError):
            crosswalks.platform2pymarc_obj()

    def test_parsing_leader(self):
        self.assertEqual(
            crosswalks.platform2pymarc_obj(self.data).leader,
            '00000cam  2200637 a 4500')

    def test_parsing_control_fields(self):
        self.assertTrue(
            crosswalks.platform2pymarc_obj(
                self.data).get_fields('001')[0].is_control_field())
        self.assertEqual(
            crosswalks.platform2pymarc_obj(
                self.data).get_fields('001')[0].data,
            u'41266045')

    def test_parsing_varialbe_fields(self):
        self.assertEqual(
            crosswalks.platform2pymarc_obj(
                self.data).get_fields('100')[0].value(),
            'Rowling, J. K.')

    def test_parsing_subfields(self):
        self.assertEqual(
            crosswalks.platform2pymarc_obj(
                self.data).get_fields('091')[0]['c'],
            'ROWLING')

    def test_parsing_indicators(self):
        self.assertEqual(
            crosswalks.platform2pymarc_obj(
                self.data).get_fields('091')[0].indicators,
            [' ', ' '])

    def test_parsing_repeatable_fields(self):
        self.assertEqual(
            len(crosswalks.platform2pymarc_obj(
                self.data).get_fields('901')), 4)


class TestPlatform2Meta(unittest.TestCase):
    """Tests parsing inhouse metadata from Platform's results"""
    def setUp(self):
        self.fh = 'platform_test_res.json'
        data = open(self.fh, 'r')
        self.results = json.load(data)

    def test_if_atttrib_is_None(self):
        with self.assertRaises(AttributeError):
            crosswalks.platform2meta(None)

    def test_returned_type(self):
        self.assertIs(
            type(crosswalks.platform2meta(self.results)), list)

    def test_returnes_correct_qty(self):
        self.assertIs(
            len(crosswalks.platform2meta(self.results)),
            2)

    def test_return_list_obj(self):
        for inst in crosswalks.platform2meta(self.results):
            self.assertIsInstance(
                inst, bibs.InhouseBibMeta)

    def test_correct_data(self):
        m1 = crosswalks.platform2meta(self.results)[0]
        self.assertEqual(
            m1.sierraId, '17409211')
        self.assertEqual(
            m1.catSource, 'vendor')
        self.assertEqual(
            m1.ownLibrary, 'branches')
        self.assertEqual(
            m1.t020, ['0439136350', '9780439136358'])


if __name__ == '__main__':
    unittest.main()
