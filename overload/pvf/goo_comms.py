# handles PVF communication with Google Drive
from datetime import date
import logging


from connectors import goo
from errors import OverloadError
from logging_setup import LogglyAdapter


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def determine_quarter(date_obj):
    curr_month = date_obj.month
    if curr_month in (7, 8, 9):
        curr_quarter = '1Q'
    elif curr_month in (10, 11, 12):
        curr_quarter = '2Q'
    elif curr_month in (1, 2, 3):
        curr_quarter = '3Q'
    elif curr_month in (4, 5, 6):
        curr_quarter = '4Q'

    return curr_quarter


def determine_fiscal_year(date_obj, quarter):
    curr_year = date_obj.year
    if quarter in ["1Q", "2Q"]:
        curr_fiscal_year = "{}/{}".format(curr_year, str(curr_year + 1)[2:])
    elif quarter in ["3Q", "4Q"]:
        curr_fiscal_year = "{}/{}".format(curr_year -1, str(curr_year)[2:])

    return curr_fiscal_year



def name_pvf_sheet(report_type):
    """
    determines sheet name of the current report
    args:
        report_type: string, 'dups', 'callNos', 'details'
    returns:
        sheet_name: string, name of the sheet

    sheet name patters:
    overload-dups-2018-1Q   (2018, first quarter)
    overload-callnos-2018-2Q    (2018, second quarter)
    overload-details-2018-01    (2018, January)

    """

    date_today = date.today()
    curr_quarter = determine_quarter(date_today)
    curr_year = determine_fiscal_year(date_today, curr_quarter)

    # determine current sheet name for each type
    if report_type == 'dups':
        # determine current spreadsheet name
        sheet_name = 'Overload Dups {}-{}'.format(
            curr_year, curr_quarter)
    elif report_type == 'callnos':
        # determine current spreadsheet name
        sheet_name = 'Overload CallNumbers {}-{}'.format(
            curr_year, curr_quarter)
    elif report_type == 'details':
        # determine current spreadsheet name
        sheet_name = 'Overload Detailed {}-{:02d}'.format(
            curr_year, curr_month)
    else:
        raise ValueError(
            'Incorrect report type on '
            'get_current_nypl_overload_report_id method. '
            'Allowed types: dups, callnos, details')
    return sheet_name


def create_sheet_for_system(system, auth, sheet_name, tabs, parent_id=None):
    """
    creates Google Sheet of given name, with layout for
    NYPL report
    args:
        system: string, 'NYPL' or 'BPl'
        auth: class 'oauth2client.client.OAuth2Credentials'
        sheet_name: string, name of the spreadsheet
        tabs: list, names of individual sheets
    returns:
        sheet_id: string, GDrive assigned id
    """

    sheet_id = goo.create_sheet(
        auth, sheet_name, tabs)

    # customize it
    if 'CallNumbers' in sheet_name:
        goo.customize_pvf_callNos_report(auth, sheet_id)
    elif 'Dups' in sheet_name and system == 'NYPL':
        goo.customize_nypl_pvf_dup_report(auth, sheet_id)
    elif 'Dups' in sheet_name and system == 'BPL':
        goo.customize_bpl_pvf_dup_report(auth, sheet_id)

    # move sheet to appropriate folder
    if not goo.file2folder(auth, parent_id, sheet_id):
        module_logger.error(
            'Unable to move sheet {} to folder {}.'.format(
                sheet_id, parent_id))
        raise OverloadError(
            'Failed to move {} document to '
            'correct GDrive folder'.format(
                sheet_name))

    return sheet_id
