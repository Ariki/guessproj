#!python
# -*- coding: utf-8 -*-

from __future__ import unicode_literals
from __future__ import print_function

import sys
import os
from setuptools import setup

vinfo = sys.version_info
if vinfo < (2, 7) or (vinfo[0] == 3 and vinfo[1] < 3):
    raise NotImplementedError('Only Python 2.7+ or 3.3+ are supported')

import guessproj

setup(name='guessproj',
      version=guessproj.__version__,
      description='Script for guessing parameters of cartographic projection',
      long_description='''Script for guessing parameters
of cartographic projection''',
      author=guessproj.__author__,
      author_email='ardjakov@rambler.ru',
      url='https://github.com/Ariki/guessproj',
      install_requires=['pyproj', 'numpy', 'scipy'],
      extras_require={'WKT': ['GDAL']},
      py_modules=['guessproj'],
      scripts=['guessproj.py'],
      license=guessproj.__license__,
      platforms='any',
      classifiers=['Development Status :: 4 - Beta',
                   'Environment :: Console',
                   'Intended Audience :: Science/Research',
                   'License:: OSI Approved :: MIT License',
                   'Natural Language :: English',
                   'Operating Systems :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3.3',
                   'Programming Language :: Python :: 3.4',
                   'Topic :: Scientific/Engineering :: GIS',
                   ],
    )
