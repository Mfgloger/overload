# module general call number rules
from pymarc import Field


from parsers import (
    parse_last_name,
    parse_first_letter,
    parse_first_word,
    parse_language_prefix,
    is_biography,
    is_dewey,
    is_picture_book,
    is_juvenile,
    is_fiction,
    get_audience_code,
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

    # construct call number field
    subfields = []
    field = None
    if order_data:
        if not order_data.ord_conflicts:

            if lang_prefix and order_data.wlPrefix:
                subfields.extend(["a", lang_prefix])

            # picture book call numbers
            if is_picture_book(audn_code, tag_300a) and order_data.callType in (
                "pic",
                "neu",
            ):
                subfields.extend(["a", "J-E"])
                if "100" in cuttering_fields:
                    cutter = determine_cutter(cuttering_fields, cutter_type="last_name")
                    subfields.extend(["a", cutter])
                else:
                    # title entry has only J-E
                    pass

            elif is_juvenile(audn_code) and order_data.audnType in (None, "j"):
                subfields.extend(["a", "J"])

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

            elif is_biography(
                leader_string, tag_008, subject_fields
            ) and order_data.callType in ("neu", "bio",):
                biographee = determine_biographee_name(subject_fields)
                cutter = determine_cutter(cuttering_fields, cutter_type="first_letter")
                if biographee is not None and cutter is not None:
                    subfields.extend(["a", "B", "a", biographee, "a", cutter])
            elif is_dewey(tag_008, tag_082) and order_data.callType in ("neu", "dew"):
                pass

        elif not order_data.ord_conflicts:
            # non-fiction
            pass
        else:
            # skip bibs with order conflicts
            pass

    else:
        raise Exception("not implemented")
        if lang_prefix:
            subfields.extend(["a", lang_prefix])

        if is_picture_book(audn_code, tag_300a):
            subfields.extend(["a", "J-E"])
            subfields.extend(["a", cutter])
        elif is_juvenile(audn_code):
            subfields.extend(["a", "J"])

        # add condition for fic, non-fic, bio based on the bibliographic record
        # alone
        else:
            subfields.extend(["a", "FIC", "a", cutter])

    if subfields:
        field = Field(tag="099", indicators=[" ", " "], subfields=subfields)
        return field
    else:
        return None
