#!/usr/bin/env python

import thread
from EslDispatcher import *
from SshDispatcher import *
from EslSocketServer import *
from EslHandler import *
import vars
        
ff = EslDispatcher()
vars.p['esl'] = ff.getself()
## for init_fs_from_list variant
#fs_host_list = ["10.100.10.110",
#                "10.100.11.162"]
#t.init_fs_list(fs_host_list)

## for init_fs_from_mysql
opensips = {    'host': "10.100.20.148",
                'port': 3306,
                'user': "opensips",
                'passwd': "opensipsrw",
                'db': "opensips" }
ff.mysql_opensips = opensips
ff.init_from_mysql_opensips()
vars.fs.extend(ff.list_connect()) ## use "extend" because of "=", "copy.copy()", "list[:]" and "list(list)" do not just copy but use symlinks!
## or use import copy
## vars.fs = copy.deepcopy(ff.list_connect())
## vars.ssh = copy.deepcopy(ss.list_connect())

thread.start_new_thread(ff.reconnecter, ())

ss = SshDispatcher()
vars.p['ssh'] = ss.getself()
ss.cert = "/root/certs/sec16all.pem"
ss.mysql_opensips = opensips
ss.init_from_mysql_opensips()
vars.ssh.extend(ss.list_connect())

server = EslSocketServer(('', 8026), EslHandler)

try:
        server.serve_forever()
except KeyboardInterrupt:
        pass
server.server_close()