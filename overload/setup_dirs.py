# defines directories and files needed for running Overload

import os

USER_NAME = os.environ['USERNAME']
APP_DIR = os.path.join(os.environ['APPDATA'], 'Overload')
LOG_DIR = os.path.join(APP_DIR, 'changesLog')
PATCHING_RECORD = os.path.join(LOG_DIR, 'patching_record.txt')
MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
TEMP_DIR = os.path.join(APP_DIR, 'temp')
BARCODES = os.path.join(TEMP_DIR, 'batch_barcodes.txt')
USER_DATA = os.path.join(APP_DIR, 'user_data')
DATASTORE = os.path.join(APP_DIR, 'datastore.db')  # move some user_data here
BATCH_STATS = os.path.join(TEMP_DIR, 'batch_stats')
BATCH_META = os.path.join(TEMP_DIR, 'batch_meta')
GOO_CREDS = 'Overload Creds/goo_credentials.bin'
GOO_FOLDERS = 'Overload Creds/goo_folders.json'
MVAL_REP = os.path.join(TEMP_DIR, 'marcedit_validation_report.txt')
CVAL_REP = os.path.join(TEMP_DIR, 'combined_validation_report.txt')
LSPEC_REP = os.path.join(TEMP_DIR, 'local_specs_report.txt')
DVAL_REP = os.path.join(TEMP_DIR, 'default_validation_report.txt')
