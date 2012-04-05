#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# This file is part of Pysilhouette.
#
# Copyright (c) 2009-2010 HDE, Inc.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
# 

"""
@author: Kei Funagayama <kei@karesansui-project.info>
"""

from setuptools import setup, find_packages
import glob
import os
import sys
# DISTUTILS_DEBUG=1
from pysilhouette import __app__, __version__, __release__

__prog__ = 'silhouette'
__progd__='%sd' % __prog__

setup(name=__app__,
    version= "%s.%s" % (__version__, __release__),
    description='A python-based background job manager',
    long_description="""Pysilhouette is a python-based background job manager,
    intended to co-work with various python-based web applications.
    It makes it available to get job status to programmers,
    which was difficult in http-based stateless/interactive session before.
    100% Pure Python.""",
    maintainer='Taizo ITO',
    maintainer_email='taizo@karesansui-project.info',
    url='http://sourceforge.jp/projects/pysilhouette/',
    download_url='',
    packages=['pysilhouette',
              'pysilhouette.db',
              'pysilhouette.tests',
              ],
    py_modules = ['pkg_resources', 'easy_install', 'site'],
    zip_safe = (sys.version>="2.5"),   # <2.5 needs unzipped for -m to work
    entry_points = {
        "egg_info.writers": [
            "PKG-INFO = setuptools.command.egg_info:write_pkg_info",
            "requires.txt = setuptools.command.egg_info:write_requirements",
            "entry_points.txt = setuptools.command.egg_info:write_entries",
            "top_level.txt = setuptools.command.egg_info:write_toplevel_names",
            "dependency_links.txt = setuptools.command.egg_info:overwrite_arg",
        ],
    },

    scripts=[],
    license='The MIT License',
    keywords='',
    platforms='Linux',
    classifiers=['Environment :: No Input/Output (Daemon)',
                 'License :: OSI Approved :: MIT License',
                 'Natural Language :: Japanese',
                 'Programming Language :: Python :: 2.4',
                 ],
)

