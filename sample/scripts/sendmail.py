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

import sys
import os
import smtplib
from optparse import OptionParser, OptionValueError
from email.MIMEText import MIMEText
from email.Utils import formatdate
from email.Header import Header


usage = "%prog [options]"
version = '%prog 0.1'

charset = 'us-ascii'
encode = 'utf-8'

def getopts():
    optp = OptionParser(usage=usage, version=version)
    optp.add_option('-f', '--from', dest='ofrom', help='Mail From')
    optp.add_option('-t', '--to', dest='oto', help='RCPT TO')
    optp.add_option('-s', '--subject', dest='osubject', help='Subject')
    optp.add_option('-m', '--msg', dest='omsg', help='E-mail message (--bodyfile is the priority.)')
    optp.add_option('-b', '--bodyfile', dest='obodyfile', help='E-mail files')
    
    optp.add_option('-n', '--hostname', dest='ohostname', help='The host name of the SMTP server')
    optp.add_option('-p', '--port', dest='oport', help='The port of the SMTP server')
    optp.add_option('-c', '--charset', dest='ocharset', help='Mail character set (Default: us-ascii)')
    optp.add_option('-e', '--encode', dest='oencode', help='Enter the character code (Default: utf-8)')
    
    return optp.parse_args()

def chkopts(opts):
    if not opts.ofrom:
        print >>sys.stderr, 'sendmail: --from is required.'
        return True
    if not opts.oto:
        print >>sys.stderr, 'sendmail: --to is required.'
        return True
    if not opts.osubject:
        print >>sys.stderr, 'sendmail: --subject is required.'
        return True
    if not opts.omsg and not opts.obodyfile:
        print >>sys.stderr, 'sendmail: --msg or --bodyfile are required.'
        return True
    if not opts.omsg and opts.obodyfile:
        if not os.path.exists(opts.obodyfile):
            print >>sys.stderr, 'sendmail: --bodyfile specified in the file does not exist.'
            return True
    if not opts.ohostname:
        print >>sys.stderr, 'sendmail: --hostname is required.'
        return True
    if not opts.oport:
        print >>sys.stderr, 'sendmail: --port is required.'
        return True
    if not opts.ocharset:
        opts.ocharset = charset
    if not opts.oencode:
        opts.oencode = encode
        
    return False

def sendmail(opts):
    if opts.obodyfile:
        fp = open(opts.obodyfile, 'r')
        body = unicode(fp.read(), opts.oencode).encode(opts.ocharset,'replace')
    else:
        body = unicode(opts.omsg, opts.oencode).encode(opts.ocharset,'replace')

    msg = MIMEText(body, 'plain', opts.ocharset)
    msg['Subject'] = Header(unicode(opts.osubject, opts.oencode), opts.ocharset)
    msg['From'] = opts.ofrom
    msg['To'] = opts.oto
    msg['Date'] = formatdate()

    s = smtplib.SMTP()
    s.connect(opts.ohostname, opts.oport)
    s.sendmail(opts.ofrom, [opts.oto], msg.as_string())
    s.close()
    
def main():
    (opts, args) = getopts()
    if chkopts(opts):
        return 1
    sendmail(opts)
    
if __name__ == '__main__':
    sys.exit(main())
