# this patch should move Platform/Sierra creds from python's shelf (user_data)
# to Windows Credential Manager

import shelve
import logging
import logging.handlers
import os
import sys
import base64
import keyring
from keyring.backends.Windows import WinVaultKeyring


# # set keyring backend
keyring.set_keyring(WinVaultKeyring())


def standard_from_vault(application, user):
    """
    gets password for appliction/user from Windows Credential Locker
    args:
        application
        user
    returns:
        password
    """

    password = keyring.get_password(application, user)
    return password


def standard_to_vault(application, user, password):
    """
    stores credentials in Windows Credential Locker
    args:
        applicaiton (name of application)
        user (name of user)
        password
    """

    # check if credentials already stored and if so
    # delete and store updated ones
    if not standard_from_vault(application, user):
        keyring.set_password(application, user, password)
    else:
        keyring.delete_password(application, user)
        keyring.set_password(application, user, password)


# run the patch
# setup patch logging
APP_DIR = os.path.join(os.environ['APPDATA'], 'Overload')
if not os.path.isdir(APP_DIR):
    os.mkdir(APP_DIR)
LOG_DIR = os.path.join(APP_DIR, 'changesLog')
if not os.path.isdir(LOG_DIR):
    os.mkdir(LOG_DIR)
PATCHING_RECORD = os.path.join(LOG_DIR, 'patching_record.txt')

LOG_FILENAME = os.path.join(LOG_DIR, 'changes_log.out')

patch_logger = logging.getLogger('patch_logger')
patch_logger.setLevel(logging.DEBUG)
handler = logging.handlers.RotatingFileHandler(
    LOG_FILENAME, maxBytes=1024 * 1024, backupCount=5)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
patch_logger.addHandler(handler)


patch_logger.info('Initiating patch 0.0.2.')

applied = False

try:
    with open(PATCHING_RECORD, 'r') as file:
        if '0.0.2' in [line[:5] for line in file.readlines()]:
            # skip patching in this case
            patch_logger.debug('patch 0.0.2 already installed')
            applied = True
except IOError:
    # file does not exist
    patch_logger.info('patching_record.txt does not exist - will create one')
    pass

if not applied:
    # check if user_data present
    user_data = os.path.join(APP_DIR, 'user_data')
    if os.path.exists(user_data):
        patch_logger.debug('User_data locatated at: {}'.format(user_data))

        user_data = shelve.open(user_data, writeback=True)
        try:
            patch_logger.info(
                'Retrieving Platform credentials from user_data.')
            for k, v in user_data['PlatformAPIs'].iteritems():
                patch_logger.info('Decoding client_id for {}.'.format(k))
                client_id = base64.b64decode(v['client_id'])
                patch_logger.info('Decoding client_secret for {}'.format(k))
                client_secret = base64.b64decode(
                    v['client_secret'])
                auth_server = v['oauth_server']
                # store creds in the vault
                patch_logger.info('Moving {} credentials to the vault.'.format(
                    k))
                standard_to_vault(auth_server, client_id, client_secret)

                # check if sucessful
                vault_secret = standard_from_vault(auth_server, client_id)
                if vault_secret == client_secret:
                    patch_logger.info(
                        'Credentials for {} successfully stored '
                        'in vault.'.format(k))
                    # create a record for the patch so it can be skipped in the
                    # future
                    with open(PATCHING_RECORD, 'a') as file:
                        file.write(
                            '0.0.2  (moves stored NYPL Platform credentials '
                            'to Windows Credentials Manager)\n')
                else:
                    patch_logger.error(
                        'Credentials for {}={}:{} corrupted '
                        'in the vault.'.format(
                            k, auth_server, client_id))
                # delete secret from the shelf
                patch_logger.info('Removing secret for {}'.format(k))
                del v['client_secret']

        except KeyError:
            patch_logger.info(
                'Platform credentials not present')
            with open(PATCHING_RECORD, 'a') as file:
                file.write(
                    '0.0.2  - not requried, skipped (moves stored NYPL '
                    'Platform credentials '
                    'to Windows Credentials Manager)\n')

        except Exception as e:
            patch_logger.error('Encountered unexpected error.', exc_info=True)

        finally:
            user_data.close()

    else:
        patch_logger.error('user_data file not found on the machine.')
