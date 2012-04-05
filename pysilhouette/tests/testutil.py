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

import os
import unittest
import pysilhouette.util as target

class TestUtil(unittest.TestCase):

    fname = '/tmp/testutil.fifo'
    pname = '/tmp/testutil.pid'

    def setUp(self):
        pass
    
    def tearDown(self):
        pass

    def unlink(self, name):
        try:
            os.unlink(name)
        except:
            pass

    def test_popen_0(self):
        cmd = target.split_shell_command('date')
        (proc, proc_info) = target.popen(cmd)
        self.assertTrue(proc_info['r_code'] == 0)
        
    def test_popen_1(self):
        cmd = target.split_shell_command('cat *')
        (proc, proc_info) = target.popen(cmd)
        self.assertTrue(proc_info['r_code'] == 1)

    def test_split_shell_command_0(self):
        ret = target.split_shell_command('date')
        self.assertTrue(type(ret) is list)
        self.assertTrue(len(ret) == 1)
        self.assertTrue(ret[0] == 'date')

        ret = target.split_shell_command('date -a')
        self.assertTrue(type(ret) is list)
        self.assertTrue(len(ret) == 2)
        self.assertTrue((ret[0] == 'date' and ret[1] == '-a'))
        

        ret = target.split_shell_command(' date  -a ')
        self.assertTrue(type(ret) is list)
        self.assertTrue(len(ret) == 2)
        self.assertTrue((ret[0] == 'date' and ret[1] == '-a'))

        ret = target.split_shell_command('    date               -a        ')
        self.assertTrue(type(ret) is list)
        self.assertTrue(len(ret) == 2)
        self.assertTrue((ret[0] == 'date' and ret[1] == '-a'))
        
    def test_split_shell_command_1(self):
        self.assertFalse(target.split_shell_command(None))


    def test_is_empty_0(self):
        self.assertFalse(target.is_empty('cmd'))
        self.assertFalse(target.is_empty(' cmd '))
        self.assertFalse(target.is_empty(' cmd'))
        self.assertFalse(target.is_empty('cmd -a '))
        self.assertFalse(target.is_empty('cmd -a  '))
        self.assertFalse(target.is_empty('cmd -a /hoge'))
        self.assertFalse(target.is_empty('cmd -a -as'))
        self.assertFalse(target.is_empty('cmd a -as'))
        self.assertTrue(target.is_empty(''))
        self.assertTrue(target.is_empty(' '))
        self.assertTrue(target.is_empty(None))

    def test_create_fifo_0(self):
        self.unlink(self.fname)
        ret = target.create_fifo(self.fname,'satori','pysilhouette','0641')
        self.assertTrue(ret)
        self.unlink(self.fname)

    def test_create_fifo_1(self):
        target.create_fifo(self.fname,'root','root','0641')
        ret = target.create_fifo(self.fname,'root','root','0641')
        self.assertFalse(ret)
        self.unlink(self.fname)

    def test_write_pidfile_0(self):
        self.unlink(self.pname)
        ret = target.write_pidfile(self.pname, 12345)
        self.assertTrue(ret)
        self.unlink(self.pname)

    def test_write_pidfile_1(self):
        self.unlink(self.pname)
        ret = target.write_pidfile(self.pname, 10)
        ret = target.write_pidfile(self.pname, 20)
        fp = open(self.pname, 'r')
        ret = fp.read()
        self.assertEquals('20', ret)
        self.unlink(self.pname)

    def test_read_pidfile_0(self):
        self.unlink(self.pname)
        target.write_pidfile(self.pname, 30)

        ret = target.read_pidfile(self.pname)
        self.assertEquals('30', ret)
        self.unlink(self.pname)

class SuiteIsSplitShellCommand(unittest.TestSuite):
    def __init__(self):
        tests = ['test_split_shell_command_0',
                 'test_split_shell_command_1',
                 ]
        unittest.TestSuite.__init__(self,map(TestUtil, tests))

class SuiteIsEmpty(unittest.TestSuite):
    def __init__(self):
        tests = ['test_is_empty_0',
                 ]
        unittest.TestSuite.__init__(self,map(TestUtil, tests))

class SuiteCreateFifo(unittest.TestSuite):
    def __init__(self):
        tests = ['test_create_fifo_0',
                 'test_create_fifo_1',
                 ]
        unittest.TestSuite.__init__(self,map(TestUtil, tests))

class SuitePopen(unittest.TestSuite):
    def __init__(self):
        tests = ['test_popen_0',
                 'test_popen_1',
                 ]
        unittest.TestSuite.__init__(self,map(TestUtil, tests))

class SuiteWritePidfile(unittest.TestSuite):
    def __init__(self):
        tests = ['test_write_pidfile_0',
                 'test_write_pidfile_1',
                 ]
        unittest.TestSuite.__init__(self,map(TestUtil, tests))

class SuiteReadPidfile(unittest.TestSuite):
    def __init__(self):
        tests = ['test_read_pidfile_0',
                 'test_read_pidfile_1',
                 ]
        unittest.TestSuite.__init__(self,map(TestUtil, tests))

def all_suite_util():
    return unittest.TestSuite([SuiteIsSplitShellCommand(),
                               SuitePopen(),
                               SuiteIsEmpty(),
                               SuiteCreateFifo(),
                               SuiteWritePidfile(),
                               SuiteReadPidfile(),
                               ])

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(all_suite_util())
