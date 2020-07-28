import os
import sys

p = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, p + "\\" + p.split("\\")[-1])
sys.path.insert(0, p)


from overload import setup_dirs
from overload.connectors.sierra_z3950 import z3950_query
from overload.connectors.platform import AuthorizeAccess, PlatformSession
from overload.connectors import goo
from overload.connectors.goo_settings.access_names import GAPP, GUSER
from overload.connectors.worldcat.accesstoken import WorldcatAccessToken
from overload.connectors.worldcat.metadata_session import (
    construct_sru_query,
    holdings_responses,
)
from overload import credentials
from overload.utils import *
from overload.bibs import (
    bibs,
    crosswalks,
    patches,
    dedup,
    parsers,
    sierra_dicts,
)
from overload.bibs.nypl_callnum import (
    remove_special_characters,
    create_nypl_callnum,
)
from overload.bibs.bpl_callnum import (
    create_bpl_callnum,
    has_division_conflict,
    is_adult_division,
)
from overload.bibs.callnum import (
    determine_cutter,
    determine_biographee_name,
    valid_audience,
)
from overload.bibs import xml_bibs
from overload.pvf import vendors
from overload.pvf.analyzer import PVRReport, PVR_NYPLReport
from overload.pvf import reports
from overload.pvf import goo_comms
from overload.errors import OverloadError, APITokenError, APITokenExpiredError
from overload.validators import local_specs, default
from overload.wc2sierra.source_parsers import (
    sierra_export_data,
    find_order_field,
    find_latest_full_order,
    parse_order_data,
    parse_BPL_order_export,
    parse_NYPL_order_export,
)
