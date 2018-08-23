# mandatory, default validation


from bibs.bibs import read_marc21
from errors import OverloadError
from utils import remove_files


def barcode_duplicates(batch, system):
    """
    Verifies there are no duplicate barcodes in the batch;
    parses all barcodes found in list of MARC files (batch),
    finds duplicates, and creates a report indicating files
    and records that are dups
    args:
        batch : list of MARC files
    returns:
        dict of dups (key: barcode, value: tuple (file, bib position))
    """
    barcodes = dict()
    dup_barcodes = dict()

    if system == 'nypl':
        item_tag = '949'
        item_tag_ind = [' ', '1']
        item_tag_sub = 'i'
    elif system == 'bpl':
        item_tag = '960'
        item_tag_ind = [' ', ' ']
        item_tag_sub = 'i'

    for fh in batch:
        reader = read_marc21(fh)
        pos = 0
        for record in reader:
            pos += 1
            for tag in record.get_fields(item_tag):
                if tag.indicators == item_tag_ind:
                    for b in tag.get_subfields(item_tag_sub):
                        if b in barcodes:
                            new_value = barcodes[b]
                            new_value.append((fh, pos))
                            barcodes[b] = new_value
                        else:
                            barcodes[b] = [(fh, pos)]

    for k, v in barcodes.iteritems():
        if len(v) > 1:
            dup_barcodes[k] = v

    return dup_barcodes


def save_report(data, outfile):
    # delete previous report
    if not remove_files([outfile]):
        raise OverloadError(
            'Unable to delete previous default '
            'validation report: {}.'.format(outfile))

    report = []
    for k, v in data.iteritems():
        report.append('\n{} - barcode dups:'.format(k))
        dups = []
        for f, p in v:
            dups.append('\tfile: {} -- record no:{}'.format(f, p))
        report.append('\n'.join(sorted(dups)))

    if report == []:
        report = ['No errors found']
    try:
        with open(outfile, 'w') as file:
            file.write('\n'.join(report))
    except IOError as e:
        raise OverloadError(
            'Unable to create a new default validation report. '
            'Error: {}'.format(e))


def validate_processed_files_integrity(files, barcodes_fh):
    valid = True
    proc_barcodes = []
    with open(barcodes_fh, 'r') as file:
        orig_barcodes = sorted([line.strip() for line in file])
        # original barcodes cannot include duplicates, because
        # batch with duplicates never will be processed - error
        # is raised in default validation
    for file in files:
        reader = read_marc21(file)
        for bib in reader:
            for tag in bib.get_fields('960'):
                if tag.indicators == [' ', ' ']:
                    for barcode in tag.get_subfields('i'):
                        proc_barcodes.append(str(barcode))
            for tag in bib.get_fields('949'):
                if tag.indicators == [' ', '1']:
                    for barcode in tag.get_subfields('i'):
                        proc_barcodes.append(str(barcode))
    missing_barcodes = set()
    for barcode in orig_barcodes:
        if barcode not in proc_barcodes:
            valid = False
            missing_barcodes.add(barcode)

    if sorted(orig_barcodes) != sorted(proc_barcodes):
        valid = False

    return valid, missing_barcodes
