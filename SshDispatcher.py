#!/usr/bin/env python
# -*- coding: utf-8 -*-

import paramiko
from Dispatcher import *
import logging
import vars
logging.basicConfig(level=vars.LOG_LEVEL, format='%(name)s: %(message)s', )

class SshDispatcher(Dispatcher):
    default = { 'fp': 0,
                'host': "",
                'port': 22,         ## paramiko: port (int) – the server port to connect to
                'user': "centos",
                'password': "",
                'description': "",
                'state': 1 }
    cert = ""                       ## paramiko: key_filename (str) – the filename, or list of filenames, of optional private key(s) to try for authentication
    def __init__(self):
        self.logger = logging.getLogger('EslSSH')
        self.logger.debug('__init__')
        return

    def connect(self, x):
        self.logger.debug('connect (skip)')
        return

    def cmd_to_fs(self, ssh_cmd): # 'sudo service freeswitch restart'
        self.logger.debug('cmd_to_fs')
        try:
            self.logger.debug('cmd "%s" to "%s"', ssh_cmd, x.get('host'))
            x.get('fp').exec_command(ssh_cmd) # run command
            return 1
        except paramiko.SSHException:
            self.logger.debug('SSH cmd error for "%s"', x.get('host'))  
            return 0
        return

    def cmd_to_host(self, ssh_cmd, host, port=default.get('port')): # 'sudo service freeswitch restart'
        self.logger.debug('cmd_to_opensips')
        self.logger.debug('connect to "%s:%s", user = "%s", password "%s", path to cert = "%s"',
                            host,
                            port,
                            self.default.get('user'),
                            self.default.get('password'),
                            self.cert
                            )
        try:
            sshcon = paramiko.SSHClient()  # will create the object
            sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # no known_hosts error

            sshcon.connect( hostname =      host,
                            port =          port,
                            username =      self.default.get('user'),
                            key_filename =  self.cert
                            ) # no passwd needed
            channel = sshcon.get_transport().open_session()
            channel.get_pty()
            channel.settimeout(2)
            channel.exec_command(ssh_cmd)
            #res = channel.recv_exit_status()
            self.logger.debug('ssh host %s on cmd "%s"', host, ssh_cmd)
        except paramiko.SSHException:
            self.logger.debug('SSH cmd error for "%s"', host)  
            return 0
        return 1

    def cmd_to_cluster(self, ssh_cmd): # 'sudo service freeswitch restart'
        self.logger.debug('cmd_to_cluster')
        for x in vars.ssh:
            self.logger.debug('connect to "%s:%s", user = "%s", password "%s", path to cert = "%s"',
                                x.get('host'),
                                x.get('port'),
                                x.get('user'),
                                x.get('password'),
                                self.cert
                                )
            try:
                sshcon = paramiko.SSHClient()  # will create the object
                sshcon.set_missing_host_key_policy(paramiko.AutoAddPolicy()) # no known_hosts error

                sshcon.connect( hostname =      x.get('host'),
                                port =          x.get('port'),
                                username =      x.get('user'),
                                key_filename =  self.cert
                                ) # no passwd needed
                #channel = x.get('fp').get_transport().open_session()
                channel = sshcon.get_transport().open_session()
                channel.get_pty()
                channel.settimeout(2)
                channel.exec_command(ssh_cmd)
                #res = channel.recv_exit_status()
                #self.logger.debug('ssh host %s on cmd "%s" responce as "%s"', x.get('host'), ssh_cmd, res) ## restart in app/sip_status/sip_status.php
                self.logger.debug('ssh host %s on cmd "%s"', x.get('host'), ssh_cmd) ## restart in app/sip_status/sip_status.php
            except paramiko.SSHException:
                self.logger.debug('SSH cmd error for "%s"', x.get('host'))  
                return 0
        return 1

### EOF

