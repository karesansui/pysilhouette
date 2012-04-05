#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import os

fpath = '/tmp/pysilhouette_job_success.txt'

if __name__ == '__main__':
    fp= open(fpath, 'w')
    fp.write('Success!!\n')
    fp.close()
    os.unlink(fpath)
    print >>sys.stdout, 'stdout : Success!!'
    sys.exit(0)
