from bibs.xml_bibs import (NS, extract_record_type, get_literary_form,
    get_record_leader, get_tag_008, get_datafield_040, get_cat_lang,
    extract_record_lvl)


def is_fiction(marcxml):
    leader = get_record_leader(marcxml)
    tag_008 = get_tag_008(marcxml)
    code = get_literary_form(leader, tag_008)
    if code in ('1', 'f', 'j'):
        return True
    else:
        return False


def is_english_cataloging(marcxml):
    """
    args:
        marcxml
    """
    field = get_datafield_040(marcxml)
    code = get_cat_lang(field)
    if not code or code == 'eng':
        return True
    else:
        return False


def create_rec_lvl_range(rec_lvl):
    """
    gui values:
        'Level 1 - blank, I, 4 ',
        'Level 2 & up - M, K, 7, 1, 2',
        'Level 3 & up - 3, 8'
    """
    default = [' ', 'I', '4']
    try:
        lvl = rec_lvl[6]
        if lvl == '1':
            return default
        elif lvl == '2':
            default.extend(['M', 'K', '7', '1', '2'])
            return default
        elif lvl == '3':
            default.extend(['M', 'K', '7', '1', '2', '3', '8'])
            return default
    except IndexError:
        return default
    except TypeError:
        return default


def meets_rec_lvl(marcxml, rec_lvl_range):
    leader_string = get_record_leader(marcxml)
    match_lvl = extract_record_lvl(leader_string)
    if match_lvl in rec_lvl_range:
        return True
    else:
        return False


def meets_user_criteria(marcxml, rec_lvl, rec_type='any',
                        cat_rules='any', cat_source='any'):
    """
    verifies if record meets all criteria set by a user
    args:
        marcxml: xml
        rec_lvl: str,
    """

    rec_lvl_range = create_rec_lvl_range(rec_lvl)
    if meets_rec_lvl(marcxml, rec_lvl_range):
        return True
    else:
        return False


    # add the rest of criteria here
    # rec type
    # cat rules
    # cat source


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

    # print materials and fiction only

    if is_fiction(marcxml) and is_english_cataloging(marcxml):
        return True
    else:
        return False
