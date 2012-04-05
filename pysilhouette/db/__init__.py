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

from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, mapper, \
     clear_mappers, relation, scoped_session
from sqlalchemy.orm.exc import UnmappedInstanceError
from sqlalchemy.pool import SingletonThreadPool, QueuePool

from pysilhouette.db.model import reload_mappers
from pysilhouette import SilhouetteException


from sqlalchemy.orm import sessionmaker, mapper, SessionExtension, scoped_session

class SilhouetteDBException(SilhouetteException):
    """Database running error.
    """
    pass

def create_database(cf):
    db = None
    if cf['database.url'][:6].strip() == 'sqlite':
        db = Database(cf['database.url'],
                      encoding="utf-8",
                      convert_unicode=True,
                      )
    else:
        if cf['database.pool.status'] == 1:
            db = Database(cf['database.url'],
                          encoding="utf-8",
                          convert_unicode=True,
                          poolclass=QueuePool,
                          pool_size=cf['database.pool.size'],
                          max_overflow=cf['database.pool.max.overflow'],
                          )
        else:
            db = Database(cf['database.url'],
                          encoding="utf-8",
                          convert_unicode=True,
                          poolclass=SingletonThreadPool,
                          pool_size=cf['database.pool.size'],
                          )
    if db is None:
        raise SilhouetteDBException('Initializing a database error - "Database" failed to create.')
    reload_mappers(db.get_metadata())
    return db

class Database:
    """TODO
    """
    
    __engine = None
    __metadata = None
    __Session = None

    def __init__(self, *args, **kwargs):
        self.get_engine(*args, **kwargs)
        self.create_metadata(self.__engine)

    def get_engine(self, *args, **kwargs):
        if not self.__engine:
            self.__engine = create_engine(*args, **kwargs)
        return self.__engine

    def create_metadata(self, bind=None, reflect=False):
        return MetaData(bind,reflect)

    def get_metadata(self):
        if not self.__metadata:
            self.__metadata = self.create_metadata(self.__engine)
        return self.__metadata

    def get_session(self):
        #if self.__Session is None:
        #    self.__Session = sessionmaker(bind=self.__engine)
        #return self.__Session()
        return scoped_session(
            sessionmaker(bind=self.__engine, autoflush=True))



def dbsave(func):
    """
    # TODO Comment
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('pysilhouette.db')
        session = args[0]
        model = args[1]
        model_name = repr(model).split("<")[0]
        model_id = model.id
        try:
            func(*args, **kwargs)
        except UnmappedInstanceError, ui:
            logger.error(('Data to insert is failed, '
                          'Invalid value was inputed. '
                          '- %s=%s, error=%s') % (model_name, model_id, str(ui.args)))
            raise SilhouetteDBException(('Data to insert is failed, '
                          'Invalid value was inputed. '
                          '- %s=%s, error=%s') % (model_name, model_id, str(ui.args)))

        num = len(session.new)
        if not num:
            logger.warn('Data has not been changed. - %s=%s' %  (model_name, model_id))
            return num  # The return value assume zero
        
        logger.debug('Data to insert is succeeded. - %s=%s' % (model_name, model_id))
        return num
    
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

def dbupdate(func):
    """
    # TODO Comment
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('pysilhouette.db')
        session = args[0]
        model = args[1]
        model_name = repr(model).split("<")[-1]
        model_id = model.id
        try:
            func(*args, **kwargs)
        except UnmappedInstanceError, ui:
            logger.error(('Data to update is failed, '
                          'Invalid value was inputed '
                          '- %s=%s, error=%s') % (model_name, model_id, str(ui.args)))
            raise SilhouetteDBException(('Data to update is failed, '
                          'Invalid value was inputed. '
                          '- %s=%s, error=%s') % (model_name, model_id, str(ui.args)))
        
        num = len(session.dirty)
        if not num:
            logger.warn('Data has not been changed. - %s=%s' %  (model_name, model_id))
            return num  # The return value assume zero
        
        logger.debug('Data to update is succeeded. - %s=%s' % (model_name, model_id))
        return num
    
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper

def dbdelete(func):
    """
    # TODO Comment
    """
    def wrapper(*args, **kwargs):
        logger = logging.getLogger('pysilhouette.db')
        session = args[0]
        model = args[1]
        model_name = repr(model).split("<")[0]
        model_id = model.id
        try:
            func(*args, **kwargs)
        except UnmappedInstanceError, ui:
            logger.error(('Data to delete is failed, '
                          'Invalid value was inputed '
                          '- %s=%s, error=%s') % (model_name, model_id, str(ui.args)))
            raise SilhouetteDBException(('Data to delete is failed, '
                          'Invalid value was inputed. '
                          '- %s=%s, error=%s') % (model_name, model_id, str(ui.args)))

        num = len(session.deleted)
        if not num:
            logger.warn('Data has not been changed. - %s=%s' %  (model_name, model_id))
            return num  # The return value assume zero
        
        logger.debug('Data to delete is succeeded. - %s=%s' % (model_name, model_id))
        return num
    
    wrapper.__name__ = func.__name__
    wrapper.__dict__ = func.__dict__
    wrapper.__doc__ = func.__doc__
    return wrapper


if __name__ == '__main__':
    pass
