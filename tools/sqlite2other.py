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


Database copy command.

example postgres) 
    python sqlite2other.py --input=sqlite:////var/lib/pysilhouette/pysilhouette.db --output=postgres://username:password@hostname:port/database 

example mysql)
    python sqlite2other.py --input=sqlite:////var/lib/pysilhouette/pysilhouette.db --output=mysql://username:password@hostname/database?charset=utf8

"""

import sys
import os
import logging

from optparse import OptionParser, OptionValueError

try:
    import sqlalchemy
    import pysilhouette
except ImportError, e:
    print >>sys.stderr, "".join(e.args)
    sys.exit(1)

import warnings
from sqlalchemy.exc import SADeprecationWarning
#warnings.filterwarnings('ignore', category=SADeprecationWarning)
#warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings("ignore", "", Warning, "", 0)


from pysilhouette.prep import getopts, readconf, chkopts
from pysilhouette.db import Database, reload_mappers
from pysilhouette.db.model import JobGroup, Job

usage = "%prog [options]"
version = "%prog 0.1"

DEBUG = False
DATABASE_MODULES = {
    "ibase":["kinterbasdb"],
    "maxdb":["sapdb"],
    "mysql":["MySQLdb"],
    "oracle":["cx_Oracle"],
    "postgres":["psycopg2"],
    "sqlite":["pysqlite2","sqlite3"],
}

def is_connect(url):
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import OperationalError
        engine = create_engine(url, echo=False, convert_unicode=True)
        connection = engine.connect()
        connection.close()
        return True
    except Exception, e:
        print >>sys.stderr, "[Error] connection refused - %s" % str(e.args)
        return False

def getopts():
    optp = OptionParser(usage=usage, version=version)
    # http://www.sqlalchemy.org/docs/05/dbengine.html?highlight=rfc#create-engine-url-arguments
    optp.add_option('-i', '--input', dest='input', help='Original database. bind-url. RFC-1738')
    optp.add_option('-o', '--output', dest='output', help='Copy, bind-url. RFC-1738')

    return optp.parse_args() 

def chkopts(opts):
    if not opts.input:
        print >>sys.stderr, "sqlite2other: --input or -i is required."
        return True
    else:
        if is_connect(opts.input) is False:
            print >>sys.stderr, \
                  "sqlite2other:bind-url \"--input\" is invalid. - input=%s" % opts.input
            return True

    if not opts.output:
        print >>sys.stderr, "sqlite2other: --output or -o is required."
        return True        
    else:
        if is_connect(opts.output) is False:
            print >>sys.stderr, \
            "sqlite2other:bind-url \"--output\" is invalid. - output=%s" % opts.output
            return True

    return False

def main():
    (opts, args) = getopts()
    if chkopts(opts) is True:
        return 1
    
    try:
        input_db = Database(opts.input,
                      encoding="utf-8",
                      convert_unicode=True,
                      assert_unicode=DEBUG,
                      echo=DEBUG,
                      echo_pool=DEBUG
                      )

        reload_mappers(input_db.get_metadata())

        output_db = Database(opts.output,
                      encoding="utf-8",
                      convert_unicode=True,
                      assert_unicode=DEBUG,
                      echo=DEBUG,
                      echo_pool=DEBUG
                      )

        reload_mappers(output_db.get_metadata())

    except Exception, e:
        print >>sys.stderr, 'Initializing a database error'
        raise

    try:
        input_session = input_db.get_session()
        jobgroups= input_session.query(JobGroup).all()
    except:
        raise

    output_jobgroups = []
    for j in jobgroups:
        _jobgroup = JobGroup(j.name, j.uniq_key)
        _jobgroup.id = j.id
        #_jobgroup.name = j.name
        #_jobgroup.uniq_key = j.uniq_key
        _jobgroup.finish_command = j.finish_command
        _jobgroup.status = j.status
        _jobgroup.register = j.register
        _jobgroup.created = j.created
        _jobgroup.modified = j.modified
        for job in j.jobs:
            _job = Job(job.name, job.order, job.action_command)
            _job.id = job.id
            _job.jobgroup_id = job.jobgroup_id
            #_job.name = job.name
            #_job.order = job.order
            #_job.action_command = job.action_command
            _job.rollback_command = job.rollback_command
            _job.status = job.status
            _job.action_exit_code = job.action_exit_code
            _job.action_stdout = job.action_stdout
            _job.action_stderr = job.action_stderr
            _job.rollback_exit_code = job.rollback_exit_code
            _job.rollback_stdout = job.rollback_stdout
            _job.rollback_stderr = job.rollback_stderr
            _job.progress = job.progress
            _job.created = job.created
            _job.modified = job.modified
            ##
            _jobgroup.jobs.append(_job)

        ##
        output_jobgroups.append(_jobgroup)

    try:
        output_db.get_metadata().drop_all()
        output_db.get_metadata().create_all()
        print >>sys.stdout, 'Cleanup Database [OK]'
        output_session = output_db.get_session()
        for j in output_jobgroups:
            #import pdb; pdb.set_trace()
            output_session.save(j)
        output_session.commit()
        print >>sys.stderr, 'copy num - %d' % len(output_jobgroups)
        
    except Exception,e:
        print >>sys.stderr, 'database drop and create error.'
        raise


    return 0

if __name__ == '__main__':
    sys.exit(main())
