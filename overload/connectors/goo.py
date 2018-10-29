# module responsible for communicaton with google tools
from googleapiclient import discovery
from httplib2 import Http
from oauth2client import client, tools
from oauth2client.contrib import keyring_storage


from connectors.goo_settings import sheet_templates
from errors import OverloadError


def store_access_token(application, user, credentials, scopes):
    """
    stores token enabling requests to google drive
    args:
        application: string, name of application
        credentials: string, path to credentials.json
        scope: string or list of scopes
    retuns:
        access token
    """

    store = keyring_storage.Storage(application, user)
    token = store.get()
    if not token or token.invalid:
        flow = client.flow_from_clientsecrets(credentials, scopes)
        token = tools.run_flow(flow, store)
    return token


def get_access_token(application, user):
    """
    retrieves token from credential manager
    args:
        applicaiton: string, name of application
        user: string, name of user
    returns:
        access token
    """

    store = keyring_storage.Storage(application, user)
    token = store.get()
    if not token or token.invalid:
        raise OverloadError(
            'Overload client is missing Google API authorization.')
    return token


def create_sheet(auth, sheet_name, tabs=[]):
    """
    creates google spreadsheet in specified folder
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        sheet name: string, name of Google sheet
        tabs: list, list of sheet tabs to be created
    returns:
        sheet_id: string, id of newly created Google Sheet
    """

    service = discovery.build('sheets', 'v4', credentials=auth)
    sheet_props = []
    for tab_name in tabs:
        sheet_props.append(
            dict(
                properties=dict(title=tab_name)))

    spreadsheet_body = {
        'sheets': sheet_props,
        'properties': {
            'title': sheet_name,
            'locale': 'en',
            'autoRecalc': 'ON_CHANGE',
            'timeZone': 'America/New_York'
        }
    }

    # create spreadsheet
    request = service.spreadsheets().create(
        body=spreadsheet_body)
    response = request.execute()

    return response['spreadsheetId']


def file2folder(auth, parent_id, file_id):
    """
    move file with provided id to appropriate folder
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        parent_id: string, Google Drive folder id
        file_id: string, Google Drive document id
    returns:
        boolean: True if operation successful, False if not
    """

    service = discovery.build('drive', 'v3', http=auth.authorize(Http()))
    file = service.files().get(
        fileId=file_id,
        fields='parents').execute()
    previous_parents = ",".join(file.get('parents'))
    # Move the file to the new folder
    response = service.files().update(
        fileId=file_id,
        addParents=parent_id,
        removeParents=previous_parents,
        fields='id, parents').execute()

    try:
        if response['parents'] == [parent_id]:
            return True
        else:
            return False
    except KeyError:
        return False


def get_latest_file_id_in_folder(auth, file_name, parent_id):
    """
    retrieves spreadsheet id of the current overload report
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        file_name: strig, name of file on Google Drive
        parent_id: string, Google Drive id of foler where the file resides
    returns:
        file_id: string, Google Drive id of file
    """

    # run drive query to find sheet id

    # compose query
    query = "mimeType='application/vnd.google-apps.spreadsheet' and " \
            "'{}' in parents and " \
            "name='{}'".format(
                parent_id,
                file_name)

    # run the query
    service = discovery.build('drive', 'v3', http=auth.authorize(Http()))
    response = service.files().list(
        q=query,
        pageSize=5,
        fields='nextPageToken, files(createdTime, id)').execute()

    items = response.get('files', [])
    if items == []:
        return None
    else:
        # pick the latest one (first one in returned items)
        return items[0]['id']


def append2sheet(auth, sheet_id, range_name, data):
    """
    appends data to Google sheet with provided id
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        sheet_id: string
        data: list of lists for each row
    returns:
        results: dictionary, Google API response
    """

    service = discovery.build('sheets', 'v4', credentials=auth)
    value_input_option = 'RAW'
    body = {
        'values': data,
    }
    result = service.spreadsheets().values().append(
        spreadsheetId=sheet_id, range=range_name,
        valueInputOption=value_input_option, body=body).execute()

    return result


def customize_bpl_pvf_dup_report(auth, sheet_id):
    """
    customizes overload report for BPL data
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        sheet_id: string, Google Sheet id
    """

    service = discovery.build('sheets', 'v4', credentials=auth)

    header = [
        'date', 'agency', 'vendor', 'vendor_id', 'target_id',
        'dups', 'corrected', 'comments']
    value_input_option = 'RAW'

    # main tab (sheet)
    body = {
        'values': [header]
    }
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id, range='duplicates',
        valueInputOption=value_input_option, body=body).execute()

    # get sheets ids and loop
    request = service.spreadsheets().get(
        spreadsheetId=sheet_id, ranges=[
            'duplicates'], includeGridData=False)
    response = request.execute()
    tab_ids = [
        sheet['properties']['sheetId'] for sheet in response['sheets']]

    # customize the look & behavior of each sheet
    for tab_id in tab_ids:
        request_body = sheet_templates.bpl_pfv_dup_report_template(tab_id)

        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=request_body).execute()


def customize_pvf_callNos_report(auth, sheet_id):
    """
    cutomizes overload PVF report for BPL data
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        sheet_id: string, Google Sheet id 
    """

    service = discovery.build('sheets', 'v4', credentials=auth)

    # create header
    header = [
        'date', 'vendor', 'vendor_id', 'target_id',
        'vendor CallNo', 'target CallNo',
        'duplicate bibs', 'corrected', 'comments']
    value_input_option = 'RAW'
    body = {
        'values': [header]
    }
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id, range='errors',
        valueInputOption=value_input_option, body=body).execute()

    request = service.spreadsheets().get(
        spreadsheetId=sheet_id, ranges=[
            'errors'], includeGridData=False)
    response = request.execute()

    # apply formatting template to each tab
    tab_ids = [
        sheet['properties']['sheetId'] for sheet in response['sheets']]

    # customize the look & behavior of each sheet
    for tab_id in tab_ids:
        request_body = sheet_templates.pvf_callNo_report_template(
            tab_id)
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=request_body).execute()


def customize_nypl_pvf_dup_report(auth, sheet_id):
    """
    customizes overload PVF report for NYPL data
    args:
        auth: class 'oauth2client.client.OAuth2Credentials'
        sheet_id: string, Google Sheet id
    """

    service = discovery.build('sheets', 'v4', credentials=auth)

    branch_header = [
        'date', 'agency', 'vendor', 'vendor_id', 'target_id',
        'branches_dups', 'mixed', 'research_dups', 'corrected',
        'comments']
    research_header = [
        'date', 'agency', 'vendor', 'vendor_id', 'target_id',
        'research_dups', 'mixed', 'branches_dups', 'corrected',
        'comments']
    value_input_option = 'RAW'

    # create branches tab
    body = {
        'values': [branch_header]
    }
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id, range='branches',
        valueInputOption=value_input_option, body=body).execute()

    # create research tab
    body = {
        'values': [research_header]
    }
    service.spreadsheets().values().append(
        spreadsheetId=sheet_id, range='research',
        valueInputOption=value_input_option, body=body).execute()

    # get tab ids and loop
    request = service.spreadsheets().get(
        spreadsheetId=sheet_id, ranges=[
            'branches', 'research'], includeGridData=False)
    response = request.execute()

    # apply formatting template to each tab
    tab_ids = [
        sheet['properties']['sheetId'] for sheet in response['sheets']]

    # customize the look & behavior of each sheet
    for tab_id in tab_ids:
        request_body = sheet_templates.nypl_pvf_dup_report_template(
            tab_id)
        service.spreadsheets().batchUpdate(
            spreadsheetId=sheet_id,
            body=request_body).execute()
