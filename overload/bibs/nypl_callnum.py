# module encodes NYPL call number rules
from pymarc import Field
from unidecode import unidecode

# namespaces
NS = {'marc': 'http://www.loc.gov/MARC21/slim'}


def create_nypl_fiction_callnum(marcxml, lang):
    """
    instead of marcxml use data from 100, 110, 111, 130?, and 245
    this will make testing easier
    """
    # langugage prefix
    lang_prefix = None
    if lang == 'eng':
        # no lang prefix
        pass
    elif lang == 'und':
        # raise as error?
        # not valid
        pass
    else:
        lang_prefix = lang.upper()

    # main entry cutter
    cutter = None
    for field in marcxml.findall('marc:datafield', NS):
        if field.attrib['tag'] == '100':
            for subfield in field.findall('marc:subfield', NS):
                if subfield.attrib['code'] == 'a':
                    cutter = subfield.text.split(',')[0].strip()
                    if cutter[-1] == '.':
                        cutter = cutter[:-1].strip()
                    cutter = unidecode(unicode(cutter)).upper()
                    break
    if not cutter:
        for field in marcxml.findall('marc:datafield', NS):
            if field.attrib['tag'] == '245':
                skip_chr = field.attrib['ind2'].strip()
                if skip_chr:
                    skip_chr = int(skip_chr)
                else:
                    skip_chr = 0
                for subfield in field.findall('marc:subfield', NS):
                    if subfield.attrib['code'] == 'a':
                        cutter = subfield.text[skip_chr:].strip()[0]
                        cutter = unidecode(unicode(cutter)).upper()
                        break
    # construct call number field
    subfields = []
    if lang_prefix:
        subfields.extend(['p', lang_prefix])
    subfields.extend(['a', 'FIC'])
    if cutter:
        subfields.extend(['c', cutter])

    return Field(tag='091', indicators=[' ', ' '], subfields=subfields)
