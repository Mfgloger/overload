# module general call number rules
from pymarc import Field


from parsers import (
    parse_first_letter,
    parse_first_word,
    parse_dewey,
    parse_language_prefix,
    parse_last_name,
    is_biography,
    is_dewey,
    is_picture_book,
    is_juvenile,
    is_fiction,
    get_audience_code,
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


def is_adult_division(locations):
    """Checks if any of the locations is Central's adult division"""

    if locations is None:
        return False

    if "03" in locations:
        return True
    elif "04" in locations:
        return True
    elif "11" in locations:
        return True
    elif "12" in locations:
        return True
    elif "13" in locations:
        return True
    elif "14" in locations:
        return True
    elif "16" in locations:
        return True
    elif "17" in locations:
        return True


def has_division_conflict(classmark, audience, locations):
    """
    Verifies if there are Dewey range conflicts and Central Lib. location
    args:
        classmark: str,     Dewey classification
        location: str,      order locations
        audn, str,          audience code
    returns:
        boolean
    """

    if classmark is None:
        return True

    if locations is None:
        return False

    main_class = classmark[0]
    digit_2nd = classmark[1]
    digit_3rd = classmark[2]

    # AAMS (11)
    if "11" in locations:
        # temporarily do not process 7xx
        # complex issue that needs to be tackled
        # with care
        return True

    # HBR (13)
    if "13" in locations:
        if main_class not in ("2", "9"):
            return True

    # Language & Literature (14)
    if "14" in locations:
        if main_class not in ("0", "4", "8"):
            return True
        else:
            if main_class == "0":
                if digit_2nd == "4":
                    return True
                if digit_2nd == "0":
                    if digit_3rd in ("0", "4", "5", "6", "7", "8", "9"):
                        return True
            elif main_class == "8":
                # temporarily do not process 8xx
                # complex issue that needs to be tackled
                # with care
                return True

    # Social Studies (16)
    if "16" in locations:
        if main_class not in ("0", "1", "3", "5", "6"):
            return True
        else:
            if main_class == "0":
                if digit_2nd != "0":
                    return True
                else:
                    if digit_3rd not in ("4", "5", "6"):
                        return True
            elif main_class == "3":
                if digit_2nd == "9" and digit_3rd == "1":
                    return True

    # audience check
    if audience is None:
        return False
    else:
        if "02" in locations:
            if audience != "j":
                return True
        else:
            if audience == "j" and is_adult_division(locations):
                return True

    return False


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


def create_bpl_callnum(
    leader_string,
    tag_008,
    tag_082,
    tag_300a,
    cuttering_fields,
    subject_fields,
    order_data,
):
    """
    creates pymarc Field with BPL Branch call number
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
    vetted_audn = valid_audience(leader_string, tag_008, order_data.audnType)

    # construct call number field
    subfields = []
    field = None
    if order_data:
        if not order_data.ord_conflicts:

            if lang_prefix and order_data.wlPrefix:
                subfields.extend(["a", lang_prefix])

            # picture book & easy readers call numbers
            if is_picture_book(audn_code, tag_300a) and order_data.callType in (
                "pic",
                "eas",
                "neu",
            ):
                subfields.extend(["a", "J-E"])
                if "100" in cuttering_fields:
                    cutter = determine_cutter(cuttering_fields, cutter_type="last_name")
                    subfields.extend(["a", cutter])
                else:
                    # title entry has only J-E
                    pass
            # juvenile call numbers
            elif is_juvenile(audn_code) and order_data.audnType in (None, "j"):
                subfields.extend(["a", "J"])

            # fiction call numbers
            if (
                is_fiction(leader_string, tag_008)
                and order_data.callType in ("neu", "fic")
                and not is_picture_book(audn_code, tag_300a)
            ):
                if "100" in cuttering_fields:
                    cutter = determine_cutter(cuttering_fields, cutter_type="last_name")
                else:
                    cutter = determine_cutter(
                        cuttering_fields, cutter_type="first_letter"
                    )
                if cutter:
                    subfields.extend(["a", "FIC", "a", cutter])

            # biography call numbers
            elif is_biography(
                leader_string, tag_008, subject_fields
            ) and order_data.callType in ("neu", "bio",):
                biographee = determine_biographee_name(subject_fields)
                cutter = determine_cutter(cuttering_fields, cutter_type="first_letter")
                if biographee is not None and cutter is not None:
                    subfields.extend(["a", "B", "a", biographee, "a", cutter])

            # non-fic call numbers
            elif is_dewey(leader_string, tag_008) and order_data.callType in (
                "neu",
                "dew",
            ):
                classmark = parse_dewey(tag_082)
                division_conflict = has_division_conflict(
                    classmark, vetted_audn, order_data.locs
                )
                # print(division_conflict)
                cutter = determine_cutter(cuttering_fields, cutter_type="first_letter")
                if (
                    not division_conflict
                    and cutter is not None
                    and vetted_audn is not False
                ):
                    subfields.extend(["a", classmark, "a", cutter])

        else:
            # skip bibs with order conflicts
            pass

    else:
        raise Exception("not implemented")
        # if lang_prefix:
        #     subfields.extend(["a", lang_prefix])

        # if is_picture_book(audn_code, tag_300a):
        #     subfields.extend(["a", "J-E"])
        #     subfields.extend(["a", cutter])
        # elif is_juvenile(audn_code):
        #     subfields.extend(["a", "J"])

        # # add condition for fic, non-fic, bio based on the bibliographic record
        # # alone
        # else:
        #     subfields.extend(["a", "FIC", "a", cutter])

    if subfields:
        field = Field(tag="099", indicators=[" ", " "], subfields=subfields)
        return field
    else:
        return None
