#!/usr/bin/env python

import SocketServer
from ESL import *
import json
from datetime import *
import xml.etree.ElementTree as xmlET
import logging
import vars
logging.basicConfig(level=vars.LOG_LEVEL, format='%(name)s: %(message)s', )

class FsReqBranches():
    def __init__(self):
        self.logger = logging.getLogger('FsReqBranches')
        self.logger.debug('__init__')
        return

    def show_channels_as_json(self): # calls_active/calls_active.php
        self.logger.debug('branch "calls_active"')
        if len(vars.rfs) == 0:
            return '{"row_count":0,"rows":[{"hostname":"ff10-110.secrom.com","created":"Freeswitch NOT AVAILABLE !"},{"hostname":"ff11-162.secrom.com","created":"Freeswitch NOT AVAILABLE !"}]}' + "\n\n"
        res=json.loads('{"row_count": 0, "rows":[]}')
        for x in vars.rfs:
            cur_dict = json.loads(x['resp'])
            if cur_dict['row_count']:
                for elem in cur_dict['rows']:
                    curt = datetime.utcnow()
                    curt = curt.replace(microsecond=0)
                    loadt = datetime.strptime(elem.get('created'),"%Y-%m-%d %H:%M:%S")
                    #self.logger.debug('created = "%s", loadt = "%s", curt = "%s" ', str(loadt), str(curt), elem.get('created'), )
                    elem['created'] = str(loadt.time()) + " UTC (" + str(curt - loadt) + " ago)"
                res['rows'].extend(cur_dict['rows'])
                res['row_count'] += cur_dict['row_count']
        return json.dumps(res)

    def sofia_xmlstatus_profile_internal_reg(self): ## registrations/status_registrations.php
        self.logger.debug('branch "status_registrations"')
        profile = xmlET.Element('profile')
        if len(vars.rfs):
            registrations = xmlET.Element('registrations')
            for x in vars.rfs:
                if x['resp'][0:6] == "<?xml ":
                    profile.extend(xmlET.fromstring(x['resp']))
            registrations.extend(profile.find("registrations"))    ## take only one registration (from one FS-node) because of shared memcache in my config
            for registration in registrations.iter("registration"):
                contact = registration[2]
                pos_ip = contact.text.find('@') + 1
                pos_port = contact.text.find(':', pos_ip) + 1
                contact_ip = contact.text[pos_ip:pos_port-1]
                contact_port = contact.text[pos_port:contact.text.find(';')]
                registration[8].text = contact_ip # network-ip
                registration[9].text = contact_port # network-port
            # than registrations will be sorted by phone on the status_registrations.php page
            profile = xmlET.Element('profile')
            profile.append(registrations)
        else:
            registrations = xmlET.SubElement(profile, 'registrations')
            for x in vars.fs:
                registration = xmlET.Element('registration')
                xmlET.SubElement(registration, 'status').text = 'Freeswitch NOT AVAILABLE !'
                xmlET.SubElement(registration, 'host').text = x['description']
                registrations.append(registration)

        return xmlET.tostring(profile, encoding="ISO-8859-1", method="xml") + "\n"

    def fifo_list(self):    ## sum
        self.logger.debug('branch "fifo_list"')
        root = xmlET.Element('fifo_report')
        for x in vars.rfs:
            if x['resp'][0:13] == "<fifo_report>":
                root.extend(xmlET.fromstring(x['resp']))
        return xmlET.tostring(root) + "\n"              ## CHECK in the real work!

    def fifo_list_(self):   ## first only
        self.logger.debug('branch "fifo_interactive"')
        for x in vars.rfs:
            if x['resp'][0:13] == "<fifo_report>":
                return x['resp']                        ## CHECK in the real work!

    def conference_xml_list(self):
        self.logger.debug('branch "conferences_active"')
        root = xmlET.Element('conferences')
        for x in vars.rfs:
            if x['resp'][0:6] == "<?xml ":
                t = xmlET.fromstring(x['resp'])
                for elem in t.findall("conference"):
                    elem.set('fs-node', x['description'])
                root.extend(t)
        return xmlET.tostring(root, encoding="ISO-8859-1", method="xml") + "\n"

    def conference__(self):
        self.logger.debug('branch "conferences_active"')
        root = xmlET.Element('conferences')
        for x in vars.rfs:
            if x['resp'][0:6] == "<?xml ":
                t = xmlET.fromstring(x['resp'])
                for elem in t.findall("conference"):
                    elem.set('fs-node', x['description'])
                root.extend(t)
        return xmlET.tostring(root, encoding="ISO-8859-1", method="xml") + "\n"

    def sofia_xmlstatus(self): # sip_status/sip_status.php
        self.logger.debug('branch "sip status"')
        root = xmlET.Element('profiles')
        t = xmlET.fromstring("<profile><name /><type /><data /><state /></profile>")
        for num,x in enumerate(vars.fs):
            t.find("name").text = "FS" + str(num)
            t.find("type").text = x['description']
            t.find("data").text = x['host']
            if x['state']:
                if x['resp'][0:6] == "<?xml ":
                    root.extend(xmlET.fromstring(x['resp']))
                    t.find("state").text = "RUNNING"
                else:
                    t.find("state").text = "RESTARTING"
            else:
                t.find("state").text = "NOT RUNNING"
            root.append(xmlET.fromstring(xmlET.tostring(t))) # copy element without linking(deepcopy)
        ## remove duplicates in <profile>
        udata = {}
        for elem in root.findall("profile"):
            key = elem.findtext("data")
            udata[key] = elem
            root.remove(elem)
        ## sort by <data>sips:mod_sofia@10.100.11.162:5067;transport=wss</data>
        sdata = []
        for elem in udata.values():
            key = elem.findtext("data")
            sdata.append((key, elem))
        sdata.sort()
        root.extend([item[-1] for item in sdata]) # insert the last item from each tuple
        ## remove duplicates in <gateway>
        udata = {}
        for elem in root.findall("gateway"):
            key = elem.findtext("data")
            udata[key] = elem
            root.remove(elem)
        ## sort by <data>sip:123@sip.nexmo.com</data>
        sdata = []
        for elem in udata.values():
            key = elem.findtext("data")
            sdata.append((key, elem))
        sdata.sort()
        root.extend([item[-1] for item in sdata]) # insert the last item from each tuple
        return xmlET.tostring(root, encoding="ISO-8859-1", method="xml") + "\n"

    def sofia_xmlstatus_profile_internal(self): # sip_status/sip_status.php 2 (SOFIA STATUS PROFILE INTERNAL)
        self.logger.debug('branch "SOFIA STATUS PROFILE INTERNAL"')
        root= xmlET.Element('profile')
        t   = xmlET.Element('profile-info')
        xmlET.SubElement(t, 'name').text = " " # make first string for non-xml responce
        sub_elements=[  'rtp-ip',     # list of changing sublelements
                        'ext-rtp-ip',
                        'sip-ip',
                        'calls-in',
                        'calls-out',
                        'failed-calls-in',
                        'failed-calls-out' 
                        ]
        for sub in sub_elements:
            xmlET.SubElement(t, sub).text = " "

        if len(vars.rfs):
            for num, x in enumerate(vars.rfs):
                if x['resp'][0:6] == "<?xml ":
                    root = xmlET.fromstring(x['resp'])
                    for sub in sub_elements:
                        t.find(sub).text += "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;FS" + str(num) + ": " + root.find('profile-info').findtext(sub, default =" ")
                        #self.logger.debug('sub = "%s" ', t.find(sub).text )
                else:
                    t.find("name").text = x['resp']
                    root.append(t)
            #self.logger.debug('root = "%s" ', xmlET.tostring(root) )
            for sub in sub_elements:
                root.find('profile-info').find(sub).text = t.findtext(sub)
            #self.logger.debug('t = "%s" ', xmlET.tostring(t) )
        else:
            t.find("name").text = "All FS-nodes NOT RUNNING"
            root.append(t)

        return xmlET.tostring(root, encoding="ISO-8859-1", method="xml") + "\n"

    def status(self): # sip_status/sip_status.php 3
        self.logger.debug('branch "sip uptime"')
        body_xml = ""
        for num,x in enumerate(vars.rfs):
            body_xml += "\nFS" + str(num) + ": " + x['description'] + "\n\n" + x['resp'] + "\n"
            #self.logger.debug('resp = "%s"', x.get('resp'))
        return body_xml

        
### EOF
