#!/usr/bin/env python

import MySQLdb
import boto3
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
                'state': 0 }

    def __init__(self):
        self.logger = logging.getLogger('EslDispatcher')
        self.logger.debug('__init__')
        return

    def connect(self, x):
        self.logger.debug('connect to "%s:%s", password "%s"', x.get('host'), x.get('port'), x.get('password'))
        fs_cur = ESLconnection(x.get('host'), x.get('port'), x.get('password'))
        if fs_cur.connected():
            x['fp'] = fs_cur
            x['state'] = 1
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
                            # check if new fs present in opensips dispatcher
                            present = 0
                            for xx in self.req_sql("SELECT * FROM `dispatcher` LIMIT 50"): ## x[2] = host, x[8] = description
                                self.logger.debug('row = "%s"', xx)
                                self.logger.debug('xx[2].split(":")[1] = "%s" host = "%s"', xx[2].split(":")[1], x.get('host'))
                                if xx[2].split(":")[1] == x.get('host'):
                                    present = 1
                            if not present:
                                # new fs
                                self.logger.debug('add new fs to opensips "%s", fp="%s"', x.get('description'), fs_cur)
                                ## change to use opensipsctl
                                ## sql_cmd = "INSERT INTO dispatcher VALUES (0, 1, 'sip:" + newfs + ":5061', '', 2, 50, 0, 'C0', '" + newfs_desc + "');"
                                ## self.request.send(sql_cmd)
                                ssh_cmd = "sudo opensipsctl dispatcher addgw 1 sip:" + x.get('host') + ":5061 '' 0 50 'auto' '" + x.get('description') + "'"
                                vars.p.get('ssh').cmd_to_host(ssh_cmd, '10.100.1.85', 22, 'ec2-user')
                                ssh_cmd = "sudo opensipsctl dispatcher reload"
                                vars.p.get('ssh').cmd_to_host(ssh_cmd, '10.100.1.85', 22, 'ec2-user')
                            
                            self.logger.debug('reconnected to "%s", fp="%s"', x.get('description'), fs_cur)
                        else:
                            self.logger.debug('still cannot connect to "%s"!', x.get('host'))
                            ec2 = boto3.client('ec2', region_name='us-east-1')
                            filters = [{ 'Name': 'private-ip-address', 'Values': [x.get('host')] }]
                            resp = ec2.describe_instances(Filters=filters)
                            if len(resp.get('Reservations')):
                                self.logger.debug('fs did not answer but instance exists, its state is "%s"', resp.get('Reservations')[0].get('Instances')[0].get('State').get('Name'))
                            else:
                                self.logger.debug('instance with IP %s does not exist! Remove it from Opensips DB.', x.get('host'))
                                sql_cmd = "DELETE FROM dispatcher WHERE destination='sip:" + x.get('host') + ":5061';"
                                self.req_sql(sql_cmd)
                                ssh_cmd = "sudo opensipsctl dispatcher reload"
                                vars.p.get('ssh').cmd_to_host(ssh_cmd, '10.100.1.85', 22, 'ec2-user')
                                vars.fs.remove(x)
                            time.sleep(15)
                    except:
                        #self.logger.debug('error in transition with esl')
                        self.logger.debug('error in reconnection to "%s"', x.get('host'))
                        time.sleep(30)
        return

    def cmd_to_cluster(self, fs_req):
        self.logger.debug('cmd_to_cluster')
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

## EOF

