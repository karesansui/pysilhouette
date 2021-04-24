#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This file is part of Pysilhouette.
#
# Copyright (c) 2009 HDE, Inc.
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

import sys
import os
import unittest
import pysilhouette.prep

class TestPrep(unittest.TestCase):

    _sysappend0 = ['hoge', 'foo']
    _sysappend1 = []
    _sysappend2 = ''
    _sysappend3 = None

    _tmpfile = None

    def setUp(self):
        # readconf
        import tempfile
        self._tmpfile = tempfile.mkstemp()
        fp = open(self._tmpfile[1], 'w')
        fp.write('key0=value0\n')
        fp.write('key1 =value1\n')
        fp.write('key2= value2\n')
        fp.write('key3 = value3\n')
        fp.write('#key4=value4\n')
        fp.write('k#ey5=value5\n')
        fp.close()
        pass
    
    def tearDown(self):
        os.unlink(self._tmpfile[1])
        pass
        
    def test_sysappend_0(self):
        ret = pysilhouette.prep.sysappend(self._sysappend0)
        self.assertEqual(ret, True)
        for target in self._sysappend0:
            val = False
            for line in sys.path:
                if target == line:
                    val = True
            if val is False:
                self.fail('sys.path insert error!!')

    def test_sysappend_1(self):
        ret = pysilhouette.prep.sysappend(self._sysappend1)
        self.assertEqual(ret, True)

    def test_sysappend_2(self):
        ret = pysilhouette.prep.sysappend(self._sysappend2)
        self.assertEqual(ret, False)

    def test_sysappend_3(self):
        ret = pysilhouette.prep.sysappend(self._sysappend3)
        self.assertEqual(ret, False)

    def test_readconf_0(self):
        ret = pysilhouette.prep.readconf(self._tmpfile[1])
        if ret['key0'] != 'value0':
            self.fail()
        if ret['key1'] != 'value1':
            self.fail()
        if ret['key2'] != 'value2':
            self.fail()
        if ret['key3'] != 'value3':
            self.fail()
        try:
            if ret['#key4'] != 'value4':
                self.fail()
        except KeyError:
            pass
        if ret['k#ey5'] != 'value5':
            self.fail()

class SuiteSysappend(unittest.TestSuite):
    def __init__(self):
        tests = ['test_sysappend_0', 'test_sysappend_1',
                 'test_sysappend_2', 'test_sysappend_3']
        unittest.TestSuite.__init__(self,list(map(TestPrep, tests)))

class SuiteReadconf(unittest.TestSuite):
    def __init__(self):
        tests = ['test_readconf_0']
        unittest.TestSuite.__init__(self,list(map(TestPrep, tests)))

def all_suite_prep():
    return unittest.TestSuite([SuiteSysappend(), SuiteReadconf()])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(all_suite_prep())
