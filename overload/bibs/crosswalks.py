import json
from pymarc import Record, Field

from bibs import InhouseBibMeta


def platform2pymarc_obj(data):
    """
    converts platform bib data into pymarc object
    """
    # get MARC data
    record = Record(force_utf8=True)

    # parse variable fields
    varFields = data.get('varFields')
    for f in varFields:
        if f.get('fieldTag') == '_':
            record.leader = f.get('content')
        # control fields case
        elif f.get('subfields') is None:
            field = Field(
                tag=f.get('marcTag'),
                indicators=[f.get('ind1'), f.get('ind2')],
                data=f.get('content'))
            record.add_field(field)
        else:  # variable fields
            subfields = []
            for d in f.get('subfields'):
                subfields.append(d.get('tag'))
                subfields.append(d.get('content'))
            field = Field(
                tag=f.get('marcTag'),
                indicators=[f.get('ind1'), f.get('ind2')],
                subfields=subfields)
            record.add_field(field)
    return record


def platform2meta(results):
    bibs = []
    data = results.get('data')
    for b in data:
        # get Sierra data
        bid = b.get('id')
        locations = [x.get('code') for x in b.get('locations')]
        bib = platform2pymarc_obj(b)
        meta = InhouseBibMeta(bib, sierraID=bid, locations=locations)
        bibs.append(meta)
    return bibs