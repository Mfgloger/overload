import csv
from bibs.bibs import BibOrderMeta


def find_order_field(fields, field_position, order_sequence):
    """applies only to BPL order export"""
    try:
        return fields[field_position].split("^")[order_sequence]
    except IndexError:
        return ""


def parse_BPL_order_export(ords_data):
    ords_organized = []
    ordlen = len(ords_data[0].split("^")) + 1
    for o in range(ordlen):
        oid = find_order_field(ords_data, 0, o)
        status = find_order_field(ords_data, 9, o)
        if not oid or status in ("1", "z"):
            # return empty if order data is empy string or
            # order status indicates its cancelled or on hold
            break
        else:
            ord_dict = dict(
                oid=oid,
                venNote=find_order_field(ords_data, 1, o),
                note=find_order_field(ords_data, 2, o),
                intNote=find_order_field(ords_data, 3, o),
                code2=find_order_field(ords_data, 4, o),
                code4=find_order_field(ords_data, 5, o),
                locs=ords_data[6],  # BPL export combines locations :(
                oFormat=find_order_field(ords_data, 7, o),
                vendor=find_order_field(ords_data, 8, o),
            )
            ords_organized.append(ord_dict)
    return ords_organized


def parse_NYPL_order_export(ords_data):
    ords_organized = []

    # NYPL repeated field delimiter for order data is the same as field delimiter for
    # some reason; method below takes care of that
    ordlen = len(ords_data) / 10
    for o in range(ordlen):
        oid = ords_data[o]
        status = ords_data[o + (9 * ordlen)]
        if not oid or status in ("1", "2", "s", "z"):
            # return empty if order data is empy string or
            # order status indicates its cancelled or on hold
            break
        else:
            ord_dict = dict(
                oid=oid,
                venNote=ords_data[o + ordlen],
                note=ords_data[2 * ordlen],
                intNote=ords_data[3 * ordlen],
                code2=ords_data[o + (4 * ordlen)],
                code4=ords_data[o + (5 * ordlen)],
                locs=ords_data[o + (6 * ordlen)],
                oFormat=ords_data[o + (7 * ordlen)],
                vendor=ords_data[o + (8 * ordlen)],
            )
            ords_organized.append(ord_dict)
    return ords_organized


def parse_order_data(system, ords_segment):
    """returns dictionary"""

    # NYPL and BPL Sierra exports look differently,
    # NYPL order fields for multiple orders are not separated by repeated
    # field delimiter (default ^),
    if system == "NYPL":
        ords_data = parse_NYPL_order_export(ords_segment)
    elif system == "BPL":
        ords_data = parse_BPL_order_export(ords_segment)
    else:
        ords_data = []
    if len(ords_data) == 0:
        single_order = None
    elif len(ords_data) == 1:
        single_order = True
    elif len(ords_data) > 1:
        single_order = False

    # oldest to latest order from Sierra, interested only in newest
    try:
        last_order = ords_data[-1]
    except IndexError:
        last_order = None

    return single_order, last_order


def sierra_export_data(source_fh, system, dstLibrary):
    """
    Exported from Sierra data includes multiple values in each column,
    for example:
    returns:
        meta, single_order: tuple, (BibOrderMeta obj, single_order)
    """
    with open(source_fh) as source:
        reader = csv.reader(source, delimiter="~", quoting=csv.QUOTE_NONE)
        # skip header
        reader.next()
        for row in reader:
            kwargs = dict(system=system, dstLibrary=dstLibrary)
            if row[0].strip():
                kwargs["t020"] = row[0].split("^")
            kwargs["sierraId"] = row[1][1:-1]
            if row[2].strip():
                kwargs["t005"] = row[2]
            if row[3].strip():
                kwargs["t010"] = row[3]
            if row[4].strip():
                kwargs["t024"] = row[4].split("^")
            if row[5].strip():
                ids = row[5].split("^")
                for i in ids:
                    if "(OCoLC)" in i:
                        kwargs["t001"] = i.replace("(OCoLC)", "").strip()
                        break
            kwargs["title"] = row[6]

            # determine how many orders in row
            # and create a list of tuples for each order
            ords_segment = row[7:]
            single_order, last_order = parse_order_data(system, ords_segment)
            if last_order is not None:
                # update BibOrderMeta with order data if present
                kwargs.update(last_order)
            meta = BibOrderMeta(**kwargs)

            yield (meta, single_order)
