# updates overload
import shutil
import os
import sys
import time
import subprocess
from distutils.dir_util import copy_tree


APP_DIR = os.path.join(os.environ['APPDATA'], 'Overload')
LOG_DIR = os.path.join(APP_DIR, 'changesLog')
PATCHING_RECORD = os.path.join(LOG_DIR, 'patching_record.txt')


def run_update(src_directory):
    if os.path.isfile('overload.exe'):

        CREATE_NO_WINDOW = 0x08000000

        # kill the app
        try:
            subprocess.call(
                'TASKKILL /F /IM overload.exe',
                creationflags=CREATE_NO_WINDOW)
            time.sleep(1)
        except:
            pass

        # delete content of the main folder except updater.exe
        entries = [f for f in os.listdir('.') if 'updater' not in f]
        for f in entries:
            if os.path.isdir(f):
                shutil.rmtree(f)
            else:
                os.remove(f)

        # copy updated files
        entries = [f for f in os.listdir(src_directory) if 'updater' not in f]
        for f in entries:
            if os.path.isdir(src_directory + '\\' + f):
                copy_tree(src_directory + '\\' + f, os.getcwd() + '\\' + f)
            else:
                shutil.copy2(src_directory + '\\' + f, os.getcwd())

        # apply patches
        # find if any new patches have been copied
        found_patches = [f for f in os.listdir('.') if 'patch' in f]

        # find patches already applied (we don't want to run the same ones
        # every single update)
        installed_patches = []
        if os.path.isfile(PATCHING_RECORD):
            with open(PATCHING_RECORD, 'r') as file:
                installed_patches = [line[:5] for line in file.readlines()]

        # run patches in order
        for f in sorted(found_patches):
            if f[6:11] not in installed_patches:
                subprocess.call(f, creationflags=CREATE_NO_WINDOW)

        subprocess.call(
            'overload.exe',
            creationflags=CREATE_NO_WINDOW)


if __name__ == '__main__':
    run_update(sys.argv[1])
