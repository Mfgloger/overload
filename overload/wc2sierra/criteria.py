from bibs.xml_bibs import (get_record_leader, get_datafield_040,
                           get_cat_lang, get_tag_005, get_tag_008,
                           get_tags_041a,
                           get_tag_300a, get_tags_347b, get_tags_538a)
from bibs.parsers import (extract_record_lvl, is_picture_book, is_fiction,
                          get_audience_code)


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


def meets_mat_type(marcxml, mat_type='any'):
    """
    args:
        marcxml: xml obj, MARC record encodeded in XML
        mat_type: str, options: any, print, large print, dvd, bluray
    returns:
        Boolean: marcxml corresponds to indicated mat_type or not
    """

    meets = True
    if mat_type == 'any':
        return meets
    else:
        leader_string = get_record_leader(marcxml)
        t008 = get_tag_008(marcxml)
        if mat_type == 'print':
            if leader_string[6] != 'a':
                meets = False
            else:
                if t008[23] != ' ':
                    meets = False
        elif mat_type == 'large print':
            if leader_string[6] != 'a':
                meets = False
            else:
                if t008[23] != 'd':
                    meets = False
        elif mat_type == 'dvd':
            t347s = get_tags_347b(marcxml)
            t538s = get_tags_538a(marcxml)
            if leader_string[6] != 'g':
                meets = False
            else:
                found = False
                for s in t347s:
                    if 'DVD' in s:
                        found = True
                for s in t538s:
                    if 'DVD' in s:
                        found = True
                if not found:
                    meets = False
        elif mat_type == 'bluray':
            t347s = get_tags_347b(marcxml)
            t538s = get_tags_538a(marcxml)
            if leader_string[6] != 'g':
                meets = False
            else:
                found = False
                for s in t347s:
                    if 'Blu-ray' in s:
                        found = True
                for s in t538s:
                    if 'Blu-ray' in s:
                        found = True
                if not found:
                    meets = False
        else:
            raise AttributeError('Invalid mat_type attribute has been passed')

    return meets


def passes_language_test(t008, t041s):
    """
    Checks if data in 008 and 041$a fulfills Recap language test
    args:
        t008: str, value of 008 MARC tag
        t041s: list, list of language codes found in 041 $a
    returns:
        Boolean: True if applicable for Recap, False if not
    """
    if t041s is None:
        t041s = []

    passes = True
    langs = set()
    langs.add(t008[35:38])
    for code in t041s:
        langs.add(code)

    if 'eng' in langs:
        # multilanguge materials and English are not to be
        # sent to Recap
        passes = False

    return passes


def meets_user_criteria(marcxml, rec_lvl, mat_type='any',
                        cat_rules='any', cat_source='any'):
    """
    verifies if record meets all criteria set by a user
    args:
        marcxml: xml
        rec_lvl: str,
    """
    # add the rest of criteria here
    # cat rules
    # cat source

    meets = True
    rec_lvl_range = create_rec_lvl_range(rec_lvl)
    if not meets_rec_lvl(marcxml, rec_lvl_range):
        meets = False

    if not meets_mat_type(marcxml, mat_type):
        meets = False

    return meets


def meets_upgrade_criteria(marcxml, local_timestamp=None):
    """
    Validates bibliographic record meets upgrade criteria
    args:
        marcxml: xml, bibliographic record in MARCXML format
    returns:
        Boolean
    """

    if is_english_cataloging(marcxml):
        if local_timestamp:
            # compare
            wc_timestamp = float(get_tag_005(marcxml))
            if float(local_timestamp) < wc_timestamp:
                # worldcat record has been updated
                return True
            else:
                return False
        else:
            return True
    else:
        return False


def meets_catalog_criteria(marcxml, library):
    """
    sets criteria for Worldcat records to be fully cataloged;
    at the moment records we will process only print fiction
    materials, records must follow anglo-american cataloging
    rules (040$b blank or eng)
    args:
        marcxml: xml, record in MARCXML format
    returns:
        Boolean
    """

    # BL print materials and fiction, and RL Recap only
    leader_string = get_record_leader(marcxml)
    tag_008 = get_tag_008(marcxml)
    audn_code = get_audience_code(leader_string, tag_008)
    t041s = get_tags_041a(marcxml)
    tag_300a = get_tag_300a(marcxml)

    if library == 'branches':
        if is_fiction(leader_string, tag_008) or \
                is_picture_book(audn_code, tag_300a):
            return True
        else:
            return False
    elif library == 'research':
        if is_english_cataloging(marcxml) and \
                passes_language_test(tag_008, t041s):
            return True
    else:
        raise AttributeError('Incorrect ')
