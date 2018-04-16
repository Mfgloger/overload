# runs MarcEdit and local validation

from validators import marcedit
from errors import OverloadError
from setup_dirs import MVAL_REP


def validate_files(files, marcval=False, locval=False):
    valid_files = True
    if marcval:
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
    if locval:
        # placeholder; replace when local validation is developed
        raise OverloadError(
            'Local specs validation is still being developed.\n'
            'Uncheck the box to not display this warning')
    return valid_files
