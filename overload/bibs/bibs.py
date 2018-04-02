# general tools to read, parse, and write MARC files

from pymarc import MARCReader, JSONReader, MARCWriter
import re
from datetime import datetime


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


def read_marc21(file):
    reader = MARCReader(open(file, 'r'), hide_utf8_warnings=True)
    return reader


def write_marc21(outfile, bib):
    try:
        writer = MARCWriter(open(outfile, 'a'))
        writer.write(bib)
    except WindowsError:
        raise WindowsError
    finally:
        writer.close()


def read_marc_in_json(data):
    reader = JSONReader(data)
    return reader


class BibMeta:
    """
    creates a general record meta object
    args:
        bib obj (pymarc)
        sierraId str
    """
    def __init__(self, bib, sierraId=None):
        self.t001 = None
        self.t003 = None
        self.t005 = None
        self.t020 = []
        self.t022 = []
        self.t024 = []
        self.t028 = []
        self.t901 = []
        self.t947 = []
        self.sierraId = sierraId
        self.bCallNumber = None
        self.rCallNumber = []

        # parse 001 field (control field)
        if '001' in bib:
            self.t001 = bib['001'].data

        # parse 003 field (control number identifier)
        if '003' in bib:
            self.t003 = bib['003'].data

        # parse 005 field (version date)
        if '005' in bib:
            try:
                self.t005 = datetime.strptime(
                    bib['005'].data,
                    '%Y%m%d%H%M%S.%f')
            except ValueError:
                pass

        for field in bib.get_fields('020'):
            for subfield in field.get_subfields('a'):
                self.t020.append(parse_isbn(subfield))

        for field in bib.get_fields('022'):
            for subfield in field.get_subfields('a'):
                self.t022.append(parse_issn(subfield))

        for field in bib.get_fields('024'):
            for subfield in field.get_subfields('a'):
                self.t024.append(
                    parse_upc(subfield))

        for field in bib.get_fields('028'):
            for subfield in field.get_subfields('a'):
                self.t028.append(
                    parse_upc(subfield))

        for field in bib.get_fields('901'):
            self.t901.append(field.value())

        for field in bib.get_fields('947'):
            self.t947.append(field.value())

        # parse Sierra number
        if self.sierraId is None:
            if '907' in bib:
                self.sierraId = parse_sierra_id(
                    bib.get_fields('907')[0].value())
            elif '945' in bib:
                self.sierraId = parse_sierra_id(
                    bib.get_fields('945')[0].value())

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
        return "<BibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, 024:{}, " \
            "028:{}, 901:{}, 947:{}, sierraId:{}, " \
            "bCallNumber:{}, rCallNumber:{})>".format(
                self.t001,
                self.t003,
                self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.t901,
                self.t947,
                self.sierraId,
                self.bCallNumber,
                self.rCallNumber)


class VendorBibMeta(BibMeta):
    """
    Implements vendor specific bib metatada
    args:
        bib (pymarc obj)
        vendor str
        dstLibrary str ('research' or 'branches')
    """
    def __init__(self, bib, vendor=None, dstLibrary=None):
        BibMeta.__init__(self, bib)
        self.vendor = vendor
        self.dstLibrary = dstLibrary
        self.action = 'attach'

    def __repr__(self):
        return "<VendorBibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, " \
            "024:{}, 028:{}, 901:{}, 947:{}, " \
            "sierraId:{}, bCallNumber:{}, rCallNumber:{}, " \
            "vendor:{}, dstLibrary:{}, action:{})>".format(
                self.t001,
                self.t003,
                self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.t901,
                self.t947,
                self.sierraId,
                self.bCallNumber,
                self.rCallNumber,
                self.vendor,
                self.dstLibrary,
                self.action)


class InhouseBibMeta(BibMeta):
    """
    Implements inhouse specific bib metadata
    args:
        bib obj (pymarc)
        sierraId str
        location list
    """

    def __init__(self, bib, sierraId=None, locations=[]):
        BibMeta.__init__(self, bib)
        self.sierraId = sierraId
        self.catSource = 'vendor'
        self.ownLibrary = None

        # source of cataloging
        # check 049 code to determine library
        if '049' in bib:
            field = bib.get_fields('049')[0]['a']
            if 'BKLA' in field:  # BPL
                if self.t001 is not None:
                    if self.t001[0] == 'o' and self.t003 == 'OCoLC':
                        self.catSource = 'inhouse'
            elif 'NYPP' in field:  # NYPL
                if '901' in bib:
                    fields = bib.get_fields('901')
                    for field in fields:
                        subfield = field['b'][0]
                        if 'CAT' in subfield:
                            self.catSource = 'inhouse'
                            break

        # owning library
        # for nypl check also locations
        bl = False
        rl = False
        # brief order record scenario
        if 'zzzzz' in locations:
            bl = True
        if 'xxx' in locations:
            rl = True
        # full bib scenario
        if self.ownLibrary is None:
            if '091' in bib or '099' in bib:
                bl = True
            if '852' in bib:
                for field in bib.get_fields('852'):
                    if field.indicators[0] == '8':
                        rl = True
                        break

        if bl and not rl:
            self.ownLibrary = 'branches'
        elif bl and rl:
            self.ownLibrary = 'mixed'
        elif not bl and rl:
            self.ownLibrary = 'research'

    def __repr__(self):
        return "<VendorBibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, " \
            "024:{}, 028:{}, 901:{}, 947:{}, " \
            "sierraId:{}, bCallNumber:{}, rCallNumber:{}, " \
            "catSource:{}, ownLibrary:{})>".format(
                self.t001,
                self.t003,
                self.t005,
                self.t020,
                self.t022,
                self.t024,
                self.t028,
                self.t901,
                self.t947,
                self.sierraId,
                self.bCallNumber,
                self.rCallNumber,
                self.catSource,
                self.ownLibrary)
