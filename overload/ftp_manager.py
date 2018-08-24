import json
import base64

from ftplib import FTP, all_errors
import logging
from sqlalchemy.exc import IntegrityError


from datastore import FTPs, session_scope
from db_worker import insert_or_ignore, retrieve_values, retrieve_record, \
    delete_record
from errors import OverloadError
from utils import convert2date_obj

module_logger = logging.getLogger('overload_console.ftp_manager')


def store_connection(host, folder, user, password, system):
    if host == '':
        host = None
    if folder == '':
        folder = None
    if system == '':
        system = None
    if user == '':
        user = None
    else:
        user = base64.b64encode(user)
    if password == '':
        password = None
    else:
        password = base64.b64encode(password)

    try:
        with session_scope() as db_session:
            insert_or_ignore(
                db_session,
                FTPs,
                host=host,
                folder=folder,
                user=user,
                password=password,
                system=system)
    except IntegrityError as e:
        module_logger.error(e)
        raise OverloadError(
            'Please provide missing host address')


def delete_connection(host, system):
    with session_scope() as db_session:
        try:
            delete_record(
                db_session,
                FTPs,
                host=host,
                system=system)
        except Exception as e:
            module_logger.error(e)
            raise OverloadError(e)


def get_ftp_connections(system):
    with session_scope() as db_session:
        names = retrieve_values(
            db_session,
            FTPs,
            'host',
            system=system)
        return [x.host for x in names]


def get_connection_details(host, system):
    with session_scope() as db_session:
        record = retrieve_record(
            db_session,
            FTPs,
            host=host,
            system=system)
        if record.user:
            user = base64.b64decode(record.user)
        else:
            user = ''
        if record.password:
            password = base64.b64decode(record.password)
        else:
            password = ''

        return (user, password, record.folder)


def connect2ftp(host, user, password):
    module_logger.info('Connecting to FTP: {}.'.format(
        host))
    try:
        ftp = FTP(host)
        conn = ftp.login(user, password)
        if conn[:3] == '230':
            module_logger.debug(
                'Successful connection.')
            return ftp
        else:
            module_logger.error(
                'Unsuccessful connection attempt: {}.'.format(
                    conn))
            raise OverloadError(
                'Unable to connect to FTP.\n'
                'Error: {}'.format(conn))
    except all_errors as e:
        module_logger.error('Unable to connect to: {}. {}'.format(
            host, e))
        raise OverloadError(
            'Unable to connect to: {}.\n'
            'Verify host and your credentials'.format(
                host))


def disconnect_ftp(ftp):
    try:
        ftp.quit()
        module_logger.info('Quiting FTP.')
    except all_errors:
        ftp.close()
        module_logger.info('Quiting FTP unsuccessful. Calling close method.')


def read_ftp_content(ftp, host):
    module_logger.info(
        'Accessing FTP ({}) directory & file listing'.format(
            host))
    # create a list of directories and files
    ls = []
    try:
        ftp.retrlines('LIST', ls.append)
    except all_errors as e:
        module_logger.error(
            'Unable to retrieve file & directory list on FTP host {}.'
            'Error: {}'.format(host, e))
        raise OverloadError(
            'Encountered error while retrieving\n'
            'content of the FTP server.')

    # load available FTP parsing methods
    try:
        ftp_settings = open('./rules/ftp_parsing.json', 'r')
        fs = json.load(ftp_settings)
    except ValueError as e:
        module_logger.error(
            'FTP settings JSON file malformed. Error: {}'.format(
                e))
        raise OverloadError('Unable to access FTP parsing methods')
    finally:
        ftp_settings.close()

    # determine FTP server response parsing
    try:
        m = fs[host]
    except KeyError:
        module_logger.error(
            'Accessing parsing info for unidentified FTP host: {}'.format(
                host))
        raise OverloadError(
            'Unidentified FTP host.')
    if m:
        dirs = []
        files = []
        try:
            for l in ls:
                if l[m['dir_mark'][1]:m['dir_mark'][2] + 1] == \
                        m['dir_mark'][0]:
                    d = l[m['dir_handle']:].strip()
                    dirs.append(d)
                elif l[m['file_mark'][1]:m['file_mark'][2] + 1] == \
                        m['file_mark'][0]:
                    f = l[m['file_handle']:].strip()
                    s = l[m['file_size_pos'][0]:m[
                        'file_size_pos'][1] + 1].strip()

                    # timestamp 
                    t = l[m['file_time_pos'][0]:m[
                        'file_time_pos'][1] + 1].strip()
                    patterns = m['time_patterns']
                    for p in patterns:
                        try:
                            t = convert2date_obj(t, p)
                            break
                        except ValueError:
                            pass
                    files.append((f, s, t))
            return (dirs, files)
        except KeyError as e:
            module_logger.error(
                'FTP parsing settings for {} are malformed. Error: {}'.format(
                    host, e))
            raise OverloadError(
                'FTP parsing settings error.')
        except IndexError as e:
            module_logger.error(
                'FTP parsing settigns for {} are incorrect. Error: {}'.format(
                    host, e))
            raise OverloadError(
                'FTP parsing settings error.')
    else:
        module_logger.error(
            'Unable to parse FTP response to LIST cmd on host {}'.format(
                host))
        raise OverloadError('Unable to parse FTP response.')


def move2ftp(host, ftp, fh, dstfh, transfer_type):
    try:
        module_logger.debug(
            'Uploading file to FTP: host={}, local path={}, '
            'destination fh={}, transfer type={}'.format(
                host, fh, dstfh, transfer_type))
        if transfer_type == 'binary':
            ftp.storbinary('STOR {}'.format(dstfh), open(fh, 'rb'))
        elif transfer_type == 'ASCII':
            ftp.storlines('STOR {}'.format(dstfh), open(fh, 'r'))
        module_logger.debug(
            'Upload successful.')

    except all_errors as e:
        module_logger.error(
            'Upload to FTP failed: host={}, destination fh={}, '
            'transfer type={}. Error: {}'.format(
                host, dstfh, transfer_type, e))
        raise OverloadError(
            'Encountered error while uploading file to FTP.\nAborting.')


def move2local(host, ftp, fh, dstfh, transfer_type):
    try:
        module_logger.debug(
            'Downloading file from FTP: host={}, fh={}, destination path={}, '
            'transfer type={}'.format(
                host, fh, dstfh, transfer_type))
        if transfer_type == 'binary':
            with open(dstfh, 'wb') as f:
                ftp.retrbinary('RETR %s' % fh, lambda data: f.write(data))
        elif transfer_type == 'ASCII':
            with open(dstfh, 'w') as f:
                ftp.retrlines('RETR %s' % fh, lambda data: f.write(data))
        module_logger.debug(
            'Download successful.')

    except all_errors as e:
        module_logger.error(
            'Download from FTP failed: host={}, file on remote={}, '
            'destination path={}, transfer type={}. Error: {}'.format(
                host, fh, dstfh, transfer_type, e))
        raise OverloadError('Encountered error while downloading the file.')
