# module encodes NYPL call number rules
from pymarc import Field


from parsers import (parse_last_name, parse_first_letter,
                     is_picture_book, is_juvenile, get_language_code,
                     get_audience_code)
# namespaces
NS = {'marc': 'http://www.loc.gov/MARC21/slim'}


def create_nypl_fiction_callnum(
        leader_string, tag_008, tag_300a, cuttering_fields):
    """
    creates pymarc Field with NYPL Branch call number
    args:
        lang: str, 3 character MARC language code
        cuttering_fields: dict, cuttering fields options created by
                          bibs.xml_bibs.get_cuttering_fields
    returns:
        field: pymarc Field object, 091 MARC field with a
               full fiction call number
    """

    # langugage prefix
    lang = get_language_code(tag_008)
    lang_prefix = None
    if lang == 'eng':
        # no lang prefix
        pass
    elif lang == 'und':
        # raise as error?
        # not valid
        pass
    elif lang is None:
        # raise error?
        pass
    else:
        lang_prefix = lang.upper()

    # audience
    audn_code = get_audience_code(leader_string, tag_008)

    # main entry cutter
    cutter = None
    if '100' in cuttering_fields:
        # use last name
        cutter = parse_last_name(cuttering_fields['100'])
    elif '110' in cuttering_fields:
        cutter = parse_first_letter(cuttering_fields['110'])
    elif '111' in cuttering_fields:
        cutter = parse_first_letter(cuttering_fields['111'])
    else:
        cutter = parse_first_letter(cuttering_fields['245'])

    # construct call number field
    subfields = []
    subfield_p_values = []
    field = None
    if is_juvenile(audn_code):
        subfield_p_values.append('J')
    if lang_prefix:
        subfield_p_values.append(lang_prefix)
        subfields.extend(['p', ' '.join(subfield_p_values)])
    if is_picture_book(audn_code, tag_300a):
        subfields.extend(['a', 'PIC'])
    else:
        subfields.extend(['a', 'FIC'])
    if cutter:
        subfields.extend(['c', cutter])
        field = Field(tag='091', indicators=[' ', ' '], subfields=subfields)

    return field
