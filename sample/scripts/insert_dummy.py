#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys

from pysilhouette.command import Command
from pysilhouette.db.model import JobGroup, Job

class DummyCommand(Command):

    def insert_data(self):
        self.db.get_metadata().drop_all()
        self.db.get_metadata().create_all()

        jg_name = u'JobGroup-Dummy'
        jg_ukey = unicode(self.cf['env.uniqkey'], "utf-8")
        j_name = u'Job-Dummy'
        j_order = 0
        j_cmd = unicode( os.path.dirname(__file__) + "/dummy.py", "utf-8")
        jg = JobGroup(jg_name, jg_ukey)
        jg.jobs.append(Job(j_name, j_order, j_cmd))
        self.session.save(jg)
        self.session.commit()

if __name__ == '__main__':
    dc = DummyCommand()
    sys.exit(dc.insert_data())
