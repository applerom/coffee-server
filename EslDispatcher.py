#!/usr/bin/env python

import MySQLdb
from ESL import *
from Dispatcher import *
import time
import logging
import vars
logging.basicConfig(level=vars.LOG_LEVEL, format='%(name)s: %(message)s', )

class EslDispatcher(Dispatcher):
    default = { 'fp': 0,
                'host': "",
                'port': "8021",
                'user': "",
                'password': "ClueCon",
                'description': "",
                'state': 1 }

    def __init__(self):
        self.logger = logging.getLogger('EslDispatcher')
        self.logger.debug('__init__')
        return

    def connect(self, x):
        self.logger.debug('connect to "%s:%s", password "%s"', x.get('host'), x.get('port'), x.get('password'))
        fs_cur = ESLconnection(x.get('host'), x.get('port'), x.get('password'))
        if fs_cur.connected():
            x['fp'] = fs_cur
            self.logger.debug('connected to "%s", fp="%s"', x.get('description'), fs_cur)
        else:
            self.logger.debug('cannot connect to "%s"!', x.get('host'))
            #self.finish()
        return

    def reconnecter(self):
        self.logger.debug('reconnecter')
        while 1:
            for x in vars.fs:
                if x['state'] == 0:
                    try:
                        self.logger.debug('try reconnect to "%s:%s", password "%s"', x.get('host'), x.get('port'), x.get('password'))
                        fs_cur = ESLconnection(x.get('host'), x.get('port'), x.get('password'))
                        if fs_cur.connected():
                            x['fp'] = fs_cur
                            x['state'] = 1
                            self.logger.debug('reconnected to "%s", fp="%s"', x.get('description'), fs_cur)
                        else:
                            self.logger.debug('still cannot connect to "%s"!', x.get('host'))
                            time.sleep(15)
                    except:
                        #self.logger.debug('error in transition with esl')
                        self.logger.debug('error in reconnection to "%s"', x.get('host'))
                        time.sleep(30)
        return

    def cmd_to_cluster(self, fs_req):
        vars.rfs[:] = []
        for x in vars.fs:
            #self.logger.debug('fp = "%s", send to %s "%s" fs_req "%s"', x.get('fp'), x.get('description'), x.get('host'), fs_req)
            if x.get('state'):
                try:
                    x['result'] = x.get('fp').sendRecv(fs_req) # send fs_req to FS
                    x['resp'] = x.get('result').getBody()
                    vars.rfs.append(x)
                    self.logger.debug('resp = "%s"', x.get('resp'))
                except:
                    #self.logger.debug('error in transition with esl')
                    self.logger.debug('error in transition with "%s"', x.get('host'))
                    x['state'] = 0
        return len(vars.rfs)
