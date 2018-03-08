# defines directories and files needed for running Overload

import os

APP_DIR = os.environ['APPDATA'] + r'\Overload'
MY_DOCS = os.path.expanduser(os.sep.join(["~", "Documents"]))
TEMP_DIR = APP_DIR + r'\temp'
SUMMARIES_DIR = r'S:\CATAL\BookOps Apps\Overload STATS'
USER_DATA = APP_DIR + r'\user_data'
USER_STATS = APP_DIR + r'\user_stats.csv'
BATCH_STATS = TEMP_DIR + r'\session_report.db'
VENDOR_STATS = SUMMARIES_DIR + r'\vendor_totals.csv'
MVAL_REP = TEMP_DIR + r'\marcedit_validation_report.txt'
CVAL_REP = TEMP_DIR + r'\combined_validation_report.txt'
