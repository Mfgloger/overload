# module encodes NYPL call number rules
from pymarc import Field


from callnum import get_last_name, get_first_letter
from xml_bibs import get_literary_form

# namespaces
NS = {'marc': 'http://www.loc.gov/MARC21/slim'}



def create_nypl_fiction_callnum(lang, cuttering_fields):
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
    if '100' in cuttering_fields:
        # use last name
        cutter = get_last_name(cuttering_fields['100'])
    elif '110' in cuttering_fields:
        cutter = get_first_letter(cuttering_fields['110'])
    elif '111' in cuttering_fields:
        cutter = get_first_letter(cuttering_fields['111'])
    else:
        cutter = get_first_letter(cuttering_fields['245'])

    # construct call number field
    subfields = []
    field = None
    if lang_prefix:
        subfields.extend(['p', lang_prefix])
    subfields.extend(['a', 'FIC'])
    if cutter:
        subfields.extend(['c', cutter])
        field = Field(tag='091', indicators=[' ', ' '], subfields=subfields)

    return field
