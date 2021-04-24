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
import sqlalchemy.orm
from pysilhouette.db import dbsave, dbupdate, dbdelete
from  pysilhouette.db.model import JobGroup, Job, JOBGROUP_STATUS

# JobGroup Table
def jobgroup_findbyall(session, desc=False):
    if desc is True:
        return session.query(JobGroup).order_by(JobGroup.id.desc()).all()
    else:
        return session.query(JobGroup).order_by(JobGroup.id.asc()).all()

def jobgroup_findbyall_limit(session, limit, desc=False):
    if desc is True:
        return session.query(JobGroup).order_by(JobGroup.modified.desc()).all()[:limit]
    else:
        return session.query(JobGroup).order_by(JobGroup.modified.asc()).all()[:limit]

def jobgroup_findbystatus(session, status=JOBGROUP_STATUS['PEND']):
    return session.query(JobGroup).filter(
        JobGroup.status == status).order_by(JobGroup.id.asc()).all()

def jobgroup_findbytype_status(session, type, status=JOBGROUP_STATUS['PEND']):
    return session.query(JobGroup).filter(
        JobGroup.type == type).filter(
        JobGroup.status == status).order_by(JobGroup.id.asc()).all()

def jobgroup_findbytype_limit_status(session, type, limit, status=JOBGROUP_STATUS['PEND']):
    return session.query(JobGroup).filter(
        JobGroup.type == type).filter(
        JobGroup.status == status).order_by(JobGroup.id.asc()).limit(limit).all()

def jobgroup_findbyuniqkey(session, uniq_key):
    if uniq_key:
        return session.query(JobGroup).filter(
            JobGroup.uniq_key == uniq_key).all()
    else:
        return None

def jobgroup_findbyid(session, jgid, uniq_key):
    try:
        return session.query(JobGroup).filter(
            JobGroup.id == jgid).filter(JobGroup.uniq_key == uniq_key).one()
    except sqlalchemy.orm.exc.NoResultFound as nrf:
        return None


def jobgroup_update(session, m_jg, status, autocommit=True):
    m_jg.status = status
    ret = update(session, m_jg)
    if autocommit is True:
        session.commit()
    return ret

# Edit
@dbsave
def save(session, model):
    return session.add(model)

@dbupdate
def update(session, model):
    return session.add(model)

@dbdelete
def delete(session, model):
    return session.delete(model)


# Job Table
def job_findbyjobgroup_id(session, jgid, desc=False):
    _q = session.query(Job).filter(Job.jobgroup_id == jgid)
    if desc:
        _r = _q.order_by(Job.order.desc()).all()
    else:
        _r = _q.order_by(Job.order.asc()).all()
    return _r

def job_update(session, m_job, status=None, autocommit=True):
    if not status is None:
        m_job.status = status
        
    ret = update(session, m_job)
        
    if autocommit is True:
        session.commit()
    return ret

def job_result_action(session, job, info, autocommit=True):
    job.action_exit_code = info['r_code']
    job.action_stdout = info['stdout']
    job.action_stderr = info['stderr']

    ret = job_update(session, job)
        
    if autocommit is True:
        session.commit()

    return ret

def job_result_rollback(session, job, info, autocommit=True):
    job.rollback_exit_code = info['r_code']
    job.rollback_stdout = info['stdout']
    job.rollback_stderr = info['stderr']

    ret = job_update(session, job)

    if autocommit is True:
        session.commit()

    return ret

# progress
def get_progress(session, job_id):
    job = session.query(Job).filter(Job.id == job_id).one()
    return job.progress

def up_progress(session, job_id, up):
    job = session.query(Job).filter(Job.id == job_id).one()
    job.progress += up
    if 100 < job.progress:
        job.progress = 100
    
    job_update(session, job)
    
if __name__ == '__main__':
    pass
