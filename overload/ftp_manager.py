import base64
from ftplib import FTP, error_reply, all_errors
import logging
from sqlalchemy.exc import IntegrityError


from datastore import FTPs, session_scope
from db_worker import insert_or_ignore, retrieve_values, retrieve_record, \
    delete_record
from errors import OverloadError

module_logger = logging.getLogger('overload_console.ftp_manager')


def store_connection(host, user, password, system):
    if host == '':
        host = None
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

        return (user, password)


def connect2FTP(host, user, password):
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


def disconnectFTP(ftp):
    try:
        ftp.quit()
        module_logger.info('Quiting FTP.')
    except error_reply:
        ftp.close()
        module_logger.info('Quiting FTP unsuccessful. Calling close method.')


if __name__ == '__main__':
    store_connection('', 'tomek', 'pass', 'nypl')
