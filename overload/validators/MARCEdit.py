import subprocess
import os
import shelve
import logging
import datetime


from logging_setup import LogglyAdapter
from setup_dirs import CVAL_REP, MVAL_REP, USER_DATA, USER_NAME


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def get_engine():

    module_logger.debug('Getting MARCEdit engine & MARC21 rules info')

    user_data = shelve.open(USER_DATA)
    # find cmarcedit.exe
    if 'cmarcedit' in user_data['paths'] and \
            os.path.exists(user_data['paths']['cmarcedit']):
        module_logger.debug('cmarcedit info found in user data file')
        cmarcedit = user_data['paths']['cmarcedit']
    else:
        # check most common location (may be deleted in the future)
        cmarcedit = 'C:/Program Files/MarcEdit 6/cmarcedit.exe'
        module_logger.debug(
            'checking if cmarcedit can be found in usual location: {}'.format(
                cmarcedit))
        if not os.path.exists(cmarcedit):
            cmarcedit = None
            module_logger.error(
                'MARCEdit not found on user {} machine'.format(
                    USER_NAME))

    # find validation rules
    if 'marc_rules' in user_data['paths'] and \
            os.path.exists(user_data['paths']['marc_rules']):
        # module_logger.debug('rules location info found in user data file')
        rules = user_data['paths']['marc_rules']
    else:
        appdata = os.environ['APPDATA']
        rules = appdata + '\\marcedit\\configs\\marcrules.txt'
        # module_logger.debug(
        #     'checking if rules can be found in usual location: {}'.format(
        #         rules))
        if not os.path.exists(rules):
            rules = None
            module_logger.error('MARC21 rules not found on user machine')

    user_data.close()

    # module_logger.debug('cmarcedit: {}, rules: {}'.format(
    #     cmarcedit, rules))

    if cmarcedit is not None and rules is not None:
        return cmarcedit, rules
    else:
        return None


def validate(cmarcedit, MARCfile, report, rules_fh, overwrite):

    """uses MARCEdit engine to validate records in a file"""

    args = [
        cmarcedit,
        '-validate',
        '-s', MARCfile,
        '-d', report,
        '-rules', rules_fh]

    module_logger.debug(
        'Begin MARCEdit validation with params: {}'.format(
            ' '.join(args)))
    try:
        si = subprocess.STARTUPINFO()
        si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        h = subprocess.check_output(
            args,
            stdin=subprocess.PIPE,
            stderr=subprocess.PIPE,
            startupinfo=si)
    except OSError as e:
        module_logger.exception(
            'MARCEdit validation error: {}'.format(
                str(e)))
        return False

    # delete combined report from previous batch process
    if overwrite:
        if os.path.isfile(CVAL_REP):
            module_logger.debug(
                'deleting previous batch MARCEdit validation report')
            try:
                os.remove(CVAL_REP)
            except WindowsError:
                module_logger.error('not able to delete previous batch report')

    if 'completed' in h:
        module_logger.debug('MARC file successfully processed by MARCEdit')

        with open(CVAL_REP, 'a') as combined_report:
            module_logger.debug('adding new report to the batch')
            combined_report.write(
                'timestamp: {}\nfile: {}\n'.format(
                    datetime.datetime.now(), MARCfile))
            combined_report.write('-' * 50 + '\n')
            marcedit_report = open(MVAL_REP, 'r')
            for line in marcedit_report:
                combined_report.write(line)
            combined_report.write(('-' * 50 + '\n') * 2)
            marcedit_report.close()
        return True
    else:
        module_logger.error(
            'MARCEdit encounted error while validating file: {}'.format(
                args[3]))
        with open(CVAL_REP, 'a') as combined_report:
            combined_report.write(
                'timestamp: {}\nMARCEdit validation could not'
                'be completed for {}.\n Please check the file.'.format(
                    datetime.datetime.now(),
                    MARCfile))
            combined_report.write('-' * 50 + '\n')
        return False


def validation_check(report):
    result = []
    passed = False
    with open(report, 'r') as file:
        for line in file:
            if "MARCValidator" in line:
                continue
            elif 'Rules File' in line:
                continue
            elif 'File:' in line:
                continue
            else:
                line = line.strip()
                result.append(line)
                if 'Invalid data' in line:
                    passed = False
                    break
                elif 'No errors were reported' in line:
                    passed = True
        return passed, result


def delete_validation_report():
    try:
        os.remove(CVAL_REP)
    except OSError:
        pass
