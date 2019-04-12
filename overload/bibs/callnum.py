from unidecode import unidecode


def is_short(tag_300a):
    # shorter than 50 pages (kind of arbitrary)
    short = False
    if 'volume' in tag_300a or ' v.' in tag_300a:
        # children's picture books are often unpaged and short
        short = True
    else:
        words = tag_300a.split(' ')
        for w in words:
            try:
                w_int = int(w)
                if w_int < 50:
                    short = True
            except TypeError:
                pass
            except ValueError:
                pass
    return short


def is_picture_book(audn_code, tag_300a):
    """
    for reference see https://www.oclc.org/bibformats/en/fixedfield/audn.html
    args:
        audn_code: str, one character MARC21 audience code
        tag_300a: str, value of MARC21 tag 300, subfield $a (extend)
    returns:
        boolean
    """
    if audn_code in ('a', 'b'):
        return True
    elif audn_code == 'j':
        if is_short(tag_300a):
            return True
    else:
        return False


def is_juvenile(audn_code):
    if audn_code in ('a', 'b', 'c', 'j'):
        return True
    else:
        return False


def get_literary_form(leader_string, tag_008):
    rec_type = extract_record_type(leader_string)
    if rec_type == 'a':
        return tag_008[33]
    else:
        return


def is_fiction(leader_string, tag_008):
    code = get_literary_form(leader_string, tag_008)
    if code in ('1', 'f', 'j'):
        return True
    else:
        return False


def get_last_name(name_string):
    """
    isolates last name in a name string extracted from a record
    args:
        name_string: str, entire name
    returns:
        last_name: str, with removed diactritics and in uppper case;
                   may include value of subfield $b
    """
    last_name = name_string.split(',')[0].strip()
    if last_name[-1] == '.':
        last_name = last_name[:-1]

    # remove diacritics & change to upper case
    last_name = unidecode(unicode(last_name)).upper()
    return last_name


def get_first_letter(field_string):
    """
    finds first letter in a field string, removes diacritics and changes
    case to upper
    args:
        field_string: str, marc field value, must not include any articles
    returns:
        first_chr: str, one character in upper case
    """

    return unidecode(unicode(field_string)).upper()
