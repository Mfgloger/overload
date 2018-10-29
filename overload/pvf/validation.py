# runs MarcEdit and local validation
import logging


from validators import marcedit, local_specs, default
from errors import OverloadError
from logging_setup import LogglyAdapter
from utils import remove_files
from setup_dirs import MVAL_REP, LSPEC_REP, DVAL_REP


module_logger = LogglyAdapter(logging.getLogger('overload'), None)


def validate_files(system, agent, files, marcval=False, locval=False):

    valid_files = True
    # mandatory, default validation

    try:
        dup_barcodes = default.barcode_duplicates(files, system)
        if dup_barcodes != {}:
            valid_files = False
        default.save_report(dup_barcodes, DVAL_REP)
    except OverloadError as e:
        module_logger.error(
            'Unable to create default validation report. '
            'Error: {}'.format(e))
        raise OverloadError(e)

    # MARCEdit MARC syntax validation
    if marcval:
        module_logger.debug('Running MARCEdit validation.')
        # make sure MARCEdit is installed on the machine
        val_engine = marcedit.get_engine()
        if val_engine is None:
            # display error message
            raise OverloadError(
                'Failed to locate cmarcedit.exe or marcrules.txt\n'
                'files of MARCEdit program. Unable to complete\n'
                'MARC validation. Please uncheck the box if you\n'
                'still want to proceed.')
        else:
            cme = val_engine[0]
            rules = val_engine[1]
            report_q = MVAL_REP
            overwrite = True
            for file in files:
                file_q = file
                success_process = marcedit.validate(
                    cme, file_q, report_q, rules, overwrite)
                overwrite = False
                if success_process:
                    result = marcedit.validation_check(MVAL_REP)
                    if not result[0]:
                        valid_files = False
                else:
                    valid_files = False
                    raise OverloadError(
                        'Encounted a problem with the file:\n'
                        '{}.\nNot able to validate in MARCEdit'.format(
                            file))

    # delete previous local spec report
    if not remove_files([LSPEC_REP]):
        module_logger.error(
            'Unable to delete pevious local spec validation report.')
        raise OverloadError(
            'Unable to remove previous local spec validation report.')

    # local specification validation
    if locval:
        module_logger.debug('Local specs validation launch.')

        # define local specs rules for each system, agent, and vendor
        try:
            rules = './rules/vendor_specs.xml'
            specs = local_specs.local_specs(system, agent, rules)
        except AttributeError as e:
            module_logger.error(
                'Unable to parse local specs rules.'
                'Error: {}'.format(e))
            raise OverloadError(e)

        # run the local specs validation
        locval_passed, report = local_specs.local_specs_validation(
            system, files, specs)
        if not locval_passed:
            valid_files = False

        # save the report to a file so the last batch is always remembered.
        try:
            with open(LSPEC_REP, 'w') as file:
                file.write(report)
        except IOError as e:
            module_logger.error(
                'Encountered error while creating local specs validation'
                ' report. Error: {}'.format(
                    e))
            raise OverloadError(
                'Unable to create local spec validation\nreport.')

    return valid_files
