#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys

from pysilhouette.command import Command

class DummyCommand(Command):

    def process(self):
        import time
        for x in xrange(0, 10):
            time.sleep(1)
            self.up_progress(10)
            
        return True
if __name__ == '__main__':
    dc = DummyCommand()
    sys.exit(dc.run())
