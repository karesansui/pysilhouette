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
import sys
import signal
import logging
import traceback

try:
    import sqlalchemy
except ImportError as e:
    print('[Error] There are not enough libraries. - %s' % str(e.args), file=sys.stderr)
    #traceback.format_exc()
    sys.exit(1)

from pysilhouette import PROCERROR, PROCSUCCESS
from pysilhouette.prep import readconf, getopts, chkopts, parse_conf
from pysilhouette.daemon import daemonize, observer
from pysilhouette.log import reload_conf

opt = None #: command options

def sigterm_handler(signum, frame):
    global opt
    logger = logging.getLogger('pysilhouette.silhouette.signal')
    logger.info('Stop the schedulerd with signal- pid=%s, signal=%s' % (os.getpid(), signum))
    if opts.daemon is True and os.path.isfile(opts.pidfile):
        os.unlink(opts.pidfile)
        logger.info('Process file has been deleted.. - pidfile=%s' % opts.pidfile)

def main():
    global opts

    (opts, args) = getopts()
    if chkopts(opts) is True:
        return PROCERROR
    
    ####
    try:
        opts.config = os.path.abspath(opts.config)
    except AttributeError as e:
        print('No configuration file path.', file=sys.stderr)
        return PROCERROR
    
    cf = readconf(opts.config)
    if cf is None:
        print('Failed to load the config file "%s". (%s)' % (opts.config, sys.argv[0]), file=sys.stderr)
        return PROCERROR

    # conf parse
    if parse_conf(cf) is False:
        return PROCERROR
    
    if reload_conf(cf["env.sys.log.conf.path"]):
        logger = logging.getLogger('pysilhouette.silhouette')
    else:
        print('Failed to load the log file. (%s)' % sys.argv[0], file=sys.stderr)
        return PROCERROR

    if opts.uniqkey:
        print(cf["env.uniqkey"], file=sys.stdout)
        return PROCSUCCESS

    if opts.daemon is True:
        logger.debug('Daemon stdin=%s' % cf['daemon.stdin'])
        logger.debug('Daemon stdout=%s' % cf['daemon.stdout'])
        logger.debug('Daemon stderr=%s' % cf['daemon.stderr'])
        pid = daemonize(stdin=cf['daemon.stdin'],
                        stdout=cf['daemon.stdout'],
                        stderr=cf['daemon.stderr'],
                        pidfile=opts.pidfile)
        logger.info('Daemon Running!! pid=%s' % pid)

    try:
        signal.signal(signal.SIGTERM, sigterm_handler)
        ret = observer(opts=opts, cf=cf) # start!!
        return ret
    except KeyboardInterrupt as k:
        logger.critical('Keyboard interrupt occurred. - %s' % str(k.args))
        print('Keyboard interrupt occurred. - %s' % str(k.args), file=sys.stderr)
    except Exception as e:
        logger.critical('System error has occurred. - %s' % str(e.args))
        print('System error has occurred. - %s' % str(e.args), file=sys.stderr)
        t_logger = logging.getLogger('pysilhouette_traceback')
        t_logger.critical(traceback.format_exc())
        print(traceback.format_exc(), file=sys.stderr)

    return PROCERROR

if __name__ == '__main__':
    sys.exit(main())
