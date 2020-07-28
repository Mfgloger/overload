import os
import sys

p = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, p + "\\" + p.split("\\")[-1])
sys.path.insert(0, p)

from overload.datastore import session_scope, WCHit
from overload.db_worker import retrieve_record
from overload.bibs.crosswalks import xml2string, string2xml
from overload.bibs.xml_bibs import ONS, get_record_leader
from overload.connectors.worldcat.session import has_records

from overload.bibs.xml_bibs import (
    results2record_list,
    get_cat_lang,
    get_datafield_040,
    get_cuttering_fields,
    get_subject_fields,
)
from overload.wc2sierra.criteria import (
    meets_upgrade_criteria,
    meets_catalog_criteria,
    meets_user_criteria,
    create_rec_lvl_range,
    meets_rec_lvl,
    is_english_cataloging,
    meets_mat_type,
)
