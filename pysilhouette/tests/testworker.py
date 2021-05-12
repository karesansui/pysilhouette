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
import logging

import sqlalchemy.orm

from pysilhouette.prep import readconf 
from pysilhouette.db import Database
from pysilhouette.db.model import RES_PENDING, RES_RUNNING,RES_NORMAL_END, \
    RES_ABNORMAL_TERMINATION, RES_ROLLBACK,RES_ROLLBACK_ABEND, \
    RES_ROLLBACK_SUCCESSFUL_COMPLETION, reload_mappers
from pysilhouette.worker import Worker
from pysilhouette.db.access import *

class TestWorker(unittest.TestCase):
    """
    """
    _db = None

    def setUp(self):
        # O/R mapping
        self._db = Database(cf['database.url'], encoding="utf-8", convert_unicode=True, echo=True)
        reload_mappers(self._db.get_metadata())

        # database init
        self._db.get_metadata().drop_all()
        self._db.get_metadata().create_all() # create table
        pass

    def tearDown(self):
        sqlalchemy.orm.clear_mappers()
        pass

    def set_job(self, session, jg_name, uniqkey, 
                job=(True, True, True), rollback=None, mail=None):
        jg1 = JobGroup(jg_name.decode('utf-8'), uniqkey)

        if job[0] is True:
            j1 = Job('file create','0','/bin/touch /tmp/test_case1.txt')
        else:
            j1 = Job('file create','0','/bin/touch_dummy /tmp/test_case1.txt')

        if job[1] is True:
            j2 = Job('file copy', '1', '/bin/cp /tmp/test_case1.txt /tmp/test_case1_rename.txt')
        else:
            j2 = Job('file copy', '1', '/bin/cp_dummy /tmp/test_case1.txt /tmp/test_case1_rename.txt')

        if job[2] is True:
            j3 = Job('file delete','2','/bin/rm /tmp/test_case1.txt')
        else:
            j3 = Job('file delete','2','/bin/rm_dummy /tmp/test_case1.txt')

        jg1.jobs.append(j1)
        jg1.jobs.append(j2)
        jg1.jobs.append(j3)

        if rollback is True:
            j1.rollback_command = '/bin/echo JOB1 rollback'
            j2.rollback_command = '/bin/echo JOB2 rollback'
            j3.rollback_command = '/bin/echo JOB3 rollback'
        elif rollback is False:
            j1.rollback_command = '/bin/echo_dummy JOB1 rollback'
            j2.rollback_command = '/bin/echo_dummy JOB2 rollback'
            j3.rollback_command = '/bin/echo_dummy JOB3 rollback'
        elif rollback is None:
            pass

        if mail is True:
            jg1.finish_command = ok_f_cmd % (jg1.name, jg1.name)
        elif mail is False:
            jg1.finish_command = ng_f_cmd % (jg1.name, jg1.name)
        elif mail is None:
            pass

        session.add_all([jg1])
        session.commit()

    def run_job(self, sess):
        _m_jgs = jobgroup_findbystatus(sess)
        for _m_jg in _m_jgs:
            _w = Worker(self._db, _m_jg.id)
            _w.process()
            worker_debug(self._db, _m_jg.id)
        sess.close()
        
    def check_job(self, sess, jg=RES_NORMAL_END, 
                  job=(RES_NORMAL_END, RES_NORMAL_END, RES_NORMAL_END)):
        sess = self._db.get_session()
        _m_jg1 = jobgroup_findbyid(sess, 1)
        self.assertEqual(int(_m_jg1.status), int(jg))

        _m_jobs = job_findbyjobgroup_id(sess, 1, False)
        self.assertEqual(int(_m_jobs[0].status), int(job[0]))
        self.assertEqual(int(_m_jobs[1].status), int(job[1]))
        self.assertEqual(int(_m_jobs[2].status), int(job[2]))

        sess.close()
        

    def test_case1(self):
        """Test Case 1
          - Job Group : Normal end
          - Job : All Normal end
          - Rollback: Normal end
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 1', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, True), rollback=True, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_NORMAL_END, 
              job=(RES_NORMAL_END, RES_NORMAL_END, RES_NORMAL_END))


    def test_case2(self):
        """Test Case 2
          - Job Group : Normal end
          - Job : All Normal end
          - Rollback: Abnormal termination
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 2', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, True), rollback=False, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_NORMAL_END, 
              job=(RES_NORMAL_END, RES_NORMAL_END, RES_NORMAL_END))

        sess.close()


    def test_case3(self):
        """Test Case 3
          - Job Group : Normal end
          - Job : All Normal end
          - Rollback: None
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 3', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, True), rollback=None, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_NORMAL_END, 
              job=(RES_NORMAL_END, RES_NORMAL_END, RES_NORMAL_END))

        sess.close()

    def test_case4(self):
        """Test Case 4
          - Job Group : Normal end
          - Job : All Normal end
          - Rollback: Normal end
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 4', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, True), rollback=None, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_NORMAL_END, 
              job=(RES_NORMAL_END, RES_NORMAL_END, RES_NORMAL_END))

        sess.close()


    def test_case5(self):
        """Test Case 5
          - Job Group : Normal end
          - Job : All Normal end
          - Rollback: None
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 5', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, True), rollback=None, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_NORMAL_END, 
              job=(RES_NORMAL_END, RES_NORMAL_END, RES_NORMAL_END))

        sess.close()

    def test_case6(self):
        """Test Case 6
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 6', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=True, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION,
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION, 
                            RES_PENDING,
                            RES_PENDING))
        sess.close()

    def test_case7(self):
        """Test Case 7
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 7', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=False, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION,
                       job=(RES_ROLLBACK_ABEND, RES_PENDING, RES_PENDING))

        sess.close()


    def test_case8(self):
        """Test Case 8
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: None
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 8', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=None, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
              job=(RES_ABNORMAL_TERMINATION, RES_PENDING, RES_PENDING))

        sess.close()

    def test_case9(self):
        """Test Case 9
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 9', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=True, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_PENDING,
                            RES_PENDING))

        sess.close()

    def test_case10(self):
        """Test Case 10
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 10', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=False, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_ABEND, RES_PENDING, RES_PENDING))

        sess.close()


    def test_case11(self):
        """Test Case 11
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback : None
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 11', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=None, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ABNORMAL_TERMINATION, RES_PENDING, RES_PENDING))

        sess.close()


    def test_case12(self):
        """Test Case 12
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 12', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=True, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_PENDING,
                            RES_PENDING))

        sess.close()

    def test_case13(self):
        """Test Case 13
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 13', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=False, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_ABEND, RES_PENDING, RES_PENDING))

        sess.close()

    def test_case14(self):
        """Test Case 14
          - Job Group : Abnormal termination
          - Job : First Job Abnormal termination
          - Rollback: None
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 14', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(False, True, True), rollback=None, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ABNORMAL_TERMINATION, RES_PENDING, RES_PENDING))

        sess.close()

    def test_case15(self):
        """Test Case 15
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 15', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=True, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION,
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION, 
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION, 
                            RES_PENDING))
        sess.close()

    def test_case16(self):
        """Test Case 16
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 16', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=False, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION,
                       job=(RES_ROLLBACK_ABEND, RES_ROLLBACK_ABEND, RES_PENDING))

        sess.close()


    def test_case17(self):
        """Test Case 17
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: None
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 17', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=None, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
              job=(RES_NORMAL_END, RES_ABNORMAL_TERMINATION, RES_PENDING))

        sess.close()

    def test_case18(self):
        """Test Case 9
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 18', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=True, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_PENDING))

        sess.close()

    def test_case19(self):
        """Test Case 19
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 19', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=False, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_ABEND, RES_ROLLBACK_ABEND, RES_PENDING))

        sess.close()


    def test_case20(self):
        """Test Case 11
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback : None
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 20', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=None, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_NORMAL_END,
                            RES_ABNORMAL_TERMINATION,
                            RES_PENDING))

        sess.close()


    def test_case21(self):
        """Test Case 21
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 21', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=True, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_PENDING))

        sess.close()

    def test_case22(self):
        """Test Case 22
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case ス22', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=False, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_ABEND, RES_ROLLBACK_ABEND, RES_PENDING))

        sess.close()

    def test_case23(self):
        """Test Case 23
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: None
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'テストケース23', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, False, True), rollback=None, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_NORMAL_END, 
                            RES_ABNORMAL_TERMINATION,
                            RES_PENDING))

        sess.close()

    def test_case24(self):
        """Test Case 24
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 24', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=True, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION,
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION, 
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION, 
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION))
        sess.close()

    def test_case25(self):
        """Test Case 25
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 25', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=False, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION,
                       job=(RES_ROLLBACK_ABEND, 
                            RES_ROLLBACK_ABEND,
                            RES_ROLLBACK_ABEND))

        sess.close()


    def test_case26(self):
        """Test Case 26
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback: None
          - Send Mail : Normal end
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 26', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=None, mail=True)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
              job=(RES_NORMAL_END, RES_NORMAL_END, RES_ABNORMAL_TERMINATION))

        sess.close()

    def test_case27(self):
        """Test Case 27
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 27', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=True, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION))

        sess.close()

    def test_case28(self):
        """Test Case 28
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 28', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=False, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_ABEND, RES_ROLLBACK_ABEND, RES_ROLLBACK_ABEND))

        sess.close()


    def test_case29(self):
        """Test Case 29
          - Job Group : Abnormal termination
          - Job : Second Job Abnormal termination
          - Rollback : None
          - Send Mail : Abnormal termination
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 29', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=None, mail=False)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_NORMAL_END,
                            RES_NORMAL_END,
                            RES_ABNORMAL_TERMINATION))

        sess.close()


    def test_case30(self):
        """Test Case 30
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: Normal end
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 30', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=True, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION,
                            RES_ROLLBACK_SUCCESSFUL_COMPLETION))

        sess.close()

    def test_case31(self):
        """Test Case 31
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: Abnormal termination
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 31', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=False, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_ROLLBACK_ABEND, 
                            RES_ROLLBACK_ABEND, 
                            RES_ROLLBACK_ABEND))

        sess.close()

    def test_case32(self):
        """Test Case 32
          - Job Group : Abnormal termination
          - Job : Third Job Abnormal termination
          - Rollback: None
          - Send Mail : None
        """
        sess = self._db.get_session()
        self.set_job(sess, 'Test Case 32', 'b942f21c-4039-e6e9-09dc-9685985a1b84',
                     job=(True, True, False), rollback=None, mail=None)

        self.run_job(sess)

        self.check_job(sess, jg=RES_ABNORMAL_TERMINATION, 
                       job=(RES_NORMAL_END, 
                            RES_NORMAL_END,
                            RES_ABNORMAL_TERMINATION))

        sess.close()

def worker_debug(db, jobgroup_id):
    logger = logging.getLogger('pysilhouette.performer.worker')
    session = db.get_session()
    jg = jobgroup_findbyid(session, jobgroup_id)
    
    def po(msg):
        logger.debug(str(msg))

    def poc(msg, code):
        import pysilhouette.db.model
        if pysilhouette.db.model.RES_PENDING == str(code):
            po(msg+' : Pending')
        if pysilhouette.db.model.RES_RUNNING == str(code):
            po(msg+' : Running')
        if pysilhouette.db.model.RES_NORMAL_END == str(code):
            po(msg+' : Normal end')
        if pysilhouette.db.model.RES_ABNORMAL_TERMINATION == str(code):
            po(msg+' : Abnormal termination')
        if pysilhouette.db.model.RES_ROLLBACK == str(code):
            po(msg+' : Rollback running')
        if pysilhouette.db.model.RES_ROLLBACK_ABEND == str(code):
            po(msg+' : Rollback abend')
        if pysilhouette.db.model.RES_ROLLBACK_SUCCESSFUL_COMPLETION == str(code):
            po(msg+' : Rollback successful completion')
    def pc(uni):
        if not uni:
            return str(uni)
        else:
            return str(uni.encode('utf-8'))

    # debug print
    po('------------------------------')
    po("Job Group ID=%s" % jg.id)
    po("Target host ip address=%s" % str(jg.uniq_key))
    po("Job Group name=%s" % pc(jg.name))
    poc("Job Group status now=%s" % str(jg.status), jg.status)
    po("Finish Command='%s'" % pc(jg.finish_command))
    po('------------------------------')

    jobs = job_findbyjobgroup_id(session, jg.id, False)
    for j in jobs:
        po("Job ID=%s" % str(j.id))
        po("Job Name=%s" % pc(j.name))
        po("Job Order=%s" % str(j.order))
        po("Job Progress=%s" % str(j.progress))
        po("Job Action Command='%s'" % pc(j.action_command))
        po("Job Rollback Command='%s'"% pc(j.rollback_command))
        poc("Job Status=%s" % str(j.status), str(j.status))
        po("Job Action Exit Code='%s'" % str(j.action_exit_code))
        po("Job Action Stdout='%s'" % pc(j.action_stdout))
        po("Job Action Stderr='%s'" % pc(j.action_stderr))
        po("Job Rollback Exit Code='%s'" % str(j.rollback_exit_code))
        po("Job Rollback Stdout='%s'" % pc(j.rollback_stdout))
        po("Job Rollback Stderr='%s'" % pc(j.rollback_stderr))
        po('------------------------------')
        
    session.close()

def test_setup(cf):
    # --
    db = Database(cf['database.url'], encoding='utf-8', convert_unicode=True)
    reload_mappers(db.get_metadata())

    db.get_metadata().drop_all()
    db.get_metadata().create_all()

    f_cmd = ('python /root/repository/pysilhouette_svn/pysilhouette/job/sendmail.py'
             ' --from="root@localhost"'
             ' --to="root@localhost"'
             ' --subject="test"'
             ' --hostname="localhost"'
             ' --port="25"'
             ' --msg="%s"'
             ' --charset="utf-8"')

    session = db.get_session()
    jg1 = JobGroup('get date', '172.16.0.123')
    jg1.finish_command = f_cmd % jg1.name
    jb1 = Job('get date','0','/bin/date error')
    jb1.rollback_command = '/bin/date'
    jg1.jobs.append(jb1)
    jg2 = JobGroup('get route', '172.16.0.123')
    jg2.finish_command = f_cmd % jg2.name
    jg2.jobs.append(Job('get route','1', '/sbin/route'))
    jg3 = JobGroup('print string', '172.16.0.123')
    jg3.finish_command = f_cmd % jg3.name
    jg3.jobs.append(Job('print string','2', '/bin/echo test'))
    session.add_all([jg1,jg2,jg3])
    #session.add(jg1)
    session.commit()

    from pysilhouette.db.access import jobgroup_findbystatus
    _m_jgs = jobgroup_findbystatus(session)
    return db, session, _m_jgs


class SuiteWorker(unittest.TestSuite):
    def __init__(self):
        #tests = ['test_case1']
        tests = ['test_case1', 'test_case2', 'test_case3', 
                 'test_case4', 'test_case5', 'test_case6',
                 'test_case7', 'test_case8', 'test_case9',
                 'test_case10', 'test_case11', 'test_case12',
                 'test_case13', 'test_case14', 'test_case15',
                 'test_case16', 'test_case17', 'test_case18',
                 'test_case19', 'test_case20', 'test_case21',
                 'test_case22', 'test_case23', 'test_case24', 
                 'test_case25', 'test_case26', 'test_case27', 
                 'test_case28', 'test_case29', 'test_case30', 
                 'test_case31', 'test_case32']

        unittest.TestSuite.__init__(self,list(map(TestWorker, tests)))

def all_suite_worker():
    return unittest.TestSuite([SuiteWorker()])

if __name__ == '__main__':
    job_path = '/root/repository/pysilhouette_svn/job/'

    os.environ['PYSILHOUETTE_CONF'] = '/etc/pysilhouette/silhouette.conf'
    cf = readconf(os.environ['PYSILHOUETTE_CONF'])
    pysilhouette.log.reload_conf(cf["env.sys.log.conf.path"])

    ok_f_cmd = ('python /root/pysilhouette/pysilhouette/job/sendmail.py' 
                ' --from="root@localhost"' 
                ' --to="root@localhost"'
                ' --subject="Results of Worker(%s)"' 
                ' --hostname="localhost"' 
                ' --port="25"'
                ' --msg="%s"' 
                ' --charset="utf-8"') 

    ng_f_cmd = ('python /root/pysilhouette/pysilhouette/job/sendmail_dummy.py' 
                ' --from="root@localhost"' 
                ' --to="root@localhost"' 
                ' --subject="Results of Worker(%s)"' 
                ' --hostname="localhost"' 
                ' --port="25"'
                ' --msg="%s"' 
                ' --charset="utf-8"') 

    unittest.TextTestRunner(verbosity=2).run(all_suite_worker())
