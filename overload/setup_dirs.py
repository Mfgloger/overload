# defines directories and files needed for running Overload

import os

USER_NAME = os.environ["USERNAME"]
APP_DIR = os.path.join(os.environ["USERPROFILE"], "BookOps Apps\\Overload")
LOG_DIR = os.path.join(APP_DIR, "changesLog")
PATCHING_RECORD = os.path.join(LOG_DIR, "patching_record.txt")
MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
TEMP_DIR = os.path.join(APP_DIR, "temp")
BARCODES = os.path.join(TEMP_DIR, "batch_barcodes.txt")
USER_DATA = os.path.join(APP_DIR, "user_data")
DATASTORE = os.path.join(APP_DIR, "datastore.db")  # move some user_data here
BATCH_STATS = os.path.join(TEMP_DIR, "batch_stats")
BATCH_META = os.path.join(TEMP_DIR, "batch_meta")
GETBIB_REP = os.path.join(TEMP_DIR, "getbib-report.csv")
W2S_MULTI_ORD = os.path.join(TEMP_DIR, "w2s-multi-orders.csv")
W2S_SKIPPED_ORD = os.path.join(TEMP_DIR, "w2s-skipped-orders.csv")
WORLDCAT_CREDS = "Overload Creds/Worldcat"
GOO_CREDS = "Overload Creds\\Google\\goo_credentials.bin"
GOO_FOLDERS = "Overload Creds\\Google\\goo_folders.json"
MVAL_REP = os.path.join(TEMP_DIR, "marcedit_validation_report.txt")
CVAL_REP = os.path.join(TEMP_DIR, "combined_validation_report.txt")
LSPEC_REP = os.path.join(TEMP_DIR, "local_specs_report.txt")
DVAL_REP = os.path.join(TEMP_DIR, "default_validation_report.txt")
