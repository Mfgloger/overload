import xml.etree.ElementTree as ET


def vendor_index(vendor_fh, library, agent):
    """
    creates library's vendor index based on rules/vendors.xml file
    the vendor index contains methods of identifying bibs to belong
    to a particuar vendor, as well as preferred Sierra query methods

    args:
        library str (nypl or bpl)
    return:
        vendor data for the library in form of a dictionary
    """
    tree = ET.parse(vendor_fh)
    root = tree.getroot()
    ven_index = dict()

    for system in root.iter('system'):
        if system.attrib['name'] == library and \
                system.attrib['agent'] == agent:
            for vendor in system:

                vids_dict = dict()
                if agent == 'cat':
                    # parse identification methods for cat bibs
                    vids = vendor.findall('vendor_tag')
                    for vid in vids:
                        vids_dict[vid.attrib['tag']] = {
                            'operator': vid.attrib['operator'],
                            'type': vid.attrib['type'],
                            'value': vid.text}

                # load applicable templates
                templates_dict = dict()
                templates = vendor.findall('template')
                for template in templates:
                    # define bibliographic record template to be applied
                    fields = []
                    for field in template.findall('field'):
                        subfields_dict = dict()
                        for subfield in field.findall('subfield'):
                            subfields_dict[
                                subfield.attrib['code']] = subfield.text
                        fields.append({
                            'tag': field.find('tag').text,
                            'ind1': field.find('ind1').text,
                            'ind2': field.find('ind2').text,
                            'subfields': subfields_dict})
                    templates_dict[template.attrib['type']] = fields

                # parse query points
                query_dict = dict()
                queries = vendor.findall('query_tag')
                for query in queries:
                    query_dict[query.attrib['preference']] = (
                        query.attrib['type'], query.text)

                # add to the index
                ven_index[vendor.attrib['name']] = dict(dict(
                    identification=vids_dict),
                    query=query_dict,
                    template=templates_dict)

    return ven_index


def find_matches(bib, conditions):
    """
    finds matches in fields and subfieds specified in contitions
    args:
        bib obj (pymarc)
        conditions list of tuples (tag, subfield, value)
    return:
        matches_found int (number of matches in bib)
    """
    matches_found = 0
    for condition in conditions:
        fields = bib.get_fields(condition[0])
        for field in fields:
            if condition[1] is not None:
                for subfield in field.get_subfields(condition[1]):
                    if condition[2] == subfield:
                        matches_found += 1
            else:
                if condition[2] == field.data:
                    matches_found += 1
    return matches_found


def parse_identification_method(tag, type):
    """
    parses id_marc_tag tag attrib for proper handling in pymarc obj
    args:
        tag str (marc tag)
        type str (standard, control field)
    return:
        (tag, subfield) tuple
    """
    if type == 'standard':
        tag_to_check = tag[:3]
        subfield = tag[-1]
    elif type == 'control_field':
        tag_to_check = tag
        subfield = None
    elif type == 'missing':
        tag_to_check = None
        subfield = None
    return (tag_to_check, subfield)


def identify_vendor(bib, vendor_index):
    """
    identifies vendor in the bib based on vendor_index
    args:
        bib obj (pymarc)
        vendor_index dict
    return
        vendor str
    """
    matching_vendors = []
    for vendor, data in vendor_index.iteritems():
        main = []
        alternative = []
        identification = data['identification']
        for tag, conditions in identification.iteritems():
            operator = conditions['operator']
            type = conditions['type']
            value = conditions['value']
            if operator == 'main':
                main.append(parse_identification_method(
                    tag, type) + (value, ))
            elif operator == 'alternative':
                alternative.append(parse_identification_method(
                    tag, type) + (value, ))

        # all main conditions must be met
        matches_needed = len(main)
        if matches_needed > 0:
            matches_found = find_matches(bib, main)
            if matches_found == matches_needed:
                matching_vendors.append(vendor)
            else:
                # go to alternarive method
                # all alt conditions must be met
                matches_needed = len(alternative)
                if matches_needed > 0:
                    matches_found = find_matches(bib, alternative)
                    if matches_found == matches_needed:
                        matching_vendors.append(vendor)

    # set to unknown if not found
    if len(matching_vendors) != 1:
        return 'UNKNOWN'
    else:
        return matching_vendors[0]


def get_query_matchpoint(vendor, vendor_index):
    return vendor_index[vendor]['query']
