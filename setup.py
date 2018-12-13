#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


# Package meta-data.
NAME = 'overload'
DESCRIPTION = 'BookOps toolbox.'
URL = 'https://github.com/BookOps/overload'
EMAIL = 'klingaroo@gmail.com'
AUTHOR = 'Tomek Kalata'
REQUIRES_PYTHON = '>=2.7.13'
VERSION = None

# Requiared packages
REQUIRED = [
    "altgraph==0.15",
    "cachetools==2.1.0",
    "certifi==2017.7.27.1",
    "chardet==3.0.4",
    "configparser==3.5.0",
    "dis3==0.1.2",
    "entrypoints==0.2.3",
    "funcsigs==1.0.2",
    "future==0.16.0",
    "futures==3.1.1",
    "google-api-python-client==1.7.4",
    "google-auth==1.5.1",
    "google-auth-httplib2==0.0.3",
    "httplib2==0.11.3",
    "idna==2.6",
    "keyring==15.1.0",
    "loggly-python-handler==1.0.0",
    "macholib==1.9",
    "mock==2.0.0",
    "numpy==1.13.1",
    "oauth2client==4.1.3",
    "oauthlib==2.0.4",
    "pandas==0.20.3",
    "pbr==3.1.1",
    "pefile==2018.8.8",
    "pyasn1==0.4.4",
    "pyasn1-modules==0.2.2",
    "pycryptodome==3.6.6",
    "PyInstaller==3.4",
    "pymarc==3.1.7",
    "pypiwin32==223",
    "python-dateutil==2.6.1",
    "pytz==2017.2",
    "pywin32==224",
    "pywin32-ctypes==0.2.0",
    "PyZ3950==2.04",
    "requests==2.20.0",
    "requests-futures==0.9.7",
    "requests-mock==1.4.0",
    "requests-oauthlib==0.8.0",
    "rsa==4.0",
    "six==1.11.0",
    "SQLAlchemy==1.2.6",
    "uritemplate==3.0.0",
    "urllib3==1.24.1"
]

# requires manual installation of Aaron Lav's PyZ3950
# see details here: http://www.panix.com/~asl2/software/PyZ3950/

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

setup(
    name=NAME,
    version=VERSION,
    description=DESCRIPTION,
    long_description=readme,
    author='Tomasz Kalata',
    author_email=EMAIL,
    url=URL,
    packages=find_packages(exclude=('tests',)),
    install_requires=REQUIRED,
    include_package_data=True,
    license=license,
    classifiers=[
        # Trove classifiers
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7'
    ]
)

here = os.path.abspath(os.path.dirname(__file__))

about = {}
if not VERSION:
    with open(os.path.join(here, NAME, '__version__.py')) as f:
        exec(f.read(), about)
else:
    about['__version__'] = VERSION
