LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,  # this fixes the problem
    'formatters': {
        'brief': {
            'format': '%(name)s-%(asctime)s-%(filename)s-%(lineno)s-%(levelname)s-%(levelno)s-%(message)s'
        },
        'standard': {
            'format': '{"loggerName":"%(name)s", "asciTime":"%(asctime)s", "fileName":"%(filename)s", "logRecordCreationTime":"%(created)f", "levelNo":"%(levelno)s", "lineNo":"%(lineno)d", "levelName":"%(levelname)s", "message":"%(message)s"}'
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'brief'
        },
        'loggly_standard': {
            'level': 'INFO',
            'class': 'loggly.handlers.HTTPSHandler',
            'formatter': 'standard',
            'url': 'https://logs-01.loggly.com/inputs/[TOKEN]/tag/python',
        },
    },
    'loggers': {
        'main': {
            'handlers': ['console'],  # add loggly_standard after the tests
            'level': 'INFO',
            'propagate': True
        },
        'tests': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}
