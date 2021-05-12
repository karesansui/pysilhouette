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
from __future__ import print_function

import re
import sys
import os
import pwd
import grp
from optparse import OptionParser

try:
    from io import StringIO
except ImportError:
    from io import StringIO

from pysilhouette import __version__

usage = '%prog [options]'

def getopts():
    optp = OptionParser(usage=usage, version=__version__)
    optp.add_option('-c', '--config', dest='config', help='configuration file')
    optp.add_option('-d', '--daemon', dest='daemon', action="store_true", help='Daemon startup')
    optp.add_option('-v', '--verbose', dest='verbose', action="store_true", help='Has not been used.')
    optp.add_option('-p', '--pidfile', dest='pidfile', action="store", type='string', help='process file path')
    optp.add_option('-k', '--uniqkey', dest='uniqkey', action="store_true", help='show unique key')
    return optp.parse_args()

def chkopts(opts):
    if not opts.config:
        print('-c or --config option is required.', file=sys.stderr)
        return True

    if os.path.isfile(opts.config) is False:
        print('-c or --config file is specified in the option does not exist.', file=sys.stderr)
        return True

    if opts.uniqkey:
        return False

    if opts.daemon is True and not opts.pidfile:
        print('-p or --pidfile option is required.', file=sys.stderr)
        return True

    if not opts.daemon and opts.pidfile:
        print('-p doesn work without -d. Please add the option to -d or --daemon.', file=sys.stderr)
        return True

    return False

def parse_conf(cf):
    from pysilhouette.util import is_int, is_key, set_cf_int
    from pysilhouette.uniqkey import is_uuid

    # env
    err_key = ""
    if len(err_key) <= 0 and is_key(cf, "env.python") is False:
        err_key = "env.python"
    if len(err_key) <= 0 and is_key(cf, "env.sys.log.conf.path") is False:
        err_key = "env.sys.log.conf.path"
    if len(err_key) <= 0 and is_key(cf, "env.uniqkey") is False:
        err_key = "env.uniqkey"
    if len(err_key) <= 0 and is_key(cf, "daemon.stdin") is False:
        err_key = "daemon.stdin"
    if len(err_key) <= 0 and is_key(cf, "daemon.stdout") is False:
        err_key = "daemon.stdout"
    if len(err_key) <= 0 and is_key(cf, "daemon.stderr") is False:
        err_key = "daemon.stderr"
    if len(err_key) <= 0 and is_key(cf, "observer.target.python") is False:
        err_key = "observer.target.python"
    if len(err_key) <= 0 and is_key(cf, "observer.target.scheduler") is False:
        err_key = "observer.target.scheduler"
    if len(err_key) <= 0 and is_key(cf, "observer.target.performer") is False:
        err_key = "observer.target.performer"
    if len(err_key) <= 0 and is_key(cf, "observer.restart.count") is False:
        err_key = "observer.restart.count"
    if len(err_key) <= 0 and is_key(cf, "observer.restart.count.clear.time") is False:
        err_key = "observer.restart.count.clear.time"
    if len(err_key) <= 0 and is_key(cf, "observer.check.interval") is False:
        err_key = "observer.check.interval"
    if len(err_key) <= 0 and is_key(cf, "observer.status.path") is False:
        err_key = "observer.status.path"

    # performer
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.start.code") is False:
        err_key = "performer.mkfifo.start.code"
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.ignore.code") is False:
        err_key = "performer.mkfifo.ignore.code"
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.stop.code") is False:
        err_key = "performer.mkfifo.stop.code"
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.user.name") is False:
        err_key = "performer.mkfifo.user.name"
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.group.name") is False:
        err_key = "performer.mkfifo.group.name"
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.perms") is False:
        err_key = "performer.mkfifo.perms"
    if len(err_key) <= 0 and is_key(cf, "performer.mkfifo.path") is False:
        err_key = "performer.mkfifo.path"

    # asynperformer
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.start.code") is False:
        err_key = "asynperformer.mkfifo.start.code"
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.ignore.code") is False:
        err_key = "asynperformer.mkfifo.ignore.code"
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.stop.code") is False:
        err_key = "asynperformer.mkfifo.stop.code"
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.user.name") is False:
        err_key = "asynperformer.mkfifo.user.name"
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.group.name") is False:
        err_key = "asynperformer.mkfifo.group.name"
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.perms") is False:
        err_key = "asynperformer.mkfifo.perms"
    if len(err_key) <= 0 and is_key(cf, "asynperformer.mkfifo.path") is False:
        err_key = "asynperformer.mkfifo.path"

    # asynscheduler
    if len(err_key) <= 0 and is_key(cf, "asynscheduler.interval") is False:
                err_key = "asynscheduler.interval"

    if len(err_key) <= 0 and is_key(cf, "scheduler.interval") is False:
        err_key = "scheduler.interval"
    if len(err_key) <= 0 and is_key(cf, "job.popen.env.lang") is False:
        err_key = "job.popen.env.lang"
    if len(err_key) <= 0 and is_key(cf, "job.popen.timeout") is False:
        err_key = "job.popen.timeout"
    if len(err_key) <= 0 and is_key(cf, "job.popen.waittime") is False:
        err_key = "job.popen.waittime"
    if len(err_key) <= 0 and is_key(cf, "job.popen.output.limit") is False:
        err_key = "job.popen.output.limit"

    if len(err_key) <= 0 and is_key(cf, "database.url") is False:
        err_key = "database.url"
    if len(err_key) <= 0 and is_key(cf, "database.pool.status") is False:
        err_key = "database.pool.status"

    if is_uuid(cf["env.uniqkey"]) is False:
        print('UUID format is not set. - env.uniqkey', file=sys.stderr)
        return False

    if 0 < len(err_key):
        print('Configuration files are missing. - %s' % (err_key), file=sys.stderr)
        return False

    if os.access(cf["env.python"], os.R_OK | os.X_OK) is False:
        print('Incorrect file permissions. - env.python=%s' % (cf["env.python"]), file=sys.stderr)
        return False

    if os.access(cf["observer.target.python"], os.R_OK | os.X_OK) is False:
        print('Incorrect file permissions. - observer.target.python=%s' % (cf["observer.target.python"]), file=sys.stderr)
        return False

    if os.access(cf["observer.target.scheduler"], os.R_OK) is False:
        print('Incorrect file permissions. - observer.target.scheduler=%s' % (cf["observer.target.scheduler"]), file=sys.stderr)
        return False

    if os.access(cf["observer.target.performer"], os.R_OK) is False:
        print('Incorrect file permissions. - observer.target.performer=%s' % (cf["observer.target.performer"]), file=sys.stderr)
        return False

    if is_int(cf["observer.restart.count"]) is False:
        print('Must be a number. - observer.restart.count=%s' % (cf["observer.restart.count"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "observer.restart.count")

    if is_int(cf["observer.restart.count.clear.time"]) is False:
        print('Must be a number. - observer.restart.count.clear.time=%s' % (cf["observer.restart.count.clear.time"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "observer.restart.count.clear.time")

    if is_int(cf["observer.check.interval"]) is False:
        print('Must be a number. - observer.check.interval=%s' % (cf["observer.check.interval"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "observer.check.interval")

    # performer
    if is_int(cf["performer.mkfifo.start.code"]) is False:
        print('Must be a number. - performer.mkfifo.start.code=%s' % (cf["performer.mkfifo.start.code"]), file=sys.stderr)
        return False

    if is_int(cf["performer.mkfifo.ignore.code"]) is False:
        print('Must be a number. - performer.mkfifo.ignore.code=%s' % (cf["performer.mkfifo.ignore.code"]), file=sys.stderr)
        return False

    if is_int(cf["performer.mkfifo.stop.code"]) is False:
        print('Must be a number. - performer.mkfifo.stop.code=%s' % (cf["performer.mkfifo.stop.code"]), file=sys.stderr)
        return False

    # asynperformer
    if is_int(cf["asynperformer.mkfifo.start.code"]) is False:
        print('Must be a number. - asynperformer.mkfifo.start.code=%s' % (cf["asynperformer.mkfifo.start.code"]), file=sys.stderr)
        return False

    if is_int(cf["asynperformer.mkfifo.ignore.code"]) is False:
        print('Must be a number. - asynperformer.mkfifo.ignore.code=%s' % (cf["asynperformer.mkfifo.ignore.code"]), file=sys.stderr)
        return False

    if is_int(cf["asynperformer.mkfifo.stop.code"]) is False:
        print('Must be a number. - asynperformer.mkfifo.stop.code=%s' % (cf["asynperformer.mkfifo.stop.code"]), file=sys.stderr)
        return False

    if is_int(cf["asynscheduler.interval"]) is False:
        print('Must be a number. - asynscheduler.interval=%s' % (cf["asynscheduler.interval"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "asynscheduler.interval")

    if is_int(cf["scheduler.interval"]) is False:
        print('Must be a number. - scheduler.interval=%s' % (cf["scheduler.interval"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "scheduler.interval")

    if is_int(cf["job.popen.timeout"]) is False:
        print('Must be a number. - job.popen.timeout=%s' % (cf["job.popen.timeout"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "job.popen.timeout")

    if is_int(cf["job.popen.waittime"]) is False:
        print('Must be a number. - job.popen.waittime=%s' % (cf["job.popen.waittime"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "job.popen.waittime")

    if is_int(cf["job.popen.output.limit"]) is False:
        print('Must be a number. - job.popen.output.limit=%s' % (cf["job.popen.output.limit"]), file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "job.popen.output.limit")

    # performer
    p_mkfifo = set([cf["performer.mkfifo.start.code"],
                    cf["performer.mkfifo.ignore.code"],
                    cf["performer.mkfifo.stop.code"]],
                   )
    if len(p_mkfifo) != 3:
        print('Is not unique. - performer.mkfifo.[start,ignore,stop]=%s,%s,%s' \
              % (cf["performer.mkfifo.start.code"],
                 cf["performer.mkfifo.ignore.code"],
                 cf["performer.mkfifo.stop.code"],
                 ), file=sys.stderr)
        return False

    try:
        pwd.getpwnam(cf["performer.mkfifo.user.name"])
    except:
        print('Can not get information of the user (nonexistent?). - performer.mkfifo.user.name=%s' % (cf["performer.mkfifo.user.name"]), file=sys.stderr)

    try:
        grp.getgrnam(cf["performer.mkfifo.group.name"])
    except:
        print('Can not get information of the group (nonexistent?). - performer.mkfifo.group.name=%s' % (cf["performer.mkfifo.group.name"]), file=sys.stderr)

    try:
        int(cf["performer.mkfifo.perms"], 8)
    except:
        print('Incorrect file permissions. - performer.mkfifo.perms=%s' % (cf["performer.mkfifo.perms"]), file=sys.stderr)
        return False

    # asynperformer
    a_mkfifo = set([cf["asynperformer.mkfifo.start.code"],
                    cf["asynperformer.mkfifo.ignore.code"],
                    cf["asynperformer.mkfifo.stop.code"]],
                   )
    if len(a_mkfifo) != 3:
        print('Is not unique. - asynperformer.mkfifo.[start,ignore,stop]=%s,%s,%s' \
              % (cf["asynperformer.mkfifo.start.code"],
                 cf["asynperformer.mkfifo.ignore.code"],
                 cf["asynperformer.mkfifo.stop.code"],
                 ), file=sys.stderr)
        return False

    try:
        pwd.getpwnam(cf["asynperformer.mkfifo.user.name"])
    except:
        print('Can not get information of the user (nonexistent?). - asynperformer.mkfifo.user.name=%s' % (cf["asynperformer.mkfifo.user.name"]), file=sys.stderr)

    try:
        grp.getgrnam(cf["asynperformer.mkfifo.group.name"])
    except:
        print('Can not get information of the group (nonexistent?). - asynperformer.mkfifo.group.name=%s' % (cf["asynperformer.mkfifo.group.name"]), file=sys.stderr)

    try:
        int(cf["asynperformer.mkfifo.perms"], 8)
    except:
        print('Incorrect file permissions. - asynperformer.mkfifo.perms=%s' % (cf["asynperformer.mkfifo.perms"]), file=sys.stderr)
        return False

    if ("job.whitelist.flag" in cf) is True \
           and cf["job.whitelist.flag"] == "1" \
           and ("job.whitelist.path" in cf) is True \
           and 0 < len(cf["job.whitelist.path"]):
        if os.path.isfile(cf["job.whitelist.path"]) is False:
            print('File not found. - job.whitelist.path=%s' % (cf["job.whitelist.path"]), file=sys.stderr)
            return False

    # database.pool.status
    if (cf["database.pool.status"] in ("0","1")) is False:
        print('The mistake is found in the set value. Please set 0 or 1. - database.pool.status', file=sys.stderr)
        return False

    if cf["database.pool.status"] == "1":
        # database.pool.max.overflow
        if ("database.pool.max.overflow" in cf) is False:
            print('Configuration information is missing. - database.pool.max.overflow', file=sys.stderr)
            return False

        # database.pool.size
        if ("database.pool.size" in cf) is False:
            print('Configuration information is missing. - database.pool.size', file=sys.stderr)
            return False

        # int
        if is_int(cf["database.pool.max.overflow"]) is False:
            print('Please set it by the numerical value. - database.pool.max.overflow', file=sys.stderr)
            return False
        else:
            set_cf_int(cf, "database.pool.max.overflow")

        if is_int(cf["database.pool.size"]) is False:
            print('Please set it by the numerical value. - database.pool.size', file=sys.stderr)
            return False
        else:
            set_cf_int(cf, "database.pool.size")

        if int(cf["database.pool.size"]) <= 0:
            print('Please set values that are larger than 0. - database.pool.size', file=sys.stderr)
            return False
        else:
            set_cf_int(cf, "database.pool.size")

        # Comparison
        if int(cf["database.pool.max.overflow"]) < int(cf["database.pool.size"]):
            print('Please set "database.pool.max.overflow" to a value that is larger than "database.pool.size".', file=sys.stderr)
            return False

    # asynperformer.thread.pool.size
    if ("asynperformer.thread.pool.size" in cf) is False:
        print('Configuration information is missing. - asynperformer.thread.pool.size', file=sys.stderr)
        return False

    if is_int(cf["asynperformer.thread.pool.size"]) is False:
        print('Please set it by the numerical value. - asynperformer.thread.pool.size', file=sys.stderr)
        return False
    else:
        set_cf_int(cf, "asynperformer.thread.pool.size")

    if int(cf["asynperformer.thread.pool.size"]) <= 0:
        print('Please set values that are larger than 0. - asynperformer.thread.pool.size', file=sys.stderr)
        return False

    return True

def readconf(path):
    if not os.path.isfile(path):
        print('file=%s - file specified in the option does not exist.' % path, file=sys.stderr)
        return None

    fp = open(path, 'r')
    try:
        try:
            _r = {}
            for line in fp:
                line = re.sub(r'[ \t]', '', line).strip()
                if len(line) <= 0 or line[0] == '#':
                    continue
                key, value = line.split('=', 1)
                try:
                    value = value[:value.rindex('#')]
                except ValueError as ve:
                    pass
                _r[key] = value
            return _r
        except Exception as e:
            print('file=%s - Failed to load configuration files. : except=%s' \
                  % (path, e.args), file=sys.stderr)
            return None
    finally:
        fp.close()

def sysappend(pkg):
    lines = []
    if type(pkg) is list:
        lines = pkg
    else:
        print('%s should be list type.' % (pkg,), file=sys.stderr)
        return False
        
    for line in lines:
        f = False
        for path in sys.path:
            if line == path:
                f = True
                break
        if f is False:
            sys.path.insert(1, line)
    return True

if __name__ == "__main__":
    pass
