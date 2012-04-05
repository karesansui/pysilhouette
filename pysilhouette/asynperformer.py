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
import sys
import os
import logging
import traceback
import signal
import Queue

from pysilhouette import PROCERROR, PROCSUCCESS
from pysilhouette.log import reload_conf
from pysilhouette.prep import readconf, getopts, chkopts, parse_conf
from pysilhouette.db.model import JOBGROUP_STATUS, JOBGROUP_TYPE
from pysilhouette.db.access import jobgroup_findbytype_limit_status, jobgroup_update
from pysilhouette.er import ER
from pysilhouette.worker import ThreadQueue, ThreadWorker, dummy_set_job
from pysilhouette.db import create_database, Database

# var
asynpool = []

class AsynPerformer(ER):
    """AsynPerformer Class
    """
    def __init__(self, opts, cf):
        ER.__init__(self, opts, cf)
        self._fifo('asynperformer')
        self._setdaemon()
        self.db = create_database(cf)

    def process(self):
        self.logger.info('asynperformer : [started]')

        # thread pool
        request_queue = Queue.Queue()
        #response_queue = Queue.Queue()
        response_list = []
        tq = ThreadQueue(request_queue, response_list)

        while True:
            fp = open(self.cf["asynperformer.mkfifo.path"], 'r')
            try:
                code = fp.read()
            finally:
                fp.close()
                
            #self.logger.info('Received code from the FIFO file. - code=%s' % code)
            session = self.db.get_session()

            # Pending JobGroup search
            if self.cf['asynperformer.thread.pool.size'] <= tq.now_alive():
                continue
                
            m_jgs = jobgroup_findbytype_limit_status(session,
                                                     JOBGROUP_TYPE['PARALLEL'],
                                                     self.cf['asynperformer.thread.pool.size'] - tq.now_alive())

            session.close()
            #self.logger.info('Queued the Job Group from the database. - Number of JobGroup=%d' % len(m_jgs))
            #self.logger.debug('filo code=%s, cf asynperformer.mkfifo.start.code=%s' % (code, self.cf["asynperformer.mkfifo.start.code"]))
            self.logger.info('Activity Information. - [fifo_code=%s, type=serial, jobgroup_num=%d]' % (code, len(m_jgs)))
            if code == self.cf["asynperformer.mkfifo.start.code"]:
                if 0 < len(m_jgs):
                    for m_jg in m_jgs:
                        try:
                            tq.put(ThreadWorker(self.cf, self.db, m_jg.id)) # thread worker!! start
                        except Exception, e:
                            self.logger.debug('Failed to perform the job group. Exceptions are not expected. - jobgroup_id=%d : %s'
                                         % (m_jg.id, str(e.args)))
                            print >>sys.stderr, traceback.format_exc()
                            t_logger = logging.getLogger('pysilhouette_traceback')
                            t_logger.error(traceback.format_exc())
                else:
                    self.logger.debug('No Job Group.')
            elif code == self.cf["asynperformer.mkfifo.stop.code"]:
                self.logger.warning('Received stop code from the FIFO file. - code=%s' % code)
                break
            else:
                self.logger.warning('Received illegal code from the FIFO file. - code=%s' % code)

def sigterm_handler(signum, frame):
    logger = logging.getLogger('pysilhouette.asynperformer')
    logger.info('Stop the AsynPerformerd with signal - pid=%s, signal=%s' % (os.getpid(), signum))
    for x in asynpool :
        os.kill(x.pid, signum)
    sys.exit(os.getpid())

def main():
    (opts, args) = getopts()
    if chkopts(opts) is True:
        return PROCERROR
    
    cf = readconf(opts.config)
    if cf is None:
        print >>sys.stderr, 'Failed to load the config file "%s". (%s)' % (opts.config, sys.argv[0])
        return PROCERROR

    # conf parse
    if parse_conf(cf) is False:
        return PROCERROR

    # set env=PYSILHOUETTE_CONF
    os.environ['PYSILHOUETTE_CONF'] = opts.config
    
    if reload_conf(cf["env.sys.log.conf.path"]):
        logger = logging.getLogger('pysilhouette.asynperformer')
    else:
        print >>sys.stderr, 'Failed to load the log file. (%s)' % sys.argv[0]
        return PROCERROR

    try:
        try:
            signal.signal(signal.SIGTERM, sigterm_handler)
            asynperformer = AsynPerformer(opts, cf)
            ret = asynperformer.process() # start!!
            return ret
        except KeyboardInterrupt, k:
            logger.critical('Keyboard interrupt occurred. - %s' % str(k.args))
            print >>sys.stderr, 'Keyboard interrupt occurred. - %s' % str(k.args)
        except Exception, e:
            logger.critical('System error has occurred. - %s' % str(e.args))
            print >>sys.stderr, 'System error has occurred. - %s' % str(e.args)
            print >>sys.stderr, traceback.format_exc()
            t_logger = logging.getLogger('pysilhouette_traceback')
            t_logger.critical(traceback.format_exc())
            
    finally:
        if opts.daemon is True and os.path.isfile(opts.pidfile):
            os.unlink(opts.pidfile)
            logger.info('Process file has been deleted.. - pidfile=%s' % opts.pidfile)

    return PROCERROR


if __name__ == '__main__':
    sys.exit(main())
