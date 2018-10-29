import logging

from bibs import read_marc21, write_marc21, BibMeta
from logging_setup import LogglyAdapter


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def _find_duplicates(indices):
    """
    creates a dictionary of dups with bib 001 as a key, and value as a
    list of record positions in a file
    args:
        dictorinary of record position (key) and 001 tag (value)
    retuns:
        dictionary of dups
    """

    indices_organized = dict()
    skip_bibs = []
    for k, v in indices.iteritems():
        d = []
        for n, m in indices.iteritems():
            if m is not None and m == v:
                d.append(n)
        indices_organized[v] = d

    dups = dict()
    for k, v in indices_organized.iteritems():
        if len(v) > 1:
            dups[k] = v
            skip_bibs.extend(v)
    return dups, sorted(skip_bibs)


def merge_bibs_combine_items(file, bib_list):
    """
    merges bibs in bib_list and combines their item record tags
    args:
        file, bib_list
    returns:
        merged record, number of combined bibs
    """

    reader = read_marc21(file)
    counter = -1
    dedup_add = 0
    for record in reader:
        counter += 1
        if counter == bib_list[0]:
            # use first record in file as a base
            new_record = record
            dedup_add += 1
        elif counter in bib_list:
            # for the following dups copy item 949 and
            # add to merged record
            dedup_add += 1

            # NYPL
            tags = record.get_fields('949')
            for tag in tags:
                if tag.indicators == [' ', '1']:
                    new_record.add_ordered_field(tag)
            # BPL
            tags = record.get_fields('960')
            for tag in tags:
                if tag.indicators == [' ', ' ']:
                    new_record.add_ordered_field(tag)

    return new_record, dedup_add


def dedup_marc_file(file, progbar=None):
    """
    Dedups records in a processed file based on the 001 tag (control field);
    combies 949 item tags on merged bibs
    args:
        file: string, marc file handle
        progbar: instance of ttk.Progressbar
    returns:
        dedup_count: tuple (int, int, str)
            number of dups, number of resulting bibs,
            file_handle of deduped file
    """

    module_logger.debug('Deduping processed file {}'.format(
        file))

    reader = read_marc21(file)
    c = 0
    indices = dict()
    for record in reader:
        meta = BibMeta(record)
        indices[c] = meta.t001
        c += 1

    dups, skip_bibs = _find_duplicates(indices)
    # print skip_bibs
    # print dups
    dedup_count = 0
    fh_deduped = None

    if progbar is not None:
        progbar['maximum'] = c + (c * len(dups))
        n = 0
        progbar['value'] = n
        progbar.update()

    if len(dups) > 0:
        module_logger.debug(
            'Discovered {} duplicate(s) in processed file {}'.format(
                file, dups))

        # create new MARC file and add deduped bibs to it
        fh_deduped = file[:-4] + '-DEDUPED.mrc'

        # save files that do not have duplicates
        n = 0
        reader = read_marc21(file)
        dedup_count = 0
        for record in reader:
            if n not in skip_bibs:
                write_marc21(fh_deduped, record)
            n += 1
            if progbar is not None:
                progbar['value'] = n

        for key, bib_list in dups.iteritems():
            n += (c * len(bib_list))
            new_record, dedup_add = merge_bibs_combine_items(
                file, bib_list)

            # add to deduped count
            dedup_count += dedup_add

            # save new merged record
            write_marc21(fh_deduped, new_record)

            if progbar is not None:
                progbar['value'] = n
                progbar.update()

        module_logger.debug(
            'Merged {} duplicate bibs into {} in file {}'.format(
                dedup_count, len(dups), file))

    else:
        if progbar is not None:
            progbar['value'] = progbar['maximum']
            progbar.update()
        module_logger.debug('No duplicates found in file: {}'.format(
            file))

    return dedup_count, len(dups), fh_deduped
