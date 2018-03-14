import xml.etree.ElementTree as ET
# from pymarc import Field


def vendor_index(vendor_fh, library):
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
    ven_index = []

    for system in root.iter('system'):
        if system.attrib['name'] == library:
            for vendor in system:

                # parse identification methods
                ven_dict = dict()
                vids = vendor.findall('id_marc_tag')
                vids_dict = dict()
                for vid in vids:
                    vids_dict[vid.attrib['tag']] = {
                        'operator': vid.attrib['operator'],
                        'type': vid.attrib['type'],
                        'value': vid.find('tag_value').text}

                # parse query points
                query_dict = dict()
                queries = vendor.findall('query_tag')
                for query in queries:
                    query_dict[query.attrib['type']] = query.text

                # append the index
                ven_dict[vendor.attrib['name']] = dict(dict(
                    identification=vids_dict),
                    query=query_dict)
                ven_index.append(ven_dict)

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
    for vendor_data in vendor_index:
        main = []
        alternative = []
        name = vendor_data.keys()[0]
        identification = vendor_data[name]['identification']
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
                name = vendor_data.keys()[0]
                matching_vendors.append(name)
            else:
                # go to alternarive method
                # all alt conditions must be met
                matches_needed = len(alternative)
                if matches_needed > 0:
                    matches_found = find_matches(bib, alternative)
                    if matches_found == matches_needed:
                        name = vendor_data.keys()[0]
                        matching_vendors.append(name)

    # set to unknown if not found
    if len(matching_vendors) != 1:
        return 'UNKNOWN'
    else:
        return matching_vendors[0]
