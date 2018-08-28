import hashlib
import os
from datetime import datetime


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
