import unicodecsv as csv
import hashlib
import os
from datetime import datetime

from pandas import read_csv


def md5(text):
    hash_md5 = hashlib.md5(text.encode('utf-8'))
    return hash_md5.hexdigest()


def convert_file_size(size_bytes):
    return '%.1f' % (float(size_bytes) / float(1024)) + 'KB'


def remove_files(fhs):
    removed = True
    if type(fhs) == str:
        fhs = [fhs]
    try:
        for fh in fhs:
            if os.path.isfile(fh):
                os.remove(fh)
    except WindowsError:
        removed = False
    except TypeError:
        removed = False

    finally:
        return removed


def convert2date_obj(str, pattern):
    stamp = datetime.strptime(str, pattern)
    if stamp.year == 1900:
        stamp = stamp.replace(year=datetime.today().year)
    return stamp


def save2csv(dst_fh, row):
    """
    Appends a list with data to a dst_fh csv
    args:
        dst_fh: str, output file
        row: list, list of values to write in a row
    """

    with open(dst_fh, 'a') as csvfile:
        out = csv.writer(
            csvfile,
            encoding='utf-8',
            delimiter=',',
            lineterminator='\n',
            quotechar='"', quoting=csv.QUOTE_MINIMAL)
        out.writerow(row)


def csv2df(csvfile):
    """
    Converts csv data into pandas dataframe
    args:
        csvfile: str, path to csvfile including processing data
    returns:
        df: pandas dataframe
    """

    df = read_csv(csvfile, header=0, na_values=['[]'])
    return df
