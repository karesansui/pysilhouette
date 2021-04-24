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

import time
import os
import sys
import math
import subprocess
import signal
import logging

import pysilhouette.log
from pysilhouette import PROCERROR
from pysilhouette.util import astrftime
from pysilhouette.util import kill_proc

def observer(opts, cf):    
    """scheduler and performer manage and monitor.
    @param opts: command options
    @type opts: dict(OptionParser)
    @param cf: Configuration info
    @type cf: dict
    @rtype: int
    @return: exit code
    """
    def scheduler():
        cmd = [cf['observer.target.python'], cf['observer.target.scheduler']]
        if cmd_args:
            cmd.extend(cmd_args)
        if opts.daemon is True:
            cmd.extend(['-p', os.path.abspath(os.path.dirname(opts.pidfile)) + '/schedulerd.pid'])

        logger.debug('scheduler:popen - cmd=%s' % cmd)
        return subprocess.Popen(args=cmd,
                                close_fds=True,
                                env=this_env,
                                shell=False)

    def performer():
        cmd = [cf['observer.target.python'], cf['observer.target.performer']]
        if cmd_args:
            cmd.extend(cmd_args)
        if opts.daemon is True:
            cmd.extend(['-p', os.path.abspath(os.path.dirname(opts.pidfile)) + '/performerd.pid'])

        logger.debug('performer:popen - cmd=%s' % cmd)
        return subprocess.Popen(args=cmd,
                                close_fds=True,
                                env=this_env,
                                shell=False)

    def asynscheduler():
        cmd = [cf['observer.target.python'], cf['observer.target.asynscheduler']]
        if cmd_args: 
            cmd.extend(cmd_args)
        if opts.daemon is True:
            cmd.extend(['-p', os.path.abspath(os.path.dirname(opts.pidfile)) + '/asynschedulerd.pid'])
            
        logger.debug('asynscheduler:popen - cmd=%s' % cmd)
        return subprocess.Popen(args=cmd,
                                close_fds=True,
                                env=this_env,
                                shell=False)

    def asynperformer():
        cmd = [cf['observer.target.python'], cf['observer.target.asynperformer']]
        if cmd_args: 
            cmd.extend(cmd_args)
        if opts.daemon is True:
            cmd.extend(['-p', os.path.abspath(os.path.dirname(opts.pidfile)) + '/asynperformerd.pid'])

        logger.debug('asynperformer:popen - cmd=%s' % cmd)
        return subprocess.Popen(args=cmd,
                                close_fds=True,
                                env=this_env,
                                shell=False)

    def status(count, status, default, force=False):
        try:
            if (force is True) or (status != count):
                status = count
                fp = open(cf["observer.status.path"], "w")
                try:
                    logger.debug("%d/%d" % (count, default))
                    fp.write("%d/%d" % (count, default))
                except:
                    fp.close()
            else:
                pass
            
        except IOError as ioe:
            logger.error("Failed to write status. file=%s - %s" \
                        % (cf["observer.status.path"], str(ioe.args)))

    ##
    logger = logging.getLogger('pysilhouette.observer')

    # environment
    this_env = os.environ
    cmd_args = ['-c', opts.config]

    if opts.verbose is True:
        cmd_args.append('-v')
    if opts.daemon is True:
        cmd_args.append('-d')

    spoint = time.time()
    
    default_count = cf['observer.restart.count'] # default
    status_count = default_count # status
    count = default_count # now

    sd = pf = None

    pf = performer() # start!!
    logger.info('performer : [start] - pid=%s, count=%s/%s'
                 % (pf.pid, count, cf['observer.restart.count']))
    sd = scheduler() # start!!
    logger.info('scheduler : [start] - pid=%s, count=%s/%s'
                 % (sd.pid, count, cf['observer.restart.count']))

    asynpf = asynperformer() # start!!
    logger.info('asynperformer : [start] - pid=%s, count=%s/%s'
                 % (pf.pid, count, cf['observer.restart.count']))

    asynsd = asynscheduler() # start!!
    logger.info('asynscheduler : [start] - pid=%s, count=%s/%s'
                 % (sd.pid, count, cf['observer.restart.count']))

    status(count, status_count, default_count, True)

    try:
        while True:
            simple_log = []
            # Performer
            if not pf.poll() is None:
                logger.debug('return code=%d' % pf.returncode)
                logger.info('performer : [stop] - pid=%s, count=%s/%s'
                             % (pf.pid, count, cf['observer.restart.count']))
                pf = performer() # restart
                count -= 1
                logger.info('performer : [start] - pid=%s, count=%s/%s'
                             % (pf.pid, count, cf['observer.restart.count']))
            else:
                simple_log.append('performer (running) - count=%s/%s' % (count, cf['observer.restart.count']))
                logger.debug('performer [running] - pid=%s, count=%s/%s'
                             % (pf.pid, count, cf['observer.restart.count']))

            # Scheduler
            if not sd.poll() is None:
                logger.debug('return code=%d' % sd.returncode)
                logger.info('scheduler : [stop] - pid=%s, count=%s/%s'
                             % (sd.pid, count, cf['observer.restart.count']))
                sd = scheduler() # restart
                count -= 1
                logger.info('scheduler : [start] - pid=%s, count=%s/%s'
                                  % (sd.pid, count, cf['observer.restart.count']))
            else:
                simple_log.append('scheduler (running) - count=%s/%s' % (count, cf['observer.restart.count']))
                logger.debug('scheduler [running] - pid=%s, count=%s/%s'
                             % (sd.pid, count, cf['observer.restart.count']))

            # AsynPerformer
            if not asynpf.poll() is None:
                logger.debug('return code=%d' % asynpf.returncode)
                logger.info('asynperformer : [stop] - pid=%s, count=%s/%s'
                             % (asynpf.pid, count, cf['observer.restart.count']))
                asynpf = asynperformer() # restart
                count -= 1
                logger.info('asynperformer : [start] - pid=%s, count=%s/%s'
                             % (asynpf.pid, count, cf['observer.restart.count']))
            else:
                simple_log.append('asynperformer (running) - count=%s/%s' % (count, cf['observer.restart.count']))
                logger.debug('asynperformer [running] - pid=%s, count=%s/%s'
                             % (asynpf.pid, count, cf['observer.restart.count']))

            # AsynScheduler
            if not asynsd.poll() is None:
                logger.debug('return code=%d' % asynsd.returncode)
                logger.info('asynscheduler : [stop] - pid=%s, count=%s/%s'
                             % (asynsd.pid, count, cf['observer.restart.count']))
                asynsd = asynscheduler() # restart
                count -= 1
                logger.info('asynscheduler : [start] - pid=%s, count=%s/%s'
                                  % (asynsd.pid, count, cf['observer.restart.count']))
            else:
                simple_log.append('asynscheduler (running) - count=%s/%s' % ( count, cf['observer.restart.count']))
                logger.debug('asynscheduler [running] - pid=%s, count=%s/%s'
                             % (asynsd.pid, count, cf['observer.restart.count']))

            logger.info(str(simple_log)[1:-1])
            
            # status output
            status(count, status_count, default_count, False)
    
            if ( 0 < cf['observer.restart.count.clear.time'] ) and (count <= 0):
                epoint = time.time()
                interval = int(math.ceil(epoint) - math.floor(spoint))
                logger.error('observer restart count reached the value specified in config. Checking interval time.  observer.restart.count=%s interval=%d/%s'
                             % (cf['observer.restart.count'], interval, cf['observer.restart.count.clear.time']))
            
                if interval < cf['observer.restart.count.clear.time']:
                    # Failed 'observer.restart.count' times in 'observer.restart.count.clear.time' seconds.
                    logger.error('observer restarted %s times in count.clear.time seconds interval. Recognizing as failure. Exiting.'
                                 % cf['observer.restart.count'])
                    break
                else:
                    # Failed 'observer.restart.count' times in an interval longer than
                    # 'observer.restart.count.clear.time' seconds. Clearing counter.
                    spoint = time.time()
                    count = cf['observer.restart.count']
                    logger.info('observer restarted %s times, but in not short time. Clearing count. start time %s'
                                 % (cf['observer.restart.count'], astrftime(spoint)))
                                      
            time.sleep(cf['observer.check.interval'])

        # -- end while
        
    finally:
        # destroy
        # scheduler
        if not sd is None:
            if kill_proc(sd) is True:
                logger.info('KILL %d: killing scheduler succeeded.' % sd.pid)
            else:
                logger.info('KILL %d: killing scheduler failed.' % sd.pid)
        # performer
        if not pf is None:
            if kill_proc(pf) is True:
                logger.info('KILL %d: killing performer succeeded.' % pf.pid)
            else:
                logger.info('KILL %d: killing performer failed.' % pf.pid)
        # asynscheduler
        if not asynsd is None:
            if kill_proc(asynsd) is True:
                logger.info('KILL %d: killing asynscheduler succeeded.' % asynsd.pid)
            else:
                logger.info('KILL %d: killing asynscheduler failed.' % asynsd.pid)
   
        if not asynpf is None:
            if kill_proc(asynpf) is True:
                logger.info('KILL %d: killing asynperformer succeeded.' % asynpf.pid)
            else:
                logger.info('KILL %d: killing asynperformer failed.' % asynpf.pid)

    return PROCERROR

# -- daemon
def daemonize(stdin, stdout, stderr, pidfile):
    """The state is changed into daemon.
    """
    logger = logging.getLogger('pysilhouette.daemonize')

    try:
        pid = os.fork()
        if pid > 0: sys.exit(0)
    except OSError as e:
        print('fork #1 failed: (%d) %s\n' % (e.errno, e.strerror), file=sys.stderr)
        logger.error('fork #1 failed: (%d) %s\n' % (e.errno, e.strerror))
        sys.exit(1)
    os.chdir('/')
    os.umask(0)
    os.setsid()
    try:
        pid = os.fork()
        if pid > 0: sys.exit(0)
    except OSError as e:
        print('fork #2 failed: (%d) %s\n' % (e.errno, e.strerror), file=sys.stderr)
        logger.error('fork #2 failed: (%d) %s\n' % (e.errno, e.strerror))
        sys.exit(1)
    # Write pid.
    pid=''
    try:
        f = file(pidfile, 'w')
        pid = os.getpid()
        f.write('%d' % pid)
        f.close()
    except IOError:
        print('file=%s - daemonize: failed to write pid to %s' % (pidfile , pid), file=sys.stderr)
        logger.error('file=%s - daemonize: failed to write pid to %s' % (pidfile , pid))
        sys.exit(1)

    for f in sys.stdout, sys.stderr: f.flush()
    sin = file(stdin, 'r')
    sout = file(stdout, 'a+')
    serr = file(stderr, 'a+')
    os.dup2(sin.fileno(), sys.stdin.fileno())
    os.dup2(sout.fileno(), sys.stdout.fileno())
    os.dup2(serr.fileno(), sys.stderr.fileno())

    return pid

if __name__ == '__main__':
    pass
