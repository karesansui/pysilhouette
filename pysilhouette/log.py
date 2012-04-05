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
import logging
import logging.config

#: logging ready
ready = False

def reload_conf(log_conf='/etc/pysilhouette/log.conf'):
    """Re-logging configuration
    @param log_conf: configuration file path
    @type log_conf: str
    @rtype: bool
    @return: ready
    """
    global ready
    try:
        logging.config.fileConfig(log_conf)
        ready = True
    except:
        ready = False
    return ready
    
def is_ready():
    return ready

if __name__ == '__main__':
    """Testing
    """
    reload_conf('/etc/pysilhouette/log.conf')
    if is_ready():
        _logger = logging.getLogger('pysilhouette.log')
        _logger.debug('test')
    else:
        print >>sys.stderr('Loading configuration files still do not log.')
