import hashlib


def md5(text):
    hash_md5 = hashlib.md5(text.encode('utf-8'))
    return hash_md5.hexdigest()
