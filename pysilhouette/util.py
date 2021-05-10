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
import pwd
import grp
import subprocess
import time
import logging

def is_empty(s):
    """is empty
    @param s: string
    @type s: str
    """
    if s and 0 < len(s.strip()):
        return False
    else:
        return True

def astrftime(tm):
    return time.strftime("%m/%d/%Y %H:%M:%S", time.localtime(tm))
    
def split_shell_command(cmd):
    ret = []
    if is_empty(cmd) is False:
        try:
            import shlex
            vs = shlex.split(cmd.encode('utf8'))
        except:
            vs = cmd.split(' ')
        for v in vs:
            v = v.strip()
            if is_empty(v): continue
            ret.append(v)
    return ret

def write_pidfile(fname, pid):
    fp = open(fname, 'w')
    try:
        fp.write('%d' % pid)
        return True
    finally:
        fp.close()

def read_pidfile(fname):
    fp = open(fname, 'r')
    try:
        return fp.read()
    finally:
        fp.close()
        

def create_fifo(fname, user, group, perm):
    """create fifo file.
    @param fname: file name
    @type fname: str
    @param: user: username
    @type: user: str
    @param: group: groupname
    @type: group: str
    @param: perm: Permission - example) '0666'
    @type: perm: str(4)
    """
    perm8 = int(perm, 8)
    os.mkfifo(fname, perm8)
    os.chown(fname, pwd.getpwnam(user)[2], grp.getgrnam(group)[2])
    os.chmod(fname, perm8)

def kill_proc(proc):
    if proc and hasattr(os, 'kill'):
        import signal
        try:
            os.kill(proc.pid, signal.SIGTERM)
            return True
        except:
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except:
                return False        

def popen(cmd, timeout, waittime, lang, limit=1048576, job_id=None):
    """<comment-ja>
    @param limit: 1048576(1MByte)
    @type limit: int
    """

    proc_info = {}

    timeout = int(timeout)
    waittime = int(waittime)
    env = os.environ.copy()
    env['LANG'] = lang
    if not (job_id is None):
        env['JOB_ID'] = str(job_id)

    proc = subprocess.Popen(cmd,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            #env=os.environ,
                            env=env,
                            shell=False,
                            )

    # parent process wait.
    start_time = time.time()
    while True:
        r = proc.poll()
        if r is None:
            interval = int(time.time() - start_time)
            if 0 < timeout and timeout < interval:
                try:
                    kill_proc(proc)
                finally:
                    break
            time.sleep(waittime)
        else:
            break

    stdout = stderr = ''
    for x in proc.stdout:
        stdout += str(x)
    for x in proc.stderr:
        stderr += str(x)

    if stdout and limit < len(stdout):
        proc_info['stdout'] = stdout[:limit]
    else:
        proc_info['stdout'] = stdout
    if stderr and limit < len(stderr):
        proc_info['stderr'] = stderr[:limit]
    else:
        proc_info['stderr'] = stderr

    proc_info['pid'] = proc.pid
    proc_info['r_code'] = r

    return proc, proc_info

def debug_popen(proc, proc_info):
    logger = logging.getLogger('pysilhouette.popen')

    #logger.debug("Command : %s" % cmd)
    logger.debug("Sub process id. id=%s" % proc.pid)
    logger.debug("stdout : %s" % proc_info['stdout'])
    logger.debug("stderr : %s" % proc_info['stderr'])

    if os.WIFSTOPPED(proc_info['r_code']) is True:
        logger.debug('The process stopped. code=%s' % proc_info['r_code'])
    if os.WIFSIGNALED(proc_info['r_code']) is True:
        logger.debug('The process stopped by the signal. code=%s' % \
                  proc_info['r_code'])
    if os.WIFEXITED(proc_info['r_code']) is True:
        logger.debug('The process stopped by the system call. code=%s' % \
                  proc_info['r_code'])
    logger.debug('Integer parameter passed to system call. parameter=%s' % \
              os.WEXITSTATUS(proc_info['r_code']))
    logger.debug('The process stopped by the signal no. no=%s' % \
              os.WSTOPSIG(proc_info['r_code']))
    logger.debug('The process finished by the signal no. no=%s' % \
              os.WTERMSIG(proc_info['r_code']))

def is_int(val):
    try:
        int(val)
        return True
    except:
        return False

def is_key(cf, key):
    if (key in cf) is True and 0 < len(cf[key]):
        return True
    else:
        return False

def set_cf_int(cf, key):
    cf[key] = int(cf[key])

if __name__ == '__main__':
    #print popen(cmd='efdsfdsafdsafdsafdsafdsa', timeout=3, waittime=1, lang='C')
    print(popen(cmd='date', timeout=3, waittime=1, lang='C'))
