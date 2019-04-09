from unidecode import unidecode


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
