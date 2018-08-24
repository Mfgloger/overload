import hashlib
import math
import os


def md5(text):
    hash_md5 = hashlib.md5(text.encode('utf-8'))
    return hash_md5.hexdigest()


def convert_file_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return "{}{}".format(s, size_name[i])


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
