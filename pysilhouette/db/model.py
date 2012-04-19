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

import sqlalchemy
import sqlalchemy.exc
from sqlalchemy.orm import mapper, relation, clear_mappers

from pysilhouette.util import is_empty

# Job Constant
_RES_CREATING = u'100' #: Creating
_RES_PENDING = u'101' #: Pending
_RES_RUNNING = u'102' #: Running
_RES_ROLLBACK = u'103' #: Rollback running
_RES_NORMAL_END = u'200' #: Normal end
_RES_ROLLBACK_SUCCESSFUL_COMPLETION = u'201' #: Rollback successful completion
_RES_ABNORMAL_TERMINATION = u'500' #: Abnormal termination
_RES_ROLLBACK_ABEND = u'501' #: Rollback abend
_RES_APP_ERROR = u'502' #: Application error
_RES_WHITELIST_ERROR = u'503' #: Whitelist error

#: Action command status.
ACTION_STATUS = {
    'PEND' : _RES_PENDING,
    'RUN' : _RES_RUNNING,
    'OK' : _RES_NORMAL_END,
    'NG' : _RES_ABNORMAL_TERMINATION,
    'WHITELIST' : _RES_WHITELIST_ERROR,
    }
#: Rollback command status.
ROLLBACK_STATUS = {
    'RUN' : _RES_ROLLBACK,
    'OK' : _RES_ROLLBACK_SUCCESSFUL_COMPLETION,
    'NG' : _RES_ROLLBACK_ABEND,
    'WHITELIST' : _RES_WHITELIST_ERROR,
    }

#: Jobgroup status
JOBGROUP_STATUS = {
    'PEND' : _RES_PENDING,
    'RUN' : _RES_RUNNING,
    'OK' : _RES_NORMAL_END,
    'NG' : _RES_ABNORMAL_TERMINATION,
    'APPERR' : _RES_APP_ERROR,
    }

#: Jobgroup type
JOBGROUP_TYPE = {
    'SERIAL': 0, #Serial
    'PARALLEL' : 1, #Parallel
    }

#: Jobgroup Table instance.
def get_jobgroup_table(metadata, now):
    return sqlalchemy.Table('jobgroup', metadata,
                            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True,
                                              autoincrement=True),
                            sqlalchemy.Column('name', sqlalchemy.String(512), nullable=False),
                            sqlalchemy.Column('uniq_key', sqlalchemy.Unicode(36), nullable=False),
                            sqlalchemy.Column('finish_command', sqlalchemy.String(1024)), 
                            sqlalchemy.Column('type', sqlalchemy.Integer(1), nullable=False,
                                              default=JOBGROUP_TYPE['SERIAL']),
                            sqlalchemy.Column('status', sqlalchemy.Unicode(3), nullable=False,
                                              default=JOBGROUP_STATUS['PEND']),
                            sqlalchemy.Column('register', sqlalchemy.String(32), nullable=True),
                            sqlalchemy.Column('created', sqlalchemy.DateTime,
                                              default=now),
                            sqlalchemy.Column('modified', sqlalchemy.DateTime,
                                              default=now,
                                              onupdate=now),
                            )

#: Job Table instance.
def get_job_table(metadata, now):
    return sqlalchemy.Table('job', metadata,
                            sqlalchemy.Column('id', sqlalchemy.Integer, primary_key=True,
                                              autoincrement=True),
                            sqlalchemy.Column('jobgroup_id', sqlalchemy.Integer, 
                                              sqlalchemy.ForeignKey('jobgroup.id'),
                                              index=True, nullable=False),
                            sqlalchemy.Column('name', sqlalchemy.String(32), nullable=False),
                            sqlalchemy.Column('order', sqlalchemy.Integer, nullable=False),
                            sqlalchemy.Column('action_command', sqlalchemy.String(1024), nullable=False),
                            sqlalchemy.Column('rollback_command', sqlalchemy.String(1024)),
                            sqlalchemy.Column('status', sqlalchemy.Unicode(3), nullable=False,
                                              default=ACTION_STATUS['PEND']),
                            sqlalchemy.Column('action_exit_code', sqlalchemy.Integer),
                            sqlalchemy.Column('action_stdout', sqlalchemy.TEXT),
                            sqlalchemy.Column('action_stderr', sqlalchemy.TEXT),
                            sqlalchemy.Column('rollback_exit_code', sqlalchemy.Integer),
                            sqlalchemy.Column('rollback_stdout', sqlalchemy.TEXT),
                            sqlalchemy.Column('rollback_stderr', sqlalchemy.TEXT),
                            sqlalchemy.Column('progress', sqlalchemy.Integer, nullable=False, 
                                              default=0),
                            sqlalchemy.Column('created', sqlalchemy.DateTime, 
                                              default=now),
                            sqlalchemy.Column('modified', sqlalchemy.DateTime,
                                              default=now,
                                              onupdate=now),
                            )

def reload_mappers(metadata):
    """all model mapper reload.
    @param metadata: reload MetaData
    @type metadata: sqlalchemy.schema.MetaData
    """
    if metadata.bind.name == 'sqlite':
        _now = sqlalchemy.func.datetime('now', 'localtime')
    else:
        _now = sqlalchemy.func.now()

    t_jobgroup = get_jobgroup_table(metadata, _now)
    t_job = get_job_table(metadata, _now)
    try:
        mapper(JobGroup, t_jobgroup, properties={'jobs': relation(Job)})
        #mapper(JobGroup, t_jobgroup, properties={'jobs': relation(Job, backref='job_group')})
        mapper(Job, t_job)
    except sqlalchemy.exc.ArgumentError, ae:
        clear_mappers()
        mapper(JobGroup, t_jobgroup, properties={'jobs': relation(Job)})
        #mapper(JobGroup, t_jobgroup, properties={'jobs': relation(Job, backref='job_group')})
        mapper(Job, t_job)        
    
class Model(object):
    """Model base class of all.
    """
    def utf8(self, column):
        if hasattr(self, column):
            ret = getattr(self, column)
            if isinstance(ret, unicode):
                return ret.encode('utf-8')
            elif isinstance(ret, str):
                return ret
            else:
                return str(ret)
        else:
            return 'not found.' # TODO: raise
        
class JobGroup(Model):
    """JobGroup Table class.
    """

    def __init__(self, name, uniq_key, type=JOBGROUP_TYPE['SERIAL']):
        self.name = name
        self.uniq_key = uniq_key
        self.type = type

    def __repr__(self):
        return "JobGroup<'%s','%s'>" % (self.name, self.uniq_key)
        
class Job(Model):
    """Job Table class.
    """
    def __init__(self, name, order, action_command):
        self.name = name
        self.order = order
        self.action_command = action_command

    def __repr__(self):
        return "Job<'%s','%s','%s'>" % \
               (self.name, self.order, self.action_command)

    def is_rollback(self):
        return not is_empty(self.rollback_command)

if __name__ == '__main__':
    """Testing
    """
    import sqlalchemy.orm
    bind_name = 'sqlite:///:memory:'

    engine = sqlalchemy.create_engine(bind_name, encoding="utf8", convert_unicode=True)
    engine.echo = True
    metadata = sqlalchemy.MetaData(bind=engine)
    
    t_jg = get_jobgroup_table(metadata)
    t_job = get_job_table(metadata)
    
    sqlalchemy.orm.mapper(JobGroup, t_jg, 
                          properties={'jobs': sqlalchemy.orm.relation(Job)})
    sqlalchemy.orm.mapper(Job, t_job)
    
    metadata.drop_all()
    metadata.create_all()
    
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()

    # INSERT
    jg = JobGroup(u'All Update', '192.168.0.100')
    jg.jobs.append(Job(
        u'Yum Update MySQL',
        '0',
        '/usr/bin/yum update mysql'))
    jg.jobs.append(Job(
        u'Yum Update PostgreSQL',
        '1',
        '/usr/bin/yum update postgresql'))
    jg.jobs.append(Job(
        u'Yum Update httpd',
        '2',
        '/usr/bin/yum update httpd'))
    session.add(jg)
    jg1 = JobGroup(u'get date', '172.16.0.123')
    jg1.jobs.append(Job(u'get date','0', '/bin/date'))
    jg2 = JobGroup(u'get route', '172.16.0.123')
    jg2.jobs.append(Job(u'get route','0', '/sbin/route'))
    jg3 = JobGroup(u'get ping', '172.16.0.123')
    jg3.jobs.append(Job(u'get ping','0', '/bin/ping 172.16.0.1'))
    session.add_all([jg1,jg2,jg3])
    session.commit()

    # SELECT One
    jg = session.query(JobGroup).filter(JobGroup.name == u'All Update').one()
    print jg.__repr__()
    for jg in session.query(JobGroup).all():
        print jg.__repr__()

    # UPDATE
    jg = session.query(JobGroup).filter(JobGroup.name == u'All Update').one()
    jg.name = 'All Update - edit'
    for j in jg.jobs:
        j.name = 'All Update - edit'
    session.add(jg)
    session.commit()

    # DELETE + Manual CASCADE
    jgs = session.query(JobGroup).\
                  filter(JobGroup.name.in_([u'get date', \
                                           u'get route', \
                                           u'get ping'])).all()
    for jg in jgs:
        for j in jg.jobs:
            session.delete(j)
        session.delete(jg)
    session.commit()
