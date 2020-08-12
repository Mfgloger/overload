# methods for extracting particular data from bibliographic records;
# get methods return value from a field or subfield;
# extract methoths return particular charater in a value string;
# parse methods are more sophisticated, isolating specific elements
# within value string

import re

from unidecode import unidecode


def extract_record_encoding(leader_string=None):
    try:
        return leader_string[9]
    except TypeError:
        return None


def extract_record_lvl(leader_string=None):
    try:
        return leader_string[17]
    except TypeError:
        return None


def extract_record_type(leader_string=None):
    try:
        return leader_string[6]
    except TypeError:
        return None


def get_audience_code(leader_string, tag_008):
    rec_type = extract_record_type(leader_string)
    if rec_type == "a":
        try:
            return tag_008[22]
        except TypeError:
            return None
    else:
        return None


def get_language_code(tag_008=None):
    """
    extracts language code form control field 008
    args:
        tag_008: str, value of MARC field 008
    returns:
        code: str, 3 character long language code
    """
    try:
        return tag_008[35:38]
    except TypeError:
        return None
    except IndexError:
        return None


def get_literary_form(leader_string, tag_008):
    rec_type = extract_record_type(leader_string)
    if rec_type == "a":
        return tag_008[33]
    else:
        return


def has_biography_code(leader_string, tag_008):
    try:
        if leader_string[6] == "a":
            if tag_008[34] in ("a", "b", "d"):
                return True
            else:
                return False
        else:
            False
    except TypeError:
        return False
    except IndexError:
        return False


def is_short(tag_300a):
    # shorter than 50 pages (kind of arbitrary)
    short = False
    try:
        if "volume" in tag_300a or " v." in tag_300a:
            # children's picture books are often unpaged and short
            short = True
        else:
            words = tag_300a.split(" ")
            for w in words:
                try:
                    w_int = int(w)
                    if w_int < 50:
                        short = True
                except TypeError:
                    pass
                except ValueError:
                    pass
    except TypeError:
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
    if audn_code in ("a", "b"):
        return True
    elif audn_code == "j":
        if is_short(tag_300a):
            return True
    else:
        return False


def is_fiction(leader_string, tag_008):
    code = get_literary_form(leader_string, tag_008)
    if code in ("1", "f", "j"):
        return True
    else:
        return False


def is_biography(leader_string, tag_008, subject_fields):
    if has_biography_code(leader_string, tag_008) and "600" in subject_fields:
        return True
    else:
        return False


def is_dewey(leader_string, tag_008):
    try:
        if leader_string[6] == "a" and tag_008[33] in ("0", "d", "e", "h", "i"):
            return True
        else:
            return False
    except TypeError:
        return False
    except IndexError:
        return False


def is_juvenile(audn_code):
    if audn_code in ("a", "b", "c", "j"):
        return True
    else:
        return False


def map_bib_audience_code(leader_string, tag_008):
    bib_code = get_audience_code(leader_string, tag_008)
    if bib_code is None:
        return None
    else:
        if bib_code in (" ", "e", "f", "g"):
            return "a"
        elif bib_code == "d":
            return "y"
        elif bib_code in ("a", "b", "c", "j"):
            return "j"
        else:
            return None


def remove_trailing_zeros(classmark):
    while len(classmark) > 3 and (classmark[-1] == "0" or classmark[-1] == "."):
        classmark = classmark[0:-1]
    return classmark


def parse_dewey(tag_082):
    """
    args:
        tag_082: str, only subfield $a of the tag
    """
    try:
        classmark = tag_082.strip().replace("/", "").replace("j", "")
        if "." in classmark:
            classmark = classmark[:8]
        else:
            if len(classmark) != 3:
                return None
            else:
                classmark = classmark

        classmark = remove_trailing_zeros(classmark)

        return classmark
    except AttributeError:
        return None
    except IndexError:
        return None


def parse_first_letter(field_string):
    """
    Finds first letter in a field string, removes diacritics and changes
    case to upper
    args:
        field_string: str, marc field value, must not include any articles
    returns:
        first_chr: str, one character in upper case
    """
    try:
        field_string = unicode(field_string.strip())
        first_letter = unidecode(field_string)[0].upper()
        if first_letter.isdigit():
            return None
        else:
            return first_letter
    except IndexError:
        return None
    except TypeError:
        return None
    except AttributeError:
        return None


def parse_first_word(field_string):
    """
    returns first word in a string, removes diacritics and changes to upper case
    """
    try:
        field_string = unicode(field_string.strip())
        first_word = unidecode(field_string.split()[0]).upper()
        if first_word.isdigit():
            return None
        else:
            return first_word
    except IndexError:
        return None
    except TypeError:
        return None
    except AttributeError:
        return None


def parse_isbn(field):
    try:
        field = field.replace("-", "")
        p = re.compile(r"^(97[8|9])?\d{9}[\dxX]")

        m = re.search(p, field)
        if m:
            return str(m.group(0))
        else:
            return None
    except AttributeError:
        return None


def parse_issn(field):
    p = re.compile(r"^(\d{4}-\d{3}[\dxX]$)")
    m = re.search(p, field)
    if m:
        return str(m.group(0).replace("-", ""))
    else:
        return None


def parse_language_prefix(tag_008):
    lang = get_language_code(tag_008)
    lang_prefix = None
    if lang == "eng":
        # no lang prefix
        pass
    elif lang == "und":
        # raise as error?
        # not valid
        pass
    elif lang is None:
        # raise error?
        pass
    else:
        lang_prefix = lang.upper()
    return lang_prefix


def parse_last_name(name_string):
    """
    isolates last name in a name string extracted from a record
    args:
        name_string: str, entire name
    returns:
        last_name: str, with removed diactritics and in uppper case;
                   may include value of subfield $b
    """
    try:
        last_name = name_string.split(",")[0].strip()
        if last_name[-1] == ".":
            last_name = last_name[:-1]

        # remove diacritics & change to upper case
        last_name = last_name.strip()
        last_name = unidecode(unicode(last_name)).upper()
        return last_name
    except AttributeError:
        return None
    except IndexError:
        return None


def parse_sierra_id(field):
    try:
        p = re.compile(r"\.b\d{8}.|\.o\d{7}.")

        m = re.match(p, field)
        if m:
            return str(m.group())[2:-1]
        else:
            return None
    except TypeError:
        return None


def parse_upc(field):
    return field.split(" ")[0]


def remove_oclcNo_prefix(oclcNo):
    """
    removes OCLC Number prefix
    for example:
        ocm00012345 => 00012345 (8 digits numbers 1-99999999)
        ocn00012345 => 00012345 (9 digits numbers 100000000 to 999999999)
        on000123456  => 000123456 (10+ digits numbers 1000000000 and higher)
    args:
        oclcNo: str, OCLC Number
    returns:
        oclcNo: str, OCLC without any prefix
    """
    oclcNo = oclcNo.strip()
    if "ocm" in oclcNo or "ocn" in oclcNo:
        return oclcNo[3:]
    elif "on" in oclcNo:
        return oclcNo[2:]
    else:
        return oclcNo
