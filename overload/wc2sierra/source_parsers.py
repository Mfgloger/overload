import csv
from bibs.bibs import BibOrderMeta


def sierra_export_data(source_fh, system, dstLibrary):
    """
    Exported from Sierra data includes multiple values in each column,
    for example:
    returns:
        meta, single_order: tuple, (BibOrderMeta obj, single_order)
    """
    with open(source_fh) as source:
        reader = csv.reader(source, delimiter='~', quotechar=None)
        # skip header
        reader.next()
        for row in reader:
            kwargs = dict(system=system, dstLibrary=dstLibrary)
            if row[0].strip():
                kwargs['t020'] = row[0].split('^')
            kwargs['sierraId'] = row[1][1:-1]
            if row[2].strip():
                kwargs['t005'] = row[2]
            if row[3].strip():
                kwargs['t010'] = row[3]
            if row[4].strip():
                kwargs['t024'] = row[4].split('^')
            if row[5].strip():
                ids = row[5].split('^')
                for i in ids:
                    if '(OCoLC)' in i:
                        kwargs['t001'] = i.replace('(OCoLC)', '').strip()
                        break
            kwargs['title'] = row[6]

            # determine how many orders in row
            # and create a list of tuples for each order
            ords_data = row[7:]
            ordlen = len(ords_data) / 9

            ords = []
            for o in range(ordlen):
                oid = ords_data[o]
                venNote = ords_data[o + ordlen]
                note = ords_data[2 * ordlen]
                intNote = ords_data[3 * ordlen]
                code2 = ords_data[o + (4 * ordlen)]
                code4 = ords_data[o + (5 * ordlen)]
                locs = ords_data[o + (6 * ordlen)]
                form = ords_data[o + (7 * ordlen)]
                vendor = ords_data[o + (8 * ordlen)]
                status = ords_data[o + (9 * ordlen)]
                ords.append((
                    oid, venNote, note, intNote,
                    code2, code4, locs, form, vendor,
                    status))

            # oldest to latest order from Sierra, interested only in newest
            for o in reversed(ords):
                # check if correct status status
                if o[7] != 'z':
                    kwargs['oid'] = o[0]
                    kwargs['venNote'] = o[1]
                    kwargs['note'] = o[2]
                    kwargs['intNote'] = o[3]
                    kwargs['code2'] = o[4]
                    kwargs['code4'] = o[5]
                    kwargs['locs'] = o[6]
                    kwargs['oFormat'] = o[7]
                    kwargs['vendor'] = o[8]
                    break
            meta = BibOrderMeta(**kwargs)

            single_order = True
            if len(ords) > 1:
                single_order = False

            yield (meta, single_order)
