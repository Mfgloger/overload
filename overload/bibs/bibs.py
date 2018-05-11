# general tools to read, parse, and write MARC files

from pymarc import MARCReader, JSONReader, MARCWriter, Field
from pymarc.exceptions import RecordLengthInvalid
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
    reader = MARCReader(
        open(file, 'r'),
        to_unicode=True, hide_utf8_warnings=True)
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


def create_target_id_field(system, bNumber):
    if len(bNumber) != 8:
        raise ValueError(
            'incorrect Sierra bib number encountered '
            'while creating target id field')
    bNumber = '.b{}a'.format(bNumber)
    if system == 'bpl':
        return Field(
            tag='907',
            indicators=[' ', ' '],
            subfields=['a', bNumber])
    if system == 'nypl':
        return Field(
            tag='945',
            indicators=[' ', ' '],
            subfields=['a', bNumber])


def check_sierra_id_presence(system, bib):
    found = False
    if system == 'nypl':
        if '945' in bib:
            found = True
    elif system == 'bpl':
        if '907' in bib:
            found = True
    return found


def check_sierra_format_tag_presence(bib):
    found = False
    try:
        if '949' in bib:
            for field in bib.get_fields('949'):
                if field.indicators == [' ', ' '] \
                        and 'a' in field and \
                        field['a'][0] == '*':
                    found = True
                    break
    except IndexError:
        raise IndexError('Encountered IndexError in vendor 949$a')
    return found


def create_field_from_template(template):
    if template['ind1'] is None:
        ind1 = ' '
    else:
        ind1 = template['ind1']
    if template['ind2'] is None:
        ind2 = ' '
    else:
        ind2 = template['ind2']
    subfields = []
    [subfields.extend([k, v]) for k, v in template['subfields'].items()]
    field = Field(
        tag=template['tag'],
        indicators=[ind1, ind2],
        subfields=subfields)
    return field


def count_bibs(file):
    reader = read_marc21(file)
    bib_count = 0
    try:
        for bib in reader:
            bib_count += 1
        return bib_count
    except RecordLengthInvalid:
        raise


def db_template_to_960(template, vendor_960):
    """"passed attr must be an instance of NYPLOrderTemplate"""

    # order fixed fields mapping
    try:
        vsub = vendor_960.subfields
        # subfields present on the vendor record
        ven_subs = set([vsub[x] for x in range(0, len(vsub), 2)])

    except AttributeError:
        vsub = []
        ven_subs = set()

    # list of relevalnt to PVR subfields of 960
    pvr_subs = set(
        ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'm',
        'v', 'w', 'x'])

    # find extra subfields to be carried over to the new field
    nsub = []
    diff_subs = ven_subs - pvr_subs
    for s in diff_subs:
        nsub.extend(
            [vsub[vsub.index(s)], vsub[vsub.index(s) + 1]])

    # create list of subfield codes without subfield data as index
    vinx = [vsub[x] if x % 2 == 0 else None for x in range(0, len(vsub))]

    # use template values if provided else use original if exists
    try:
        if template.acqType:
            nsub.extend(['a', template.acqType])
        else:
            nsub.extend([
                'a',
                vsub[vinx.index('a') + 1]])
    except ValueError:
        pass

    try:
        if template.claim:
            nsub.extend(['b', template.claim])
        else:
            nsub.extend([
                'b',
                vsub[vinx.index('b') + 1]])
    except ValueError:
        pass

    try:
        if template.code1:
            nsub.extend(['c', template.code1])
        else:
            nsub.extend([
                'c',
                vsub[vinx.index('c') + 1]])
    except ValueError:
        pass

    try:
        if template.code2:
            nsub.extend(['d', template.code2])
        else:
            nsub.extend([
                'd',
                vsub[vinx.index('d') + 1]])
    except ValueError:
        pass

    try:
        if template.code3:
            nsub.extend(['e', template.code3])
        else:
            nsub.extend([
                'e',
                vsub[vinx.index('e') + 1]])
    except ValueError:
        pass

    try:
        if template.code4:
            nsub.extend(['f', template.code4])
        else:
            nsub.extend([
                'f',
                vsub[vinx.index('f') + 1]])
    except ValueError:
        pass

    try:
        if template.form:
            nsub.extend(['g', template.form])
        else:
            nsub.extend([
                'g',
                vsub[vinx.index('g') + 1]])
    except ValueError:
        pass

    try:
        if template.orderNote:
            nsub.extend(['h', template.orderNote])
        else:
            nsub.extend([
                'h',
                vsub[vinx.index('h') + 1]])
    except ValueError:
        pass

    try:
        if template.orderType:
            nsub.extend(['i', template.orderType])
        else:
            nsub.extend([
                'i',
                vsub[vinx.index('i') + 1]])
    except ValueError:
        pass

    try:
        if template.status:
            nsub.extend(['m', template.status])
        else:
            nsub.extend([
                'm',
                vsub[vinx.index('m') + 1]])
    except ValueError:
        pass

    try:
        if template.vendor:
            nsub.extend(['v', template.vendor])
        else:
            nsub.extend([
                'v',
                vsub[vinx.index('v') + 1]])
    except ValueError:
        pass

    try:
        if template.lang:
            nsub.extend(['w', template.lang])
        else:
            nsub.extend([
                'w',
                vsub[vinx.index('w') + 1]])
    except ValueError:
        pass

    try:
        if template.country:
            nsub.extend(['x', template.country])
        else:
            nsub.extend([
                'x',
                vsub[vinx.index('x') + 1]])
    except ValueError:
        pass

    field = Field(
        tag='960',
        indicators=[' ', ' '],
        subfields=nsub)

    return field


def db_template_to_961(template, vendor_961):
    """combines vendor and template 961 field data in
    a new 961 field
    attrs:
        template (template datastore record),
        vendor_961 (vendor 961 field in form of pymarc object)
    returns:
        None (no data coded in the 961)
        field (pymarc Field object)"""

    # order variable fields
    try:
        vsub = vendor_961.subfields
        # subfields present on the vendor record
        ven_subs = set([vsub[x] for x in range(0, len(vsub), 2)])
    except AttributeError:
        vsub = []
        ven_subs = set()

    # list of relevalnt to PVR subfields of 960
    pvr_subs = set(
        ['a', 'c', 'd', 'e', 'f', 'g', 'i', 'j', 'k', 'l', 'm', 'v'])

    # find extra subfield to be carried over to the new field
    nsub = []
    diff_subs = ven_subs - pvr_subs

    for s in diff_subs:
        nsub.extend(
            [vsub[vsub.index(s)], vsub[vsub.index(s) + 1]])

    # create list of subfield codes without subfield data as index
    vinx = [vsub[x] if x % 2 == 0 else None for x in range(0, len(vsub))]

    # apply from template if provided, else keep the vendor data
    try:
        if template.identity:
            nsub.extend(['a', template.identity])
        else:
            nsub.extend([
                'a',
                vsub[vinx.index('a') + 1]])
    except ValueError:
        pass

    try:
        if template.generalNote:
            nsub.extend(['c', template.generalNote])
        else:
            nsub.extend([
                'c',
                vsub[vinx.index('c') + 1]])
    except ValueError:
        pass

    try:
        if template.internalNote:
            nsub.extend(['d', template.internalNote])
        else:
            nsub.extend([
                'd',
                vsub[vinx.index('d') + 1]])
    except ValueError:
        pass

    try:
        if template.oldOrdNo:
            nsub.extend(['e', template.oldOrdNo])
        else:
            nsub.extend([
                'e',
                vsub[vinx.index('e') + 1]])
    except ValueError:
        pass

    try:
        if template.selector:
            nsub.extend(['f', template.selector])
        else:
            nsub.extend([
                'f',
                vsub[vinx.index('f') + 1]])
    except ValueError:
        pass

    try:
        if template.venAddr:
            nsub.extend(['g', template.venAddr])
        else:
            nsub.extend([
                'g',
                vsub[vinx.index('g') + 1]])
    except ValueError:
        pass

    try:
        if template.venNote:
            nsub.extend(['v', template.venNote])
        else:
            nsub.extend([
                'v',
                vsub[vinx.index('v') + 1]])
    except ValueError:
        pass

    try:
        if template.blanketPO:
            nsub.extend(['m', template.blanketPO])
        else:
            nsub.extend([
                'm',
                vsub[vinx.index('m') + 1]])
    except ValueError:
        pass

    try:
        if template.venTitleNo:
            nsub.extend(['i', template.venTitleNo])
        else:
            nsub.extend([
                'i',
                vsub[vinx.index('i') + 1]])
    except ValueError:
        pass

    try:
        if template.paidNote:
            nsub.extend(['j', template.paidNote])
        else:
            nsub.extend([
                'j',
                vsub[vinx.index('j') + 1]])
    except ValueError:
        pass

    try:
        if template.shipTo:
            nsub.extend(['k', template.shipTo])
        else:
            nsub.extend([
                'k',
                vsub[vinx.index('k') + 1]])
    except ValueError:
        pass

    try:
        if template.requestor:
            nsub.extend(['l', template.requestor])
        else:
            nsub.extend([
                'l',
                vsub[vinx.index('l') + 1]])
    except ValueError:
        pass

    if nsub == []:
        field = None
    else:
        field = Field(
            tag='961',
            indicators=[' ', ' '],
            subfields=nsub)

    return field


def db_template_to_949(mat_format):
    field = Field(
        tag='949',
        indicators=[' ', ' '],
        subfields=['a', '*b2={};'.format(mat_format)])
    return field


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

    def __repr__(self):
        return "<VendorBibMeta(001:{}, 003:{}, 005:{}, 020:{}, 022:{}, " \
            "024:{}, 028:{}, 901:{}, 947:{}, " \
            "sierraId:{}, bCallNumber:{}, rCallNumber:{}, " \
            "vendor:{}, dstLibrary:{})>".format(
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
                self.dstLibrary)


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
                        if 'b' in field:
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
