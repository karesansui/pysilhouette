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

import subprocess
import os
import sys
import traceback
import logging

import pysilhouette
from pysilhouette.db import *
from pysilhouette.db.model import *
from pysilhouette.db.access import jobgroup_findbyid, \
     job_findbyjobgroup_id, jobgroup_update, job_update, \
     job_result_action, job_result_rollback

from pysilhouette.util import popen, kill_proc, is_empty, split_shell_command

class SilhouetteWorkerException(pysilhouette.SilhouetteException):
    """Worker execution error.
    """
    pass

class Worker:
    """Worker Base class
    """
    def process(self):
        try:
            session = self._db.get_session()
            self.logger.debug('Session was obtained from the database. - session=%s' % session)
            self._m_jg = jobgroup_findbyid(session,
                                               self._jobgroup_id,
                                               self._cf['env.uniqkey'])
            
            if self._m_jg is None: return False
            jobgroup_update(session, self._m_jg, JOBGROUP_STATUS['RUN']) # JobGroup UPDATE
            _m_jobs = job_findbyjobgroup_id(session, self._jobgroup_id, False) # order asc

            # action
            ret = False
            err = False
            try:
                ret = self._action(session, _m_jobs)
            except Exception as e:
                t_logger = logging.getLogger('pysilhouette_traceback')
                t_logger.info(traceback.format_exc())
                self.logger.info('%s, Failed to perform the job action. Exceptions are not expected. - jobgroup_id=%d : %s, JobGroup status=%s'
                             % (self.getName(), self._jobgroup_id, str(e.args), JOBGROUP_STATUS['APPERR']))

                jobgroup_update(session, self._m_jg, JOBGROUP_STATUS['APPERR'])
                err = True

            try:
                if err is False:
                    if ret is True:
                        # normal
                        jobgroup_update(session, self._m_jg, JOBGROUP_STATUS['OK'])
                    else:
                        # rollback
                        jobgroup_update(session, self._m_jg, JOBGROUP_STATUS['NG']) # JobGroup UPDATE
                        try:
                            self._rollback(session, _m_jobs)
                        except Exception as e:
                            self.logger.info('Failed to perform a rollback. Exceptions are not expected. - jobgroup_id=%d : %s'
                                         % (self._jobgroup_id, str(e.args)))
                            t_logger = logging.getLogger('pysilhouette_traceback')
                            t_logger.info(traceback.format_exc())
                        
            finally:
                # finish
                try:
                    self._finish()
                except Exception as e:
                    self.logger.info('Failed to perform the finish action. Exceptions are not expected. - jobgroup_id=%d : %s'
                                 % (self._jobgroup_id, str(e.args)))
                    t_logger = logging.getLogger('pysilhouette_traceback')
                    t_logger.info(traceback.format_exc())
        finally:
            self.logger.debug('close database session, session=%s' % session)
            session.close()

    def _action(self, session, m_jobs):
        raise SilhouetteWorkerException('Please override this method.')
    
    def _rollback(self, session, m_jobs):
        raise SilhouetteWorkerException('Please override this method.')

    def _finish(self):
        proc = None
        proc_info = []
        cmd = self._m_jg.finish_command

        if is_empty(cmd):
            self.logger.debug('finish command not running!!- jobgroup_id=%d' % (self._m_jg.id))
            return False # No finish Command
        else:
            try:
                self.logger.info('finish command running!! - jobgroup_id=%d : cmd=%s'
                                  % (self._m_jg.id, cmd))

                lcmd = split_shell_command(cmd)

                if self.chk_whitelist(lcmd[0]):
                    try:
                        (proc, proc_info) = popen(lcmd,
                                                  self._cf['job.popen.timeout'],
                                                  self._cf['job.popen.waittime'],
                                                  self._cf['job.popen.env.lang'],
                                                  )
                        self.logger.debug('Of commands executed stdout=%s' % proc_info['stdout'])
                        self.logger.debug('Of commands executed stderr=%s' % proc_info['stderr'])
                        
                    except OSError as oe:
                        self.logger.info('finish command system failed!! jobgroup_id=%d : cmd=%s'
                                          % (self._m_jg.id, cmd))
                        raise oe

                    if proc_info['r_code'] == 0:
                        self.logger.info('finish command successful!! - jobgroup_id=%d : cmd=%s'
                                          % (self._m_jg.id, cmd))
                    else:
                        self.logger.info('finish command failed!! - jobgroup_id=%d : cmd=%s'
                                      % (self._m_jg.id, cmd))
                    return True

                else:
                    # whitelist
                    self.logger.info('Tried to run the rollback command that is not registered in the whitelist. - jobgroup_id=%d : cmd=%s'
                                      % (self._m_jg.id, cmd))
                    
            finally:
                kill_proc(proc)



    def chk_whitelist(self, cmd):
        flag = self._cf['job.whitelist.flag'].strip()
        
        if is_empty(flag) is True:
            self.logger.debug("Whitelist feature [OFF] - empty")
            return True # Unconditional
        
        if flag != "1":
            self.logger.debug("Whitelist feature [OFF]")
            return True # Unconditional

        self.logger.debug("Whitelist feature [ON]")
        fp = open(self._cf['job.whitelist.path'], 'r')
        try:
            for line in fp.readlines():
                if cmd.strip() == line.strip():
                    return True
        finally:
            fp.close()
            
        return False

class SimpleWorker(Worker):
    """Sequential Worker Class
    """
    def __init__(self, cf, db, jobgroup_id):
        self._cf = cf
        self._db = db
        self._jobgroup_id = jobgroup_id
        self.logger = logging.getLogger('pysilhouette.worker.simpleworker')

    def _action(self, session, m_jobs):
        ret = True
        for m_job in m_jobs: # job(N) execute
            job_update(session, m_job, ACTION_STATUS['RUN']) # Job UPDATE
            proc = None
            proc_info = []
            try:
                cmd = m_job.action_command
                self.logger.info('action command running!!- jobgroup_id=%d : cmd=%s'
                                  % (m_job.id, cmd))

                lcmd = split_shell_command(cmd)
                if self.chk_whitelist(lcmd[0]):
                    try:
                        (proc, proc_info) = popen(cmd=lcmd,
                                                  timeout=self._cf['job.popen.timeout'],
                                                  waittime=self._cf['job.popen.waittime'],
                                                  lang=self._cf['job.popen.env.lang'],
                                                  limit=self._cf['job.popen.output.limit'],
                                                  job_id=m_job.id,
                                                  )

                        self.logger.debug('Of commands executed stdout=%s' % proc_info['stdout'])
                        self.logger.debug('Of commands executed stderr=%s' % proc_info['stderr'])

                        if self._cf['job.popen.output.limit'] < len(proc_info['stdout']):
                            self.logger.info("There was a limit beyond stdout output. Information-processing is truncated beyond the limit. - limit=%d, stdout=%d" \
                                             % (self._cf['job.popen.output.limit'], len(proc_info['stdout'])))

                        if self._cf['job.popen.output.limit'] < len(proc_info['stderr']):
                            self.logger.info("There was a limit beyond stderr output. Information-processing is truncated beyond the limit. - limit=%d, stderr=%d" \
                                             % (self._cf['job.popen.output.limit'], len(proc_info['stderr'])))
                            

                    except OSError as oe:
                        self.logger.info('action command system failed!! job_id=%d : cmd=%s'
                                          % (m_job.id, cmd))
                        raise oe

                    job_result_action(session, m_job, proc_info) # Job result UPDATE

                    if proc_info['r_code'] == 0: # Normal end
                        self.logger.info('action command was successful!! job_id=%d : cmd=%s'
                                          % (m_job.id, cmd))
                        job_update(session, m_job, ACTION_STATUS['OK']) # Job UPDATE
                    else: # Abnormal termination
                        self.logger.info('action command failed!! job_id=%d : cmd=%s'
                                          % (m_job.id, cmd))
                        job_update(session, m_job, ACTION_STATUS['NG']) # Job UPDATE
                        ret = False
                        break
                else:
                    # whitelist error
                    self.logger.info('Tried to run the action command that is not registered in the whitelist. job_id=%d : cmd=%s'
                                      % (m_job.id, cmd))
                    m_job.action_stderr = "Command is not registered to run the whitelist."
                    job_update(session, m_job, ACTION_STATUS['WHITELIST']) # Job UPDATE
                    ret = False
                    break
                    
            finally:
                kill_proc(proc)
                
        return ret
    
    def _rollback(self, session, m_jobs):
        for m_job in m_jobs:

            if m_job.is_rollback() and m_job.status in (ACTION_STATUS['RUN'],
                                                        ACTION_STATUS['OK'],
                                                        ACTION_STATUS['NG']):
                # rollback exec
                proc = None
                proc_info = []
                try:
                    cmd = m_job.rollback_command
                    self.logger.info('rollback command running!!- jobgroup_id=%d : cmd=%s'
                                      % (m_job.id, cmd))

                    lcmd = split_shell_command(cmd)
                    
                    if self.chk_whitelist(lcmd[0]):
                        try:
                            (proc, proc_info) = popen(cmd=lcmd,
                                                      timeout=self._cf['job.popen.timeout'],
                                                      waittime=self._cf['job.popen.waittime'],
                                                      lang=self._cf['job.popen.env.lang'],
                                                      limit=self._cf['job.popen.output.limit'],
                                                      )

                            self.logger.debug('Of commands executed stdout=%s' % proc_info['stdout'])
                            self.logger.debug('Of commands executed stderr=%s' % proc_info['stderr'])

                        except OSError as oe:
                            self.logger.info('rollback command system failed!! job_id=%d : cmd=%s'
                                          % (m_job.id, cmd))
                            raise oe
                    
                        job_result_rollback(session, m_job, proc_info) # Job result UPDATE
                        if proc_info['r_code'] == 0: # Normal end
                            self.logger.info('rollback command was successful!! job_id=%d : cmd=%s'
                                              % (m_job.id, cmd))
                            job_update(session, m_job, ROLLBACK_STATUS['OK']) # Job UPDATE
                        else: # Abnormal termination
                            self.logger.info('rollback command failed!! job_id=%d : cmd=%s'
                                              % (m_job.id, cmd))
                            job_update(session, m_job, ROLLBACK_STATUS['NG']) # Job UPDATE

                    else:
                        # whitelist error
                        self.logger.info('Tried to run the rollback command that is not registered in the whitelist. job_id=%d : cmd=%s'
                                          % (m_job.id, cmd))
                        m_job.rollback_stderr = "Command is not registered to run the whitelist."
                        job_update(session, m_job, ROLLBACK_STATUS['WHITELIST']) # Job UPDATE

                finally:
                    kill_proc(proc)
            else:
                self.logger.debug('Does not rollback the process. - job_id=%d : status=%s'
                                  % (m_job.id, m_job.status))

# --
import threading

class ThreadQueue(threading.Thread):
    def __init__(self, request_queue, response_list, *args, **kwargs):
        threading.Thread.__init__(self, *args, **kwargs)
        self.setDaemon(1)
        self.request_queue = request_queue
        self.response_list = response_list
        self.start()
        self.logger = logging.getLogger('pysilhouette.worker.threadqueue')

    def now_alive(self):
        ret = 0
        for th in self.response_list:
            if th[0].isAlive() is True:
                ret =+ 1
        return ret

    def response_clean(self):
        _size = 0
        _len = len(self.response_list)
        while _size < _len:
            if self.response_list[_size][0].isAlive() is False:
                self.response_list.pop(_size) # remove
                _len =- 1
            else:
                _size =+ 1
        return len(self.response_list)

    def put(self, callable, *args, **kwargs):
        self.logger.debug('callable=%s' % str(callable))
        self.request_queue.put((callable, args, kwargs))

    def run(self):
        while True:
            callable, args, kwargs = self.request_queue.get()
            self.logger.debug('callable=%s, args=%s, kwargs=%s' \
                               % (str(callable), str(args), str(kwargs)))
            callable.start()
            self.response_list.append((callable, args, kwargs))

class ThreadWorker(threading.Thread, SimpleWorker):
    def __init__(self, cf, db, jobgroup_id):
        threading.Thread.__init__(self)
        self._cf = cf
        self._jobgroup_id = jobgroup_id
        self._db = db

    def run(self):
        self.logger = logging.getLogger('pysilhouette.worker.threadworker')
        try:
            self.process()
        except Exception as e:
            self.logger.error('%s - JobGroup execute failed. - jobgroup_id=%d : %s, JobGroup status=%s' \
                              % (self.getName(), self._jobgroup_id, str(e.args), JOBGROUP_STATUS['APPERR']))
            t_logger = logging.getLogger('pysilhouette_traceback')
            t_logger.error(traceback.format_exc())
            try:
                session = self._db.get_session()
                jobgroup_update(session,
                                jobgroup_findbyid(session, self._jobgroup_id, self._cf['env.uniqkey']),
                                JOBGROUP_STATUS['APPERR'])
                session.close()
            except:
                self.logger.error('JobGroup failed to update. - jobgroup_id=%d : %s, update status=%s' \
                              % (self._jobgroup_id, str(e.args), JOBGROUP_STATUS['APPERR']))
                t_logger.error(traceback.format_exc())

def dummy_set_job(cf, number, action, rollback, finish, type, db=None):
    try:
        if db is None:
            db = Database(cf['database.url'],encoding="utf-8",convert_unicode=True,echo=True,echo_pool=True)
            reload_mappers(db.get_metadata())

        session = db.get_session()
    except Exception as e:
        print('Initializing a database error', file=sys.stderr)
        raise

    try:
        jgs = []
        for i in range(number):
            jg_name = '%s-%d' % ('worker#dummy_set_job#jobgroup', i)
            jg_ukey = str(cf['env.uniqkey'], "utf-8")
            jg = JobGroup(jg_name, jg_ukey)
            if not finish is None:
                jg.finish_command = str(finish, "utf-8")
            if type == 'serial':
                jg.type = JOBGROUP_TYPE['SERIAL']
            elif type == 'parallel':
                jg.type = JOBGROUP_TYPE['PARALLEL']
            else:
                jg.type = JOBGROUP_TYPE['SERIAL']

            j_name = '%s-%d' % ('worker#dummy_set_job#job', i)
            j_order = i
            j = Job(j_name, j_order, str(action, "utf-8"))
            if not rollback is None:
                j.rollback_command = str(rollback, "utf-8")

            jg.jobs.append(j)
            jgs.append(jg)
            
        session.add_all(jgs)
        session.commit()
        session.close()
        print('Insert JobGroup and Job. num=%d [OK]' % number, file=sys.stdout)
    except Exception as e:
        print('Failed to add JobGroup and Job.', file=sys.stderr)
        raise
            


if __name__ == '__main__':
    import queue
    request_queue = queue.Queue()
    #response_queue = Queue.Queue()
    response_list = []
    tq = ThreadQueue(request_queue, response_list)
    _env = os.environ
    _env['PYSILHOUETTE_CONF'] = '/etc/pysilhouette/silhouette.conf'
    from pysilhouette.prep import readconf 
    #cf = readconf(os.environ['PYSILHOUETTE_CONF'])
    pysilhouette.cf = pysilhouette.prep.readconf(os.environ['PYSILHOUETTE_CONF'])
    import pysilhouette
    import pysilhouette.log
    import sys
    pysilhouette.log.reload_conf(pysilhouette.cf["env.sys.log.conf.path"])
    number = 50
    dummy_set_job(pysilhouette.cf,number,'echo "aaaaaa"','echo "bbbbb"','echo "cccc"','parallel')
    try:
        db = Database(pysilhouette.cf['database.url'],encoding="utf-8",convert_unicode=True,echo=True,echo_pool=True)
        reload_mappers(db.get_metadata())
        session = db.get_session()
    except Exception as e:
        print('Initializing a database error', file=sys.stderr)
        raise

    from pysilhouette.db.access import jobgroup_findbytype_status
    m_jgs = jobgroup_findbytype_status(session, JOBGROUP_TYPE['PARALLEL'])
    for m_jg in m_jgs:
        try:
            tq.put(ThreadWorker(pysilhouette.cf, db, m_jg.id))
        except Exception as e:
            import traceback
            print(traceback.format_exc())

    import time
    time.sleep(2)

    while True:
        size = tq.response_clean()
        print('ret=' + str(size))
        if size <= 0:
            break
        time.sleep(2)

    print('end (request_queue size=%d, response_list=%s)' % (tq.request_queue.qsize(), tq.response_list))
