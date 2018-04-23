#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
from setuptools import setup, find_packages


# Package meta-data.
NAME = 'overload'
DESCRIPTION = 'BookOps toolbox.'
URL = 'https://github.com/BookOps/overload'
EMAIL = 'klingaroo@gmail.com'
AUTHOR = 'Tomasz Kalata'
REQUIRES_PYTHON = '>=2.7.13'
VERSION = None

# Requiared packages
REQUIRED = [
    "certifi==2017.7.27.1",
    "chardet==3.0.4",
    "funcsigs==1.0.2",
    "futures==3.1.1",
    "idna==2.6",
    "loggly-python-handler==1.0.0",
    "mock==2.0.0",
    "numpy==1.13.1",
    "oauthlib==2.0.4",
    "pandas==0.20.3",
    "pbr==3.1.1",
    "pymarc==3.1.7",
    "python-dateutil==2.6.1",
    "pytz==2017.2",
    "requests==2.18.4",
    "requests-futures==0.9.7",
    "requests-mock==1.4.0",
    "requests-oauthlib==0.8.0",
    "six==1.11.0",
    "SQLAlchemy==1.2.6",
    "urllib3==1.22"
]

with open('README.md') as f:
    readme = f.read()

with open('LICENSE') as f:
    license = f.read()

# requires manual installation of Aaron Lav's PyZ3950
# see details here: http://www.panix.com/~asl2/software/PyZ3950/

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
