# module used for work with MARCXML

NS = {'marc': 'http://www.loc.gov/MARC21/slim',
      'atom': 'http://www.w3.org/2005/Atom',
      'rb': 'http://worldcat.org/rb'}


def get_record_leader(marcxml):
    for field in marcxml.findall('marc:leader', NS):
        return field.text


def get_tag_005(marcxml):
    for field in marcxml.findall('marc:controlfield', NS):
        if field.attrib['tag'] == '005':
            return field.text


def get_tag_008(marcxml):
    for field in marcxml.findall('marc:controlfield', NS):
        if field.attrib['tag'] == '008':
            return field.text


def get_cat_lang(field):
    for subfield in field.findall('marc:subfield', NS):
        if subfield.attrib['code'] == 'b':
            code = subfield.text.strip()
            return code


def get_datafield_040(marcxml):
    for field in marcxml.findall('marc:datafield', NS):
        if field.attrib['tag'] == '040':
            return field


def get_oclcNo(marcxml):
    for field in marcxml.findall('marc:controlfield', NS):
        if field.attrib['tag'] == '001':
            return field.text.strip()


def get_tag_300a(marcxml):
    for field in marcxml.findall('marc:datafield', NS):
        if field.attrib['tag'] == '300':
            for subfield in field.findall('marc:subfield', NS):
                if subfield.attrib['code'] == 'a':
                    return subfield.text.strip()


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
    tags = ['100', '110', '111', '245']
    for field in marcxml.findall('marc:datafield', NS):
        for tag in tags:
            if field.attrib['tag'] == tag:
                for subfield in field.findall('marc:subfield', NS):
                    if subfield.attrib['code'] == 'a':
                        if tag == '245':
                            # skip article characters if found
                            skip_chr = field.attrib['ind2'].strip()
                            if skip_chr:
                                skip_chr = int(skip_chr)
                            else:
                                skip_chr = 0
                            cutter_opts[tag] = subfield.text[skip_chr:].strip()
                        else:
                            cutter_opts[tag] = subfield.text
                    if tag == '100':
                        # include also subfield b if present
                        if subfield.attrib['code'] == 'b':
                            name = cutter_opts[tag]
                            name += subfield.text
                            cutter_opts[tag] = name

    return cutter_opts
