# general tools to read, parse, and write MARC files

from pymarc import MARCReader
import re
from datetime import datetime
import logging


def parse_isbn(field):
    field = field.replace('-', '')
    p = re.compile(r'^(97[8|9])?\d{9}[\dxX]')

    m = re.search(p, field)
    if m:
        return str(m.group(0))
    else:
        return None


def parse_issn(field):
    p = re.compile(r'^(\d{4}-\d{3}[\dxX]$)')
    m = re.search(p, field)
    if m:
        return str(m.group(0))
    else:
        return None


def parse_upc(field):
    return field.split(' ')[0]


def parse_sierra_id(field):
    p = re.compile(r'\.b\d{8}.|\.o\d{7}.')

    m = re.match(p, field)
    if m:
        return str(m.group())[2:-1]
    else:
        return None


def read_from_marc_file(file):
    module_logger = logging.getLogger('main.bibs')
    module_logger.debug('creating pymarc MARCReader for file ({})'.format(
        file))
    reader = MARCReader(open(file, 'r'), hide_utf8_warnings=True)
    return reader


class BibMeta:
    """creates record meta objects"""
    def __init__(self, bib, sierraID=None):
        self.t001 = None
        self.t005 = None
        self.t020 = []
        self.t022 = []
        self.t024 = []
        self.t028 = []
        self.sierraID = sierraID
        self.bCallNumber = None
        self.rCallNumber = []

        # parse 001 field (control field)
        if '001' in bib:
            self.t001 = bib['001'].data
        # parse 005 field (version date)
        if '005' in bib:
            try:
                self.t005 = datetime.strptime(
                    bib['005'].data,
                    '%Y%m%d%H%M%S.%f')
            except ValueError:
                pass
        if '020' in bib:
            for field in bib.get_fields('020'):
                for subfield in field.get_subfields('a'):
                    self.t020.append(parse_isbn(subfield))
        if '022' in bib:
            for field in bib.get_fields('022'):
                for subfield in field.get_subfields('a'):
                    self.t022.append(parse_issn(subfield))
        if '024' in bib:
            for field in bib.get_fields('024'):
                for subfield in field.get_subfields('a'):
                    self.t024.append(
                        parse_upc(subfield))
        if '028' in bib:
            for field in bib.get_fields('028'):
                for subfield in field.get_subfields('a'):
                    self.t028.append(
                        parse_upc(subfield))

        # parse Sierra number
        if self.sierraID is None:
            if '907' in bib:
                self.sierraID = parse_sierra_id(
                    bib.get_fields('907')[0].value())
            elif '947' in bib:
                self.sierraID = parse_sierra_id(
                    bib.get_field('945')[0].value())

        # parse branches call number
        if '099' in bib:
            self.bCallNumber = bib.get_fields('099')[0].value()
        elif '091' in bib:
            self.bCallNumber = bib.get_fields('091')[0].value()

        # parese research call numbers
        if '852' in bib:
            for field in bib.get_fields('852'):
                if field.indicators[0] == '8':
                    self.rCallNumber.append(
                        field.value())

    def __repr__(self):
        return "<BibMeta(001:{}, 005:{}, 020:{}, 022:{}, 024:{}, 028:{}, " \
            "sierraID:{}, bCallNumber:{}, rCallNumber:{})>".format(
                self.t001, self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.sierraID,
                self.bCallNumber,
                self.rCallNumber)


if __name__ == "__main__":
    reader = read_from_marc_file(
        'C:/Users/tomaszkalata/scripts/test_files/NYPL_CATS-SERIES.mrc')
    from pvf.pvf_bibs import InhouseBibMeta
    for bib in reader:
        # bm = BibMeta(bib)
        # print(bm.t001, bm.t005, bm.t020, bm.t022, bm.t024, bm.title, bm.bCallNumber, bm.rCallNumber)
    
        vm = InhouseBibMeta(bib)
        print vm