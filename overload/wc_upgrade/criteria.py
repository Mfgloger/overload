from bibs.xml_bibs import (NS, extract_record_type, get_literary_form,
    get_record_leader, get_tag_008)


def is_fiction(marcxml):
    leader = get_record_leader(marcxml)
    tag_008 = get_tag_008(marcxml)
    code = get_literary_form(leader, tag_008)
    if code in ('1', 'f', 'j'):
        return True
    else:
        return False


def is_eng_cataloging(marcxml):
    """
    args:
        marcxml
    """
    pass


def meets_user_criteria(marcxml, rec_lvl='level3', rec_type='any',
                        cat_rules='any', cat_source='any'):
    pass


def meets_global_criteria(marcxml):
    """
    sets global criteria for accepted Worldcat records;
    at the moment records we will process only print fiction
    materials, records must follow anglo-american cataloging
    rules (040$b blank or eng)
    args:
        marcxml: xml, record in MARCXML format
    returns:
        Boolean
    """
    failed = False

    # print materials and fiction only

    if not is_fiction(marcxml):
        failed = True

    for field in marcxml.findall('marc:datafield', NS):
        if field.attrib['tag'] == '040':
            for subfield in field.findall('marc:subfield', NS):
                if subfield.attrib['code'] == 'b':
                    code = subfield.text.strip()
                    if not code or code == 'eng':
                        pass
                    else:
                        failed = True

    return failed
