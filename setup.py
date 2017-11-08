#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import sys
import os
from setuptools import setup

import guessproj


vinfo = sys.version_info
if vinfo < (2, 6) or (vinfo[0] == 3 and vinfo[1] < 3):
    raise NotImplementedError('Only Python 2.6+ or 3.3+ are supported')


def read_file(filename):
    full_name = os.path.join(os.path.dirname(__file__), filename)
    with open(full_name, 'r') as fp:
        return fp.read()


setup(
    name='guessproj',
    version=guessproj.__version__,
    description='Script for guessing parameters of cartographic projection',
    long_description=read_file('README.rst'),
    author=guessproj.__author__,
    author_email='ardjakov@rambler.ru',
    url='https://github.com/Ariki/guessproj',
    install_requires=['pyproj', 'numpy', 'scipy'],
    extras_require={'WKT': ['GDAL']},
    py_modules=['guessproj'],
    entry_points={
        'console_scripts': ['guessproj = guessproj:main'],
    },
    license=guessproj.__license__,
    platforms='any',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Scientific/Engineering :: GIS',
        'Topic :: Utilities',
    ],
)
