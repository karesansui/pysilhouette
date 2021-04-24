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

import os
import sys
import time
import signal
import traceback
import logging

from pysilhouette import PROCERROR, PROCSUCCESS
from pysilhouette.er import ER
from pysilhouette.db import create_database, Database
from pysilhouette.log import reload_conf
from pysilhouette.prep import readconf, getopts, chkopts, parse_conf

ENTITYS = ('performer',)

class Scheduler(ER):
    """Scheduler Class
    """
    def __init__(self, opts, cf):
        ER.__init__(self, opts, cf)
        for entity in ENTITYS:
            self._fifo(entity)

        self._setdaemon()
        create_database(cf)

    def process(self):
        self.logger.info('scheduler : [started]')
        while True:
            try:
                for entity in ENTITYS:
                    fp = open(self.cf["%s.mkfifo.path" % entity], 'w')
                    try:
                        fp.write(str(self.cf['%s.mkfifo.start.code' % entity]))

                        #self.logger.info('Start code was written. - file=%s : code=%s' % (self.cf["%s.mkfifo.path" % entity], self.cf['%s.mkfifo.start.code' % entity]))
                        self.logger.info('Activity Information. - [fifo code=%s]' % (self.cf['%s.mkfifo.start.code' % entity]))
                    finally:
                        fp.close()

                self.logger.debug('interval start, interval=%s' % (self.cf['scheduler.interval']))
                time.sleep(self.cf['scheduler.interval'])

            except IOError as i:
                if i.errno == 4:
                    return PROCSUCCESS # When ending with the signal

        return PROCERROR # beyond expectation

def sigterm_handler(signum, frame):
    logger = logging.getLogger('pysilhouette.scheduler.signal')
    logger.warning('Stop the schedulerd with signal- pid=%s, signal=%s' % (os.getpid(), signum))

    
def main():
    (opts, args) = getopts()
    if chkopts(opts) is True:
        return PROCERROR

    cf = readconf(opts.config)
    if cf is None:
        print('Failed to load the config file "%s". (%s)' % (opts.config, sys.argv[0]), file=sys.stderr)
        return PROCERROR
    
    # conf parse
    if parse_conf(cf) is False:
        return PROCERROR

    if reload_conf(cf["env.sys.log.conf.path"]):
        logger = logging.getLogger('pysilhouette.scheduler')
    else:
        print('Failed to load the log file. (%s)' % sys.argv[0], file=sys.stderr)
        return PROCERROR
    
    try:
        try:
            signal.signal(signal.SIGTERM, sigterm_handler)
            scheduler = Scheduler(opts, cf)
            ret = scheduler.process() # start!!
            return ret
        except KeyboardInterrupt as k:
            logger.critical('Keyboard interrupt occurred. - %s' % str(k.args))
            print('Keyboard interrupt occurred. - %s' % str(k.args), file=sys.stderr)
        except Exception as e:
            logger.critical('A system error has occurred. - %s' % str(e.args))
            print('A system error has occurred. - %s' % str(e.args), file=sys.stderr)
            print(traceback.format_exc(), file=sys.stderr)
            t_logger = logging.getLogger('pysilhouette_traceback')
            t_logger.critical(traceback.format_exc())
            
    finally:
        if opts.daemon is True and os.path.isfile(opts.pidfile):
            os.unlink(opts.pidfile)
            logger.warning('Process file has been deleted.. - pidfile=%s' % opts.pidfile)

    return PROCERROR

if __name__ == '__main__':
    sys.exit(main())
