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

import logging
import os

from pysilhouette.util import kill_proc, write_pidfile, create_fifo

class ER:
    """ER Class
    """

    def __init__(self, opts, cf):
        self.logger = logging.getLogger('pysilhouette.%s' % self.__class__.__name__.lower())
        #self.entity = self.__class__.__name__.lower()
        self.opts = opts
        self.cf = cf

    def _fifo(self, prefix):
        if os.access(self.cf["%s.mkfifo.path" % prefix], os.F_OK|os.R_OK|os.W_OK) is False:
            try:
                os.unlink(self.cf["%s.mkfifo.path" % prefix])
                self.logger.info('Deleted filo file. - file=%s' \
                                          % self.cf["%s.mkfifo.path" % prefix])
            except:
                pass # Not anything

            try:
                create_fifo(self.cf["%s.mkfifo.path" % prefix],
                            self.cf["%s.mkfifo.user.name" % prefix],
                            self.cf["%s.mkfifo.group.name" % prefix],
                            self.cf["%s.mkfifo.perms" % prefix],
                            )
            except OSError, oe:
                self.logger.error('Failed to create a fifo file.')
                raise oe

            self.logger.info('The fifo file was created. - file=%s' \
                             % self.cf["%s.mkfifo.path" % prefix])
            return True

    def _setdaemon(self):
        if self.opts.daemon is True:
            pid = os.getpid()
            try:
                write_pidfile(self.opts.pidfile, pid)
            except Exception:
                self.logger.error('Could not create process file. - file=%s' % self.opts.pidfile)
                raise e

            self.logger.info('The process file was created. - file=%s' % self.opts.pidfile)
            return True
