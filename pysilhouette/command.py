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
import logging
import sys
import traceback

import pysilhouette.prep
import pysilhouette.log
from pysilhouette.util import is_empty
from pysilhouette.db import Database
from pysilhouette.db.model import reload_mappers
from pysilhouette.db.access import \
     get_progress as dba_get_progress, \
     up_progress as dba_up_progress

# lib
def dict2command(cmd, options={}):
    """ Provides simple method to build up 
    "/usr/bin/foo --key1=value1 --key2=value2"
    styled command line.
    @param cmd: command path to be executed.
    @type cmd: string
    @param options: dictionary which contains
        {key: value} to be transformed into
        "--key=value". Defaults to {}.
        If you like to pass a flag styled option(like --flag),
        just put None into value.
    @type options: dictionary
    @return: command line in single string.
    """
    if is_empty(cmd):
        raise CommandException("command not found. - cmd=%s" % cmd)

    ret = ""
    for x in list(options.keys()):
        if options[x] is None:
            ret += "--%s " % x 
        else:
            try:
                options[x].index(' ')
                ret += "--%s=\"%s\" " % (x, options[x])
            except:
                ret += "--%s=%s " % (x, options[x])
    return "%s %s" % (cmd.strip(), ret.strip())

# public
class CommandException(Exception):
    """Command execution error.
    """
    pass

class Command:
    """Command is a class designed to assist implmentation of CLI programs.
    Expacted to be inherited.
    """

    cf = None
    logger = None

    def __init__(self):
        if ('PYSILHOUETTE_CONF' in os.environ) is False:
            print('[Error] "PYSILHOUETTE_CONF" did not exist in the environment.', file=sys.stderr)
            sys.exit(1)
            
        self.cf = pysilhouette.prep.readconf(os.environ['PYSILHOUETTE_CONF'])
        if self.logger is None:
            pysilhouette.log.reload_conf(self.cf["env.sys.log.conf.path"])
            self.logger = logging.getLogger('pysilhouette.command') 

        try:
            self.db = Database(self.cf['database.url'],
                          encoding="utf-8",
                          convert_unicode=True,
                          #assert_unicode='warn', # DEBUG
                          echo = False,
                          echo_pool = False,
                          )

            reload_mappers(self.db.get_metadata())
            self.session = self.db.get_session()
        except Exception as e:
            print('[Error] Initializing a database error - %s' % str(e.args), file=sys.stderr)
            self.logger.error('Initializing a database error - %s' % str(e.args))
            t_logger = logging.getLogger('pysilhouette_traceback')
            t_logger.error(traceback.format_exc())
            sys.exit(1)

    def _pre(self):
        if ('JOB_ID' in os.environ) is False:
            self.logger.debug('"JOB_ID" did not exist in the environment.')
            self.job_id = None
        else:
            self.job_id = os.environ['JOB_ID']
            self.logger.debug('Command JOB_ID=%s' % self.job_id)
            
        return True
            
    def _post(self):
        return True
    
    def run(self):
        try:
            try:
                try:
                    if self._pre() is False:
                        CommandException("Error running in _pre().")
                    if self.process() is False:
                        CommandException("Error running in process().")
                    if self._post() is False:
                        CommandException("Error running in _post().")
                         
                    return 0
                
                except CommandException as e:
                    self.logger.error("Command execution error - %s" % str(e.args))
                    print(_("Command execution error - %s") % str(e.args), file=sys.stderr)
                    raise
            except:
                self.session.rollback()
                return 1
        finally:
            self.session.commit()

    def process(self):
        raise CommandException('Please use the override.')

    def up_progress(self, r):
        """ Increments progress counter by r.
        If the counter reaches 100, then it will be 100 regardless of the value of r.
        @param r: Amount to increment.
        @type r: int
        """
        if self.job_id is None:
            self.logger.warn('up_progress called but no job ID is assigned with this object. Ignoring.')
            return None
        else:
            return dba_up_progress(self.session, self.job_id, r)
        
    def get_progress(self):
        """ Returns the current progress counter.
        @return: Progress counter value on success (0-100). -1 on failure.
        """
        if self.job_id is None:
            self.logger.warn('get_progress called but no job ID is assigned with this object. Ignoring and returning -1.')
            return -1
        else:
            ret = dba_get_progress(self.session, self.job_id)
            self.session.commit()
            return ret

if __name__ == '__main__':
    pass
