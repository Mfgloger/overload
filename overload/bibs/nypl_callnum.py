from datetime import date
import json

# module general call number rules
from pymarc import Field


from parsers import (
    parse_last_name,
    parse_first_letter,
    parse_language_prefix,
    is_picture_book,
    is_juvenile,
    get_audience_code,
)


def remove_special_characters(data):
    """
    this may need to be more sophistacated than below...
    """
    data = data.replace("-", " ")
    data = data.replace("'", "")
    data = data.replace("`", "")
    return data


def create_nypl_fiction_callnum(
    leader_string, tag_008, tag_300a, cuttering_fields, order_data
):
    """
    creates pymarc Field with NYPL Branch call number
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

    # main entry cutter
    cutter = None
    if "100" in cuttering_fields:
        # use last name
        cutter = parse_last_name(cuttering_fields["100"])
        cutter = remove_special_characters(cutter)
    elif "110" in cuttering_fields:
        cutter = parse_first_letter(cuttering_fields["110"])
    elif "111" in cuttering_fields:
        cutter = parse_first_letter(cuttering_fields["111"])
    else:
        cutter = parse_first_letter(cuttering_fields["245"])

    # construct call number field
    subfields = []
    subfield_p_values = []
    field = None
    if order_data and order_data.fiction_location:
        # audience element
        if is_juvenile(audn_code) and order_data.audnType == "j":
            subfield_p_values.append("J")

        # language element
        if lang_prefix and order_data.wlPrefix:
            subfield_p_values.append(lang_prefix)
            # subfields.extend(['p', ' '.join(subfield_p_values)])

        if subfield_p_values:
            subfields.extend(["p", " ".join(subfield_p_values)])

        # format element
        if order_data.callLabel:
            if order_data.callLabel == "lgp":
                subfields.extend(["f", "LG-PRINT"])
            elif order_data.callLabel == "hol":
                subfields.extend(["f", "HOLIDAY"])
            elif order_data.callLabel == "yrd":
                subfields.extend(["f", "YR"])
            elif order_data.callLabel == "cla":
                subfields.extend(["f", "CLASSICS"])
            elif order_data.callLabel == "gra":
                subfields.extend(["f", "GRAPHIC"])
            elif order_data.callLabel == "bil":
                subfields.extend(["f", "BILINGUAL"])

        # main content element
        if is_picture_book(audn_code, tag_300a) and order_data.callType == "pic":
            subfields.extend(["a", "PIC"])
        elif (
            is_picture_book(audn_code, tag_300a) and order_data.callType == "und"
        ):  # world lang picture books
            subfields.extend(["a", "PIC"])
        elif is_picture_book(audn_code, tag_300a) and order_data.callType == "eas":
            subfields.extend(["a", "E"])
        elif order_data.callType == "fic":
            if order_data.callLabel == "gra":
                subfields.extend(["a", "GN FIC"])
            else:
                subfields.extend(["a", "FIC"])
        elif order_data.callType == "mys":
            subfields.extend(["a", "MYSTERY"])
        elif order_data.callType == "rom":
            subfields.extend(["a", "ROMANCE"])
        elif order_data.callType == "sfn":
            subfields.extend(["a", "SCI-FI"])
        elif order_data.callType == "wes":
            subfields.extend(["a", "WESTERN"])
        elif order_data.callType == "urb":
            subfields.extend(["a", "URBAN"])
        elif order_data.callType == "und":
            subfields.extend(["a", "FIC"])

    else:
        if is_juvenile(audn_code):
            subfield_p_values.append("J")

        if lang_prefix:
            subfield_p_values.append(lang_prefix)

        if subfield_p_values:
            subfields.extend(["p", " ".join(subfield_p_values)])

        if is_picture_book(audn_code, tag_300a):
            subfields.extend(["a", "PIC"])
        else:
            subfields.extend(["a", "FIC"])

    # cutter element
    if cutter:
        subfields.extend(["c", cutter])
        field = Field(tag="091", indicators=[" ", " "], subfields=subfields)

    return field


def recap_call(recap_no):
    if not recap_no:
        raise ValueError("Invalid Recap number provided")
    year_ = str(date.today().year)[2:]
    callNo = "ReCAP {}-{}".format(year_, recap_no)
    return callNo


def create_nypl_recap_callnum(recap_no=None):
    callNum = recap_call(recap_no)

    field = Field(tag="852", indicators=["8", " "], subfields=["h", callNum])

    return field


def create_nypl_recap_item(order_data, recap_no=None):
    callNum = recap_call(recap_no)

    settings_data = open("./rules/nyp_recap_codes.json", "r")
    settings_dict = json.load(settings_data)
    recap_codes = settings_dict["ReCAP"]

    # determine correct codes based on order data
    if order_data:
        loc = order_data.locs[:3].upper()
        codes = recap_codes[loc]
    else:
        codes = recap_codes["generic"]

    item_field = Field(
        tag="949",
        indicators=[" ", "1"],
        subfields=[
            "z",
            "8528",
            "a",
            callNum,
            "l",
            codes["loc_code"].lower(),
            "s",
            codes["status"],
            "t",
            codes["item_type"],
            "h",
            codes["agency"],
            "o",
            codes["opac_msg"],
            "v",
            "CATRL/W2Sbot",
        ],
    )

    return item_field
