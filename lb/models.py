from django.db import models

import socket, struct

# Create your models here.
class Host(models.Model):
    hid = models.AutoField(primary_key=True) 
    ipv4 = models.CharField(max_length=17, null=True)
    mac = models.CharField(max_length=18, null=True)
    #
    fresh = models.BooleanField(default=True)

    def __unicode__(self,):
      return 'Host %d, ip: %s, mac: %s' % (self.hid, self.ipv4, self.mac,)

class LBVip(models.Model):
    vid = models.CharField(max_length=17, primary_key=True)
    name = models.CharField(max_length=20, null=True)
    protocol = models.CharField(max_length=10, null=True)
    address = models.CharField(max_length=17, null=True)
    port = models.CharField(max_length=10, null=True)
    #
    fresh = models.BooleanField(default=True)

    @property
    def naddress(self,):
        naddress = socket.inet_ntoa(struct.pack('I',socket.htonl(int(self.address))))
        return naddress
    
    @naddress.setter
    def naddress(self, address):
        self.address = socket.ntohl(struct.unpack("I",socket.inet_aton(str(address)))[0])
    
    def __unicode__(self,):
      return '[LBVIP %s: %s][%s:%s]' % (self.vid, self.name, self.naddress, self.port)


class LBPool(models.Model):
    pid = models.CharField(max_length=17, primary_key=True)
    name = models.CharField(max_length=20, null=True)
    protocol = models.CharField(max_length=10, null=True)
    vip = models.ForeignKey(LBVip)
    #
    fresh = models.BooleanField(default=True)
    
    
    def __unicode__(self,):
      return 'LBPool %s[%s]' % (self.pid, self.name,)


class LBMember(models.Model):
    mid = models.CharField(max_length=17, primary_key=True)
    address = models.CharField(max_length=17, null=True)
    naddress = models.CharField(max_length=17, null=True)
    port = models.CharField(max_length=10, null=True)
    pool = models.ForeignKey(LBPool)
    #server status
    req_count = models.IntegerField(default=0)
    kb_count = models.IntegerField(default=0)
    cpu_load = models.FloatField(default=0)
    uptime = models.IntegerField(default=0)
    req_per_sec = models.FloatField(default=0)
    byte_per_sec = models.FloatField(default=0)
    byte_per_req = models.FloatField(default=0)
    busy_workers = models.IntegerField(default=0)
    idle_workers = models.IntegerField(default=0)
    update_time = models.CharField(max_length=20, default='-1')
    #
    fresh = models.BooleanField(default=True)
    #
    flow_list = models.CharField(max_length=5217, null=True)
    
    @property
    def naddress(self,):
        naddress = socket.inet_ntoa(struct.pack('I',socket.htonl(int(self.address))))
        return naddress
    
    @naddress.setter
    def naddress(self, address):
        self.address = socket.ntohl(struct.unpack("I",socket.inet_aton(str(address)))[0])
    
    def __unicode__(self,):
      return 'LBMember %s[%s:%s]' % (self.mid, self.naddress, self.port)

    def set_flow_list(self,):
        flow_list = self.lbflow_set.all()
        tmp_flow_list = '['
        first = True
        for flow in flow_list:
          if not first:
            tmp_flow_list += ','
          f = '{"fid":"%s","packet_count":"%s","duraction":"%s"}' % (flow.fid, flow.packet_count, flow.duraction)
          tmp_flow_list += f
          first = False
        tmp_flow_list += "]"
        #print 'flow_list:', tmp_flow_list
        self.flow_list = tmp_flow_list

class LBFlow(models.Model):
    fid = models.CharField(max_length=217, primary_key=True)
    weight = models.FloatField(default=1.0)
    #member = models.CharField(max_length=17)
    member = models.ForeignKey(LBMember)

    @property
    def inbound_entry_list(self,):
        #print 'len(entry):', len(self.lbflowentry_set.all())
        return [ entry for entry in self.lbflowentry_set.all() if entry.eid.find('inbound') >= 0]

    @property
    def outbound_entry_list(self,):
        #print 'len(entry):', len(self.lbflowentry_set.all())
        return [ entry for entry in self.lbflowentry_set.all() if entry.eid.find('outbound') >= 0]

    @property
    def packet_count(self,):
        return self.outbound_entry_list[0].packet_count

    @property
    def duraction(self,):
        return self.outbound_entry_list[0].duraction

    def get_mid(self,):
        inbound_list = self.inbound_entry_list
        for entry in inbound_list:
            info1 = eval(entry.info1)
            if 'instructions' not in info1:
                continue
            inst = info1['instructions']
            if 'instruction_apply_actions' not in inst:
                continue
            actions = inst['instruction_apply_actions']
            if 'ipv4_dst' not in actions:
                continue
            return actions['ipv4_dst']
        return None

    def get_network_id(self,):
        return self.fid.split(';')[-1].split('~')[-1].split('.')[0]
            

class LBFlowEntry(models.Model):
    '''
    info1: {u'outPort': u'any', u'outGroup': u'any', u'idleTimeoutSec': u'0', u'flags': u'1', 
    u'priority': u'-32768', u'cookieMask': u'0', u'version': u'OF_13', 
    u'cookie': u'45036000170862220', u'hardTimeoutSec': u'0', u'command': u'ADD',
    u'match': {u'ip_proto': u'6', u'eth_type': u'0x800', u'ipv4_dst': u'10.0.0.100', u'in_port': u'1'},
    u'instructions': {u'instruction_apply_actions': {u'eth_src': u'12:34:56:78:90:12', 
    u'tcp_src': u'80', u'ipv4_src': u'10.0.0.200', u'output': u'2'}}}
    '''
    eid = models.CharField(max_length=217, primary_key=True)
    info1 = models.CharField(max_length=1117, null=True)
    info2 = models.CharField(max_length=1117, null=True)
    flow = models.ForeignKey(LBFlow)
    
    def __unicode__(self,):
        return 'entry: %s' % (self.eid,)

    @property
    def pinswmatch(self,):
        pinsw = self.eid.split(';')[-1].split('~')[-1]
        #print 'self.info1:', self.info1, type(self.info1)
        #info1 = dict("{'a':'a'}")
        info1 = eval(self.info1)
        if 'match' not in info1:
            return None
        match = info1['match']
        if 'ipv4_src' in match:
            return 'pinsw~%s;ipv4_src~%s' % (pinsw, match['ipv4_src'])
           
        if 'ipv4_dst' in match:
            return 'pinsw~%s;ipv4_dst~%s' % (pinsw, match['ipv4_dst'])
        #print info1
        return None
    
    @property
    def packet_count(self,):
      '''
      info2 = {u'priority': u'32768', u'idleTimeoutSec': u'0', u'flags': u'1', u'durationSeconds': u'9785',
      u'byteCount': u'488', u'version': u'OF_13', u'tableId': u'0x0', u'packetCount': u'6', 
      u'hardTimeoutSec': u'0', u'cookie': u'45035997133399063', 
      u'match': {u'ip_proto': u'6', u'eth_type': u'0x800', u'ipv4_src': u'10.0.0.100', u'in_port': u'1'}, 
      u'instructions': {u'instruction_apply_actions': {u'output': u'2'}}}
      '''
      #print 'self.info2:', self.info2 , type(self.info2)
      info2 = eval(self.info2)
      return info2['packetCount']
    
    @property
    def duraction(self,):
      info2 = eval(self.info2)
      return info2['durationSeconds']

    #eid: inbound-vip~1;client~10.0.0.100;srcsw~00:00:d2:c8:68:8a:2d:47;pinsw~00:00:d2:c8:68:8a:2d:47
    #fid = vip + client
    def get_fid(self,):
        fid = self.eid.split(';')
        fid = 'vip~%s;client~%s' % (fid[0].split('~')[-1], fid[1].split('~')[-1])
        return fid

