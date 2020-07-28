# module used for work with MARCXML

# OCLC Worldcat response namespaces
ONS = {
    "response": "http://www.loc.gov/zing/srw/",
    "marc": "http://www.loc.gov/MARC21/slim",
    "atom": "http://www.w3.org/2005/Atom",
    "rb": "http://worldcat.org/rb",
}


def get_record_leader(marcxml):
    for field in marcxml.findall("marc:leader", ONS):
        return field.text


def get_tag_005(marcxml):
    for field in marcxml.findall("marc:controlfield", ONS):
        if field.attrib["tag"] == "005":
            return field.text


def get_tag_008(marcxml):
    for field in marcxml.findall("marc:controlfield", ONS):
        if field.attrib["tag"] == "008":
            return field.text


def get_cat_lang(field):
    for subfield in field.findall("marc:subfield", ONS):
        if subfield.attrib["code"] == "b":
            code = subfield.text.strip()
            return code


def get_datafield_040(marcxml):
    for field in marcxml.findall("marc:datafield", ONS):
        if field.attrib["tag"] == "040":
            return field


def get_tags_041a(marcxml):
    langs = []
    for field in marcxml.findall("marc:datafield", ONS):
        if field.attrib["tag"] == "041":
            for subfield in field.findall("marc:subfield", ONS):
                if subfield.attrib["code"] == "a":
                    langs.append(subfield.text.strip())


def get_oclcNo(marcxml):
    for field in marcxml.findall("marc:controlfield", ONS):
        if field.attrib["tag"] == "001":
            return field.text.strip()


def get_tag_082(marcxml):
    if marcxml is None:
        return None

    tag = None
    for field in marcxml.findall("marc:datafield", ONS):
        if field.attrib["tag"] == "082":
            if field.attrib["ind1"] == "0":
                for subfield in field.findall("marc:subfield", ONS):
                    if subfield.attrib["code"] == "a":
                        tag = subfield.text.strip()
                        return tag


def get_tag_300a(marcxml):
    for field in marcxml.findall("marc:datafield", ONS):
        if field.attrib["tag"] == "300":
            for subfield in field.findall("marc:subfield", ONS):
                if subfield.attrib["code"] == "a":
                    return subfield.text.strip()


def get_tags_347b(marcxml):
    tags = []
    for field in marcxml.finall("marc:datafield", ONS):
        if field.attrib["tag"] == "347":
            for subfield in field.findall("marc:subfield", ONS):
                if subfield.attrib["code"] == "b":
                    tags.append(subfield.text.strip())
    return tags


def get_tags_538a(marcxml):
    tags = []
    for field in marcxml.findall("marc:datafield", ONS):
        if field.attrib["tag"] == "538":
            for subfield in field.findall("marc:subfield", ONS):
                if subfield.attrib["code"] == "a":
                    tags.append(subfield.text.strip())
    return tags


def get_cuttering_fields(marcxml):
    """
    parses values of fields 100, 110, 111, and 245
    and retuns them as dictionary with tags as keys
    args:
        marcxml: xml, xml.etree.ElementTree object
    returns:
        cutter_opts: dict, key marc tag, value - value of each tag
    """

    cutter_opts = dict()
    tags = ["100", "110", "111", "245"]
    for field in marcxml.findall("marc:datafield", ONS):
        for tag in tags:
            if field.attrib["tag"] == tag:
                for subfield in field.findall("marc:subfield", ONS):
                    if subfield.attrib["code"] == "a":
                        if tag == "245":
                            # skip article characters if found
                            skip_chr = field.attrib["ind2"].strip()
                            if skip_chr:
                                skip_chr = int(skip_chr)
                            else:
                                skip_chr = 0
                            cutter_opts[tag] = subfield.text[skip_chr:].strip()
                        else:
                            cutter_opts[tag] = subfield.text
                    if tag == "100":
                        # include also subfield b if present
                        if subfield.attrib["code"] == "b":
                            name = cutter_opts[tag]
                            name += subfield.text
                            cutter_opts[tag] = name

    return cutter_opts


def get_subject_fields(marcxml):
    """
    parses LC Subject Headings and outputs them as dictionary
    temporarily focus only on 600
    """
    subject_fields = dict()

    if marcxml is None:
        return subject_fields

    subjects = []
    for field in marcxml.findall("marc:datafield", ONS):
        if field.attrib["tag"] == "600" and field.attrib["ind2"] == "0":
            subject = []
            for subfield in field.findall("marc:subfield", ONS):
                if subfield.attrib["code"] in ("a", "b"):
                    subject.append(subfield.text)
            if len(subject) >= 1:
                subjects.append(" ".join(subject))
    # return temporarily only first 600
    if len(subjects) >= 1:
        subject_fields["600"] = subjects[0]

    return subject_fields


def results2record_list(results):
    recs = []
    for rec in results.findall(".//response:recordData/marc:record", ONS):
        recs.append(rec)
    return recs
