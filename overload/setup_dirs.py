# defines directories and files needed for running Overload

import os

APP_DIR = os.environ['APPDATA'] + r'\Overload'
MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
TEMP_DIR = APP_DIR + r'\temp'
USER_DATA = APP_DIR + r'\user_data'
DATASTORE = APP_DIR + r'\datastore.db'  # move some user_data here
BATCH_STATS = TEMP_DIR + r'\batch_stats'
BATCH_META = TEMP_DIR + r'\batch_meta'
MVAL_REP = TEMP_DIR + r'\marcedit_validation_report.txt'
CVAL_REP = TEMP_DIR + r'\combined_validation_report.txt'
LSPEC_REP = TEMP_DIR + r'\local_specs_report.txt'
