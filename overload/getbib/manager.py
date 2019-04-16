import csv


def launch_process(library, target, id_type, source_fh, dst_fh):
    with open(source_fh) as source:
        reader = csv.reader(source)
        # skip header
        reader.next()
        for row in reader:
            rid = row[0]
            print(rid)
