# module general call number rules
from pymarc import Field
from parsers import (parse_last_name, parse_first_letter,
                     parse_language_prefix,
                     is_picture_book, is_juvenile,
                     get_audience_code)


def remove_special_characters(data):
    """
    this may need to be more sophistacated than below...
    """
    data = data.replace('-', ' ')
    data = data.replace("'", '')
    data = data.replace('`', '')
    return data


def create_nypl_fiction_callnum(
        leader_string, tag_008, tag_300a, cuttering_fields):
    """
    creates pymarc Field with NYPL Branch call number
    args:
        leader_string: str, MARC record leader
        tag_008: str, MARC control field 008
        tag_300a, str, MARC data field 300 subfield "a"
        cuttering_fields: dict, cuttering fields options created by
                          bibs.xml_bibs.get_cuttering_fields
    returns:
        field: pymarc Field object, 091 MARC field with a
               full fiction call number
    """

    lang_prefix = parse_language_prefix(tag_008)
    audn_code = get_audience_code(leader_string, tag_008)

    # main entry cutter
    cutter = None
    if '100' in cuttering_fields:
        # use last name
        cutter = parse_last_name(cuttering_fields['100'])
        cutter = remove_special_characters(cutter)
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
