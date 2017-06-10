#!/usr/bin/env python

import thread
import MySQLdb
from ESL import *
import logging
import vars
logging.basicConfig(level=vars.LOG_LEVEL, format='%(name)s: %(message)s', )

## Base class
class Dispatcher():
    default = { 'fp': 0,
                'host': "",
                'port': "",
                'user': "",
                'password': "",
                'description': "",
                'state': 1 }
    list = []
    mysql_opensips = {  'host': "localhost",
                        'port': 3306,
                        'user': "opensips",
                        'passwd': "opensipsrw",
                        'db': "opensips" }

    def __init__(self):
        self.logger = logging.getLogger('Dispatcher')
        self.logger.debug('__init__')
        return
 
    def getself(self):
        self.logger.debug('getself')
        return self

    def new_write(self, host, description):
        self.logger.debug('getself')
        t = {   'fp': 0,
                'host': host,
                'port': self.default.get('port'),
                'user': self.default.get('user'),
                'password': self.default.get('password'),
                'description': description,
                'state': self.default.get('state') }
        return t
        
    def init_from_list(self, fs_host_list):
        self.logger.debug('init_fs_from_list')
        self.logger.debug('clear list')
        self.list[:] = []
        for x in fs_host_list:
            self.list.append(self.new_write(x,''))
        self.logger.debug('list = "%s"', self.list)
        return

    def init_from_mysql_opensips(self):
        self.logger.debug('init_from_mysql_opensips')
        self.list[:] = [] # list.clear is only in Python 3
        for x in self.req_sql("SELECT * FROM `dispatcher` LIMIT 50"): ## x[2] = host, x[8] = description
            self.logger.debug('row = "%s"', x)
            sip_address = x[2]
            pos_ip = sip_address.find(':') + 1
            pos_port = sip_address.find(':', pos_ip)
            sip_host = sip_address[pos_ip:pos_port]
            self.list.append(self.new_write(sip_host, x[8])) 
        self.logger.debug('list = "%s"', self.list)
        return self.list

    def req_sql(self, sql_cmd):
        self.logger.debug('req_sql, sql_cmd = "%s" ', sql_cmd)
        try:
            db = MySQLdb.connect(   host =  self.mysql_opensips.get('host'),
                            port =  self.mysql_opensips.get('port'),
                            user =  self.mysql_opensips.get('user'),
                            passwd= self.mysql_opensips.get('passwd'),
                            db =    self.mysql_opensips.get('db') )
            cur = db.cursor()
            cur.execute(sql_cmd)
            res = cur.fetchall()
            db.commit() # Commit your changes in the database
        except MySQLdb.Error, e:
            self.logger.debug('Error %d: "%s"', e.args[0], e.args[1])
            #self.logger.debug('SQL execution error! Rollback operation')
            #db.rollback() # Rollback in case there is any error
        db.close()
        self.logger.debug('res = "%s"', res)
        return res

    def list_connect(self):
        self.logger.debug('list_connect')
        for x in self.list:
            self.logger.debug('start_new_thread for connect to %s', x.get('host'))
            thread.start_new_thread(self.connect, (x,)) # 2nd arg must be a tuple
        return self.list

    def connect(self, x):
        self.logger.debug('connect')
        return

## EOF
