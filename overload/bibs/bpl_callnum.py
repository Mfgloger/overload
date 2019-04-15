# module general call number rules
from pymarc import Field


from parsers import (parse_last_name, parse_first_letter,
                     parse_language_prefix,
                     is_picture_book, is_juvenile,
                     get_audience_code)


def create_bpl_fiction_callnum(
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
    elif '110' in cuttering_fields:
        cutter = parse_first_letter(cuttering_fields['110'])
    elif '111' in cuttering_fields:
        cutter = parse_first_letter(cuttering_fields['111'])
    else:
        cutter = parse_first_letter(cuttering_fields['245'])

    # construct call number field
    subfields = []
    field = None
    if lang_prefix:
        subfields.extend(['a', lang_prefix])
    if is_picture_book(audn_code, tag_300a):
        subfields.extend(['a', 'J-E'])
        subfields.extend(['a', cutter])
    elif is_juvenile:
        subfields.extend(['a', 'J', 'a' 'FIC', 'a', cutter])
    else:
        subfields.extend(['a', 'FIC', 'a', cutter])

    field = Field(tag='099', indicators=[' ', ' '], subfields=subfields)
    print(subfields)
    return field
