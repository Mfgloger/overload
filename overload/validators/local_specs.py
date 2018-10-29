import xml.etree.ElementTree as ET


from bibs.bibs import read_marc21
from bibs.sierra_dicts import NYPL_BRANCHES, BPL_BRANCHES


def local_specs(system, agent, fh):
    """
    creates local specification index for given system and agent

    args:
        files (MARC21 files)
        system (str: nypl or bpl)
        agent (str: cat, sel, or acq)
    return:
        specifications dictionary
    """
    if system not in ('nypl', 'bpl'):
        raise AttributeError(
            'system value can be only "bpl" or "nypl".')
    if agent not in ('cat', 'sel', 'acq'):
        raise AttributeError(
            'agent value can be only "cat", "sel", or "acq"')

    specs = []
    tree = ET.parse(fh)
    data = tree.getroot()
    for s in data.iter('system'):
        if s.attrib['name'] == system:
            for a in s.iter('agent'):
                if a.attrib['name'] == agent:
                    for tag in a.findall('tag'):
                        tag_spec = dict()
                        tag_spec['tag'] = tag.attrib['code']
                        tag_spec['ind'] = tag.attrib['indicators']
                        tag_spec['mandatory'] = tag.attrib['mandatory']
                        tag_spec['repeatable'] = tag.attrib['repeatable']
                        tag_spec['subfields'] = []
                        for sub in tag.findall('sub'):
                            sub_spec = dict()
                            sub_spec['code'] = sub.attrib['code']
                            sub_spec['mandatory'] = sub.attrib['mandatory']
                            sub_spec['repeatable'] = sub.attrib['repeatable']

                            if sub.attrib['check'] == 'none':
                                sub_spec['check'] = None
                            else:
                                sub_spec['check'] = sub.attrib['check']

                            if sub.attrib['check'] == 'list':
                                sub_spec['value'] = sub.text.split(',')
                            else:
                                sub_spec['value'] = []
                            tag_spec['subfields'].append(sub_spec)
                        specs.append(tag_spec)
                    break
    return specs


def location_check(system, subfield):
    """
    verifies a correct location is encoded in item tag
    args:
        system, subfield
    returns:
        Boolean (valid or not)
    """
    correct = True
    if system == 'nypl':
        if subfield[:2] not in NYPL_BRANCHES:
            correct = False
    elif system == 'bpl':
        if subfield[:2] not in BPL_BRANCHES:
            correct = False

    return correct


def price_check(subfield):
    """
    verifies a price format is encoded correctly
    args:
        subfield
    returns:
        Boolean (correct or not)
    """
    correct = True
    try:
        if '.' not in subfield:
            correct = False
    except TypeError:
        correct = False

    # handle BPL Midwest coding
    try:
        if '$' in subfield:
            subfield = subfield.replace('$', '')
    except TypeError:
        correct = False

    try:
        float(subfield)
    except ValueError:
        correct = False
    except TypeError:
        correct = False

    return correct


def local_specs_validation(system, files, specs):
    """
    launches validation for bibs if they conform to criteria defined
    in vendor_specs.xml file
    args:
        files (list)
        specs (dictionary)
    returns:
        result (tupe: (boolean result, report string)
    """
    issues = []
    validates = True
    for file in files:
        file_issues = []
        bib_count = 0
        reader = read_marc21(file)
        for bib in reader:
            bib_count += 1
            bib_issues = []
            for spec in specs:
                mandat = spec['mandatory']
                repeat = spec['repeatable']
                ind = [' ' if i == 'blank' else i for i in spec['ind'].split(',')]

                # check mandatory tag criteria
                if mandat == 'y':
                    found = False
                    if spec['tag'] in bib:
                        for tag in bib.get_fields(spec['tag']):
                            if tag.indicators == ind:
                                found = True
                    if not found:
                        bib_issues.append(
                            '"{}{}" mandatory tag not found.'.format(
                                spec['tag'],
                                ''.join(ind)))

                # check repeatable criteria
                if repeat == 'n':
                    match_count = 0
                    if spec['tag'] in bib:
                        for tag in bib.get_fields(spec['tag']):
                            if tag.indicators == ind:
                                match_count += 1
                    if match_count > 1:
                        bib_issues.append(
                            '"{}{}" is not repeatable'.format(
                                spec['tag'],
                                ''.join(ind)))

                # subfields checks
                for i, tag in enumerate(bib.get_fields(spec['tag'])):
                    tag_issues = []
                    tag_head = '"{}": tag occurance {}:'.format(
                        spec['tag'],
                        i + 1)
                    sub_issues = []
                    if tag.indicators == ind:
                        for sub in spec['subfields']:
                            sub_check = sub['check']
                            sub_value = sub['value']
                            sub_mandat = sub['mandatory']
                            sub_repeat = sub['repeatable']

                            # check mandatory subfield criteria
                            if sub_mandat == 'y':
                                found = False
                                if sub['code'] in tag.subfields:
                                    found = True
                                if not found:
                                    sub_issues.append(
                                        '\t"{}" subfield is mandatory.'.format(
                                            sub['code']))

                            # check repeatable critera
                            if sub_repeat == 'n':
                                match_count = 0

                                for s in tag.get_subfields(sub['code']):
                                    match_count += 1

                                if match_count > 1:
                                    sub_issues.append(
                                        '\t"{}" subfield is not '
                                        'repeatable.'.format(
                                            sub['code']))

                            # specific value checks
                            if sub_check == 'none':
                                pass
                            elif sub_check == 'list':
                                for s in tag.get_subfields(sub['code']):
                                    if s not in sub_value:
                                        sub_issues.append(
                                            '\t"{}" subfield has '
                                            'incorrect value.'.format(
                                                sub['code']))
                            elif sub_check == 'barcode':
                                for s in tag.get_subfields(sub['code']):
                                    found = False
                                    if system == 'nypl':
                                        if s[:2] != '33':
                                            found = True
                                    elif system == 'bpl':
                                        if s[:2] != '34':
                                            found = True
                                    if len(s) != 14:
                                        found = True
                                    try:
                                        int(s)
                                    except ValueError:
                                        found = True
                                    except TypeError:
                                        found = True

                                    if found:
                                        sub_issues.append(
                                            '\t"{}" subfield has incorrect '
                                            'barcode.'.format(
                                                sub['code']))
                            elif sub_check == 'location':
                                for s in tag.get_subfields(sub['code']):
                                    if not location_check(system, s):
                                        sub_issues.append(
                                            '\t"{}" subfield has incorrect '
                                            'location code.'.format(
                                                sub['code']))
                            elif sub_check == 'price':
                                for s in tag.get_subfields(sub['code']):
                                    if not price_check(s):
                                        sub_issues.append(
                                            '\t"{}" subfield has incorrect '
                                            'price format.'.format(
                                                sub['code']))

                    if sub_issues != []:
                        tag_issues.append(tag_head)
                        tag_issues.append('\n'.join(sub_issues))
                        bib_issues.append('\n'.join(tag_issues))

            if bib_issues != []:
                bib_issues.insert(0, 'Record {}'.format(bib_count))
                file_issues.append('\n'.join(bib_issues))

        issues.append('\nFile: {}\n{}'.format(file, '-' * 40))
        if file_issues != []:
            validates = False
            issues.append('\n'.join(file_issues))
        else:
            issues.append('No errors found.')

    issues = '\n'.join(issues)

    return (validates, issues)
