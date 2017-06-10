#!/usr/bin/env python

import SocketServer
from ESL import *
import json
import xml.etree.ElementTree as xmlET
import paramiko

from EslDispatcher import *
from SshDispatcher import *
from FsReqBranches import *
import vars

import logging
logging.basicConfig(level=vars.LOG_LEVEL, format='%(name)s: %(message)s', )

class EslHandler(SocketServer.BaseRequestHandler, FsReqBranches):
    client_ip = ''
    def __init__(self, request, client_address, server):
        self.logger = logging.getLogger('EslHandler')
        self.client_ip = client_address[0]
        #self.logger.debug('__init__')
        SocketServer.BaseRequestHandler.__init__(self, request, client_address, server)
        return
    def setup(self):
        self.logger.debug('setup (client_address = "%s"), get auth from client', self.client_address)
        
        data = "Content-Type: auth/request\n\n"
        self.request.send(data)
        data = self.request.recv(1024)
        self.logger.debug('recieved data = "%s"', data)
        data = "Content-Type: command/reply\nReply-Text: +OK accepted\n\n"
        self.request.send(data)

        return SocketServer.BaseRequestHandler.setup(self)

    def handle(self):
        self.logger.debug('handle')

        ## set timeout here so timeout in SocketServer.TCPServer is not working
        ## because of serve_forever() run every 0.5 sec and not look at it!
        self.request.settimeout(3) # seconds
        data = self.request.recv(1024)
        self.logger.debug('receive from Fusion data = "%s"', data)

        ## read whole command from Fusion, it has \n\n at the end
        data_next=""        
        if data and data[-2:] != "\n\n":
            data_next = self.request.recv(1024)
            self.logger.debug('receive from Fusion data_next = "%s"', data_next)          
            data = data + data_next
        
        while data and data_next and data[-2:] != "\n\n":
            data_next = self.request.recv(1024)
            self.logger.debug('receive from Fusion data_next2 = "%s"', data_next)
            data = data + data_next

        ## process requests while there is data
        while data:
            fs_req = data # store request from Fusion to FS in fs_req
            if fs_req[0:26] == "restart freeswitch cluster":
                self.logger.debug('restart freeswitch cluster')
                ssh_cmd='sudo service freeswitch restart'
                vars.p.get('ssh').cmd_to_cluster(ssh_cmd)
                body_xml = "OK+\n\n"
                data_set = 1 # data = result1.serialize() for default
            elif fs_req[0:16] == "restart opensips":
                self.logger.debug('restart opensips')
                ssh_cmd='sudo /usr/local/sbin/opensipsctl restart'
                vars.p.get('ssh').cmd_to_host(ssh_cmd, '10.100.1.85', 64016, 'ec2-user')
                body_xml = "OK+\n\n"
                data_set = 1 # data = result1.serialize() for default
            elif fs_req[0:6] == "new fs":
                self.logger.debug('new fs "%s" ', self.client_ip) ## restart in app/sip_status/sip_status.php
                #newfs = fs_req[7:fs_req.find("\n")]
                #newfs = fs_req[7:]
                newfs = self.client_ip
                self.logger.debug('newfs = "%s"', newfs)
                is_here = 0;
                for x in vars.fs:
                    if x['host'] == newfs:
                        is_here = 1;
                ## (`id`, `setid`, `destination`, `socket`, `state`, `weight`, `priority`, `attrs`, `description`)
                if is_here:
                    self.logger.debug('this fs is already in list - do update dispatcher')
                    sql_cmd = "UPDATE dispatcher SET state=0 WHERE destination='sip:" + newfs + ":5061';"
                    res = vars.p.get('esl').req_sql(sql_cmd)               
                    self.logger.debug('res = "%s"', res)
                else:
                    self.logger.debug('new fs - add new write to dispatcher')
                    newfs_desc = "ff" + newfs.split(".")[2] + "-" + newfs.split(".")[3] # like ff11-102
                    vars.fs.append(vars.p.get('esl').new_write(newfs, newfs_desc))
                self.request.send("bash responce " + str(is_here) + "\n\n") # send responce to bash-script
                self.logger.debug('new fs -> handle end')
                return
            else:
                if vars.p.get('esl').cmd_to_cluster(fs_req): ## Send fs_req to FS cluster
                    data_set = 0 # data = result1.serialize() by default
                    data = vars.rfs[0].get('result').serialize()
                else: # fs_sum = 0
                    body_xml = "\n\n" #zero answer if no working FS-nodes
                    data_set = 1
                    #fs_req = "skip branches"
                    

            if fs_req[0:24] == "api conference xml_list\n":
                body_xml = self.conference_xml_list() ## /app/conferences_active/conference_interactive.php
                data_set = 1

            if fs_req[0:16] == "api conference '":
                body_xml = self.conference__() ## fs_req "api conference '3689fc1f-e367-4f88-80cb-384357a7715b-sp.secrom.com' xml_list
                data_set = 1
            
                            
            elif fs_req[0:41] == "api sofia xmlstatus profile internal reg\n":
                body_xml = self.sofia_xmlstatus_profile_internal_reg() ## app/registrations/status_registrations.php
                data_set = 1

            elif fs_req[0:37] == "api sofia xmlstatus profile internal\n":
                body_xml = self.sofia_xmlstatus_profile_internal()    ## app/sip_status/sip_status.php
                data_set = 1
            
            elif fs_req[0:20] == "api sofia xmlstatus\n":
                body_xml = self.sofia_xmlstatus() ## app/sip_status/sip_status.php
                data_set = 1
            
            elif fs_req[0:11] == "api status\n":    ## app/sip_status/sip_status.php
                body_xml = self.status()          ## UP 0 years, 1 day, 10 hours, 54 minutes, 46 seconds, 819 milliseconds, 550 microseconds
                data_set = 1                        ## FreeSWITCH (Version 1.8.0 git b8c65fb 2016-09-28 22:10:47Z 64bit) is ready        
                
            elif fs_req[0:26] == "api show channels as json\n":
                body_xml = self.show_channels_as_json() ## calls_active/calls_active.php
                data_set = 1
                
            elif fs_req[0:14] == "api fifo list\n" or fs_req[0:21] == "api fifo list_verbose":
                body_xml = self.fifo_list() ## app/fifo_list/fifo_list.php (sum)
                data_set = 1                ## app/fifo_list/fifo_interactive.php


                
                
                
                
                
            if data_set:
                data = "Event-Name: SOCKET_DATA\nContent-Type: api/response\nContent-Length: " + str(len(body_xml)) + "\n\n" + body_xml
                  
            self.logger.debug('send to Fusion data "%s"', data)
            self.request.send(data)
        
            data = self.request.recv(1024)
            self.logger.debug('receive from Fusion "%s"', data)
            
            data_next=""
            if data and data[-2:] != "\n\n":
                data_next = self.request.recv(1024)
                self.logger.debug('receive from Fusion data_next = "%s"', data_next)          
                data = data + data_next
            
            while data and data_next and data[-2:] != "\n\n":
                data_next = self.request.recv(1024)
                self.logger.debug('receive from Fusion data3 = "%s"', data_next)
                data = data + data_next
        
        self.logger.debug('handle end')
        return

    def finish(self):
        #self.logger.debug('finish')
        return SocketServer.BaseRequestHandler.finish(self)

### EOF

