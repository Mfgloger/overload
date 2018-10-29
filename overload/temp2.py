import logging
import logging.config
import sys
from logging_setup import DEV_LOGGING, LogglyAdapter, format_traceback
from setup_dirs import APP_DIR

logging.config.dictConfig(DEV_LOGGING)
logger = logging.getLogger('overload')
appLogger = LogglyAdapter(logger, {'version': '0.5.0'})


appLogger.info('Test')
appLogger.error('{}'.format(APP_DIR))
try:
	int('a')
except ValueError as exc:
	_, _, exc_traceback = sys.exc_info()
	appLogger.error('Error. {}'.format(format_traceback(exc, exc_traceback)))
