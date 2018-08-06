import os
import logging

from bibs import read_marc21, write_marc21, BibMeta


module_logger = logging.getLogger('overload_console.dedup')


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

    return dups


def dedup_marc_file(file):
    """
    Dedups records in a processed file based on the 001 tag (control field);
    combies 949 item tags on merged bibs
    args:
        marc file handle
    returns:
        file_handle of deduped file
    """

    module_logger.info('Deduping processed file {}'.format(
        file))

    reader = read_marc21(file)
    counter = 0
    indices = dict()
    for record in reader:
        meta = BibMeta(record)
        indices[counter] = meta.t001
        counter += 1

    dups = _find_duplicates(indices)
    dedup_count = 0
    fh_deduped = None

    if len(dups) > 0:
        module_logger.debug(
            'Discovered duplicates in processed file {}: {}'.format(
                file, dups))

        # create new MARC file and add deduped bibs to it
        fh_deduped = file[:-4] + '-DEDUPED.mrc'

        for k, v in dups.iteritems():
            counter = 0
            first_pass = True
            reader = read_marc21(file)

            for record in reader:
                if counter in v:
                    if v[0] == counter:
                        new_record = record
                        dedup_count += 1
                    else:
                        dedup_count += 1
                        tags = record.get_fields('949')
                        for tag in tags:
                            if tag.indicators == [' ', '1']:
                                new_record.add_ordered_field(tag)
                elif first_pass:
                    write_marc21(fh_deduped, record)

                counter += 1
            first_pass = False

            write_marc21(fh_deduped, new_record)
        module_logger.info('Merged {} duplicate bibs in file {}'.format(
            dedup_count, file))
    else:
        module_logger.debug('No duplicates found in file: {}'.format(
            file))

    return fh_deduped
