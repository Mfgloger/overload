from parsers import (
    parse_first_letter,
    parse_first_word,
    parse_last_name,
    map_bib_audience_code,
)


def determine_cutter(cuttering_fields, cutter_type):
    """
    args:
        cuttering_fields: dict,     dictionary of MARC fields to
                                    be used for a cutter;
                                    key = MARC tag, value = tag value
        cutter_type: str,           options:
                                        - last_name
                                        - first_letter
                                        - first_word
    """
    # main entry to be used for the cutter
    if "100" in cuttering_fields:
        main_entry = cuttering_fields["100"]
    elif "110" in cuttering_fields:
        main_entry = cuttering_fields["110"]
    elif "111" in cuttering_fields:
        main_entry = cuttering_fields["111"]
    elif "245" in cuttering_fields:
        main_entry = cuttering_fields["245"]
    else:
        main_entry = None

    # cutter
    if cutter_type == "last_name":
        cutter = parse_last_name(main_entry)
    elif cutter_type == "first_letter":
        cutter = parse_first_letter(main_entry)
    elif cutter_type == "first_word":
        cutter = parse_first_word(main_entry)
    else:
        cutter = None

    return cutter


def determine_biographee_name(subject_fields):
    try:
        name = parse_last_name(subject_fields["600"])
        return name
    except KeyError:
        return None
    except TypeError:
        return None


def valid_audience(leader_string, tag_008, order_audn_code):
    """Vets bib and order audience codes to find any conflicts"""

    bib_audn_code = map_bib_audience_code(leader_string, tag_008)

    if bib_audn_code is None:
        return order_audn_code
    else:
        if order_audn_code is None:
            return bib_audn_code
        elif order_audn_code == "y" and bib_audn_code in ("j", "y"):
            return "y"
        elif order_audn_code == "y" and bib_audn_code == "a":
            return "a"
        else:
            if order_audn_code != bib_audn_code:
                return False
            else:
                return order_audn_code
