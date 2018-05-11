LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
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
        'loggly': {
            'level': 'DEBUG',
            'class': 'loggly.handlers.HTTPSHandler',
            'formatter': 'standard',
            'url': 'https://logs-01.loggly.com/inputs/[token]/tag/python',
        },
    },
    'loggers': {
        'overload_main': {
            'handlers': ['loggly'],
            'level': 'DEBUG',
            'propagate': True
        },
        'overload_console': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True
        }
    }
}
