#encoding=utf-8
import json
import httplib, urllib
from models import *
from tool import *
from django.core.exceptions import ObjectDoesNotExist
CONTROLLER_HOST = '127.0.0.1:8080'

host_dict = {}
vip_dict = {}
pool_dict = {}
member_dict = {}
entry_dict = {}
flow_dict = {}

#@log
def sendhttp(host, url='/', data=None, method='GET', headers=None):
    if method == 'PUT' or method == 'POST':
        #headers = { 'Content-type':'application/javascript', 'Accept':'text/plain', }
        pass
    conn = httplib.HTTPConnection(host)
    #print 'method:', method, 'host:', host, 'url:',url, 'data:', data
    #conn.request(method, url, data, headers)
    conn.request(method, url, data,)
    return conn

@log
def sync_host():
    global host_dict
    #pull hosts from server
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/wm/device/'
    conn = sendhttp(host, url,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        return
    #unfresh all hosts
    for hid, host in host_dict.iteritems():
        host.fresh = False
        '''
    print 'after unfresh all hosts'
    for hid, host in host_dict.iteritems():
        print '%s; fresh:%s' % (host_dict[hid], host_dict[hid].fresh)
        '''
    #fresh hosts
    host_list = json.loads(resdata)
    for host in host_list:
        if not ('ipv4' in host):
            continue
        if not ('mac' in host):
            continue
        ipv4_list = [ ipv4 for ipv4 in host['ipv4'] if ipv4 != '0.0.0.0']
        mac_list = host['mac']
        if len(ipv4_list) <= 0:
          continue
        if len(mac_list) <= 0:
          continue
        ipv4 = ipv4_list[0]
        mac = mac_list[0]
        #print 'ipv4 = %s, mac = %s' % (ipv4, mac)
        hid = ipv4
        if hid not in host_dict:
            host_dict[hid] = Host()
            host_dict[hid].hid = hid
        host = host_dict[hid]
        host.ipv4 = ipv4
        host.mac = mac
        host.fresh = True
        '''
        #This is for test
        if host.ipv4 == '10.0.0.100':
            host.fresh = False
        '''
    '''
    print 'after fresh all hosts'
    for hid, host in host_dict.iteritems():
        print '%s; fresh:%s' % (host_dict[hid], host_dict[hid].fresh)
        '''
    #delete unfresh hosts
    for hid, host in host_dict.items():
        if not host_dict[hid].fresh:
            del host_dict[hid]
        '''
    print 'after delete unfresh hosts'
    for hid, host in host_dict.iteritems():
        print '%s; fresh:%s' % (host_dict[hid], host_dict[hid].fresh)
        '''

@log
def sync_vip():
    global vip_dict
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/vips/'
    conn = sendhttp(host, url,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        return
    vip_list = json.loads(resdata)

    #set all LBVip unfresh
    for vid, vip in vip_dict.iteritems():
        vip.fresh = False
        '''
    print 'after unfresh all vips'
    for vid, vip in vip_dict.iteritems():
        print '%s; fresh:%s' % (vip_dict[vid], vip_dict[vid].fresh)
        '''
    #refresh LBVip
    for vip in vip_list:
        vid = vip['id']
        if vid not in vip_dict:
            vip_dict[vid] = LBVip()
            vip_dict[vid].vid = vid
        v = vip_dict[vid]
        v.name = vip['name']
        v.protocol = vip['protocol']
        v.address = vip['address']
        v.port = vip['port']
        v.fresh = True
        '''
    print 'after fresh all vips'
    for vid, vip in vip_dict.iteritems():
        print '%s; fresh:%s' % (vip_dict[vid], vip_dict[vid].fresh)
        '''
    #delete unfreshed LBVip
    for vid, vip in vip_dict.items():
        if not vip_dict[vid].fresh:
            del vip_dict[vid]
        '''
    print 'after delete unfresh vips'
    for vid, vip in vip_dict.iteritems():
        print '%s; fresh:%s' % (vip_dict[vid], vip_dict[vid].fresh)
        '''

@log
def sync_pool():
    global vip_dict
    global pool_dict
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/pools/'
    conn = sendhttp(host, url,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        return
    pool_list = json.loads(resdata)

    #set all LBPool unfresh
    for pid, pool in pool_dict.iteritems():
        pool.fresh = False
        '''
    print 'after unfresh all pools'
    for pid, pool in pool_dict.iteritems():
        print '%s; fresh:%s' % (pool_dict[pid], pool_dict[pid].fresh)
        '''
    #refresh LBPool
    for pool in pool_list:
        pid = pool['id']
        if pid not in pool_dict:
            pool_dict[pid] = LBPool()
            pool_dict[pid].pid = pid
        p = pool_dict[pid]
        p.name = pool['name']
        #p.protocol = pool['protocol']
        vid = pool['vipId']
        #p.vip = vip_dict[vid]
        p.vip = vid
        p.fresh = True
        '''
    print 'after fresh all pools'
    for pid, pool in pool_dict.iteritems():
        print '%s; fresh:%s' % (pool_dict[pid], pool_dict[pid].fresh)
        '''
    #delete unfreshed LBPool
    for pid, pool in pool_dict.items():
        if not pool.fresh:
            del pool_dict[pid]
            '''
    print 'after unfresh all pools'
    for pid, pool in pool_dict.iteritems():
        print '%s; fresh:%s' % (pool_dict[pid], pool_dict[pid].fresh)
        '''

@log
def sync_member():
    global pool_dict
    global member_dict
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/members/'
    conn = sendhttp(host, url,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    #print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        print 'sync member fail!!'
        return
    member_list = json.loads(resdata)
    #print 'member_list.length:' , len(member_list)

    #set all LBMember unfresh
    for mid, member in member_dict.iteritems():
        member.fresh = False
        '''
    print 'after unfresh all members'
    for mid, member in member_dict.iteritems():
        print '%s; fresh:%s' % (member_dict[mid], member_dict[mid].fresh)
        '''
    #refresh LBMember
    for member in member_list:
        print 'member:', member
        mid = member['id']
        if mid not in member_dict:
            member_dict[mid] = LBMember()
            member_dict[mid].mid = mid
        m = member_dict[mid]
        m.address = member['address']
        m.port = member['port']
        #m.pool = pool_dict[member['poolId']]
        m.pool = member['poolId']
        m.run_status = int(member['runStatus'])
        m.fresh = True
        '''
    print 'after fresh all members'
    for mid, member in member_dict.iteritems():
        print '%s; fresh:%s' % (member_dict[mid], member_dict[mid].fresh)
        '''
    #delete unfreshed LBMember
    for mid, member in member_dict.items():
        if not member.fresh:
            del member_dict[mid]
            '''
    print 'after delete unfresh members'
    for mid, member in member_dict.iteritems():
        print '%s; fresh:%s' % (member_dict[mid], member_dict[mid].fresh)
        '''

@log
def push_flow():
    global flow_dict

    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/lbflow/'
    data = '{'
    first = True
    for fid, flow in flow_dict.iteritems():
        if not first:
            data += ','
        data += '"network_id":"%s", "weight":"%s", "member":"%s"' % (flow.get_network_id(), flow.weight, flow.member)
        first = False
    data += '}'
    #print data
    #data = '{"network_id":"123", "weight":"123.123", "member":"10.0.0.1", "network_id":"234", "weight":"1.23", "member":"10.0.0.1"}'
        
    method = 'PUT'
    conn = sendhttp(host, url, data, method)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    #print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        pass

def get_lb_match(entry):

  if str(entry).find('ipv4_') < 0:
      return None

  #print entry
  if 'match' not in entry:
      return None
  match = entry['match']
  if 'ipv4_src' in match:
      return 'ipv4_src~%s' % match['ipv4_src']
     
  if 'ipv4_dst' in match:
      return 'ipv4_dst~%s' % match['ipv4_dst']
     
  return None

def get_info1():
    #get flow entry info1
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/wm/staticflowpusher/list/all/json'
    conn = sendhttp(host, url,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    #print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        print 'sync flow fail!!'
        return None
    #print 'resdata:', resdata
    flow_entry_dict = json.loads(resdata)
    #print 'flow_entry_dict.length:' , len(flow_entry_dict)

    info1_dict = {}
    for switch, flow_entry_list in flow_entry_dict.iteritems():
        #print 'switch:', switch
        for entry in flow_entry_list:
            #print 'flow entry:'
            for key, val in entry.iteritems():
                info1_dict[key] = val
                fe = LBFlowEntry()
                fe.eid = key
                fe.info1 = str(val)
                #print fe.eid, ':' , type(fe.info1), ':', fe.info1

    #print 'len(info1_dict):', len(info1_dict)
    return info1_dict
    pass

def get_info2():
    #get flow entry info2
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/wm/core/switch/all/flow/json'
    conn = sendhttp(host, url,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    #print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        print 'sync flow fail!!'
        return None
    #print 'resdata:', resdata
    flow_entry_dict = json.loads(resdata)
    #print 'flow_entry_dict.length:' , len(flow_entry_dict)

    info2_dict = {}
    for switch, flow_entry_list in flow_entry_dict.iteritems():
        #print 'switch:', switch
        for entry in flow_entry_list['flows']:
            #print 'flow entry:'
            #print entry
            #filter load balancer entry
            if int(entry['cookie']) == 0x12345678:
                #print 'cookie:', entry['cookie']
                pass
            else:
                continue
            lb_match = get_lb_match(entry)
            if not lb_match:
                continue
            key = 'pinsw~' + switch +';'+ lb_match
            info2 = str(entry)
            info2_dict[key] = info2
            #print 'key:' + key
            pass
    #print 'len(info2_dict):', len(info2_dict)
    return info2_dict
    pass


@log
def sync_flow():
    global member_dict
    global flow_dict
    global entry_dict
    
    #get flow entry
    entry_dict = {}
    info1_dict = get_info1()
    info2_dict = get_info2()
    for eid, info1 in info1_dict.iteritems():
        entry = LBFlowEntry()
        entry.eid = str(eid)
        entry.info1 = str(info1)
        pinswmatch = entry.pinswmatch
        #print 'pinswmatch:', pinswmatch
        entry.info2 = str(info2_dict[pinswmatch])
        #print 'entry.packet_count:', entry.packet_count
        #print 'entry.fid:', entry.fid
        entry_dict[eid] = entry

    #set flow
    for eid, entry in entry_dict.iteritems():
        fid = entry.get_fid()
        if fid not in flow_dict:
            flow_dict[fid] = LBFlow()
            flow_dict[fid].fid = fid
        flow = flow_dict[fid]
        #entry.flow = flow
        entry.flow = fid
        #print entry

    #set flow inbound/outbound
    for fid, flow in flow_dict.iteritems():
        flow.inbound_entry_list = []
        flow.outbound_entry_list = []
    for eid, entry in entry_dict.iteritems():
        flow = flow_dict[entry.flow]
        if entry.eid.find('inbound') >= 0:
            flow.inbound_entry_list.append(entry)
        elif entry.eid.find('outbound') >= 0:
            flow.outbound_entry_list.append(entry)
        else :
            print 'ERROR in sync_flow, entry should be inbound or outbound!!!!!'
    #set member of flow
    for mid, member in member_dict.iteritems():
        member.flow_list = []
    for fid, flow in flow_dict.iteritems():
        mid = flow.get_mid()
        flow.member = mid
        member = member_dict[mid]
        member.flow_list.append(flow)
    #set old_req_count, old_duraction
    for fid, flow in flow_dict.iteritems():
         flow.old_req_count = flow.req_count
         flow.old_duraction = flow.duraction
    #set req_count, duraction
    for fid, flow in flow_dict.iteritems():
         flow.req_count = float(flow.outbound_entry_list[-1].packet_count) / 4.0
         flow.duraction = float(flow.outbound_entry_list[-1].duraction)
    for fid, flow in flow_dict.iteritems():
         d = flow.duraction - flow.old_duraction 
         r = flow.req_count - flow.old_req_count
         g = 0.3
         if d == 0 :
             print 'ERROR in sync_flow, d==0!!!!!'
             flow.weight = 1
         else :
             flow.weight = g * (r / d) + (1-g) * flow.weight
             flow.weight = (r / d) + 1
    for mid, member in member_dict.iteritems():
        member.weight = 0
    #set weight of flow
    for fid, flow in flow_dict.iteritems():
        member = member_dict[flow.member]
        member.weight += flow.weight

    #push flow into server
    push_flow()
        
@log
def add_vip(vip):
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/vips/'
    data = vip
    method = 'PUT'
    conn = sendhttp(host, url, data, method,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) == 200:
        vip_ = json.loads(resdata)
        print 'add vip: %s' % (vip_,) 
    return status, reason, resdata

@log
def add_pool(pool):
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/pools/'
    data = pool
    method = 'PUT'
    conn = sendhttp(host, url, data, method,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) == 200:
        pool_ = json.loads(resdata)
        print 'add pool: %s' % (pool_,) 
    return status, reason, resdata
    
@log
def add_member(member):
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/members/'
    data = member
    method = 'PUT'
    conn = sendhttp(host, url, data, method,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) == 200:
        member_ = json.loads(resdata)
        print 'add member: %s' % (member_,) 
    return status, reason, resdata

@log
def del_vip(vip):
    print 'to be implememt'
    pass

@log
def del_pool(pool):
    print 'to be implememt'
    pass
  
@log
def del_member(mid):
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    member = mid
    url = '/quantum/v1.0/members/%s' % (member,)
    #print 'url:', url
    data = None
    method = 'DELETE'
    conn = sendhttp(host, url, data, method,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) == 200:
        print 'del member: %s' % (member,) 
    return status, reason, resdata

@log
def upd_vip(vip):
    status, reason, resdata = add_vip(vip)
    if int(status) == 200:
        vip_ = json.loads(resdata)
        print 'update vip: %s [last add-operation is actually update-operation]' % (vip_,) 
    return status, reason, resdata

@log
def upd_vip(pool):
    status, reason, resdata = add_pool(pool)
    if int(status) == 200:
        pool_ = json.loads(resdata)
        print 'update pool: %s [last add-operation is actually update-operation]' % (pool_,) 
    return status, reason, resdata

@log
def upd_member(member):
    status, reason, resdata = add_member(member)
    if int(status) == 200:
        member_ = json.loads(resdata)
        print 'update member: %s [last add-operation is actually update-operation]' % (member_,) 
    return status, reason, resdata

@log
def check_member(member_):
    #member_01 = '{"id":"1", "pool_id":"1", "address":"10.0.0.1", "port":"80"}'
    valid = True
    if 'id' not in member_:
        valid = False
    if 'pool_id' not in member_:
        valid = False
    if 'address' not in member_:
        valid = False
    if 'port' not in member_:
        valid = False
    return valid

@log
def del_flow(flow):
    global entry_dict
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/wm/staticflowpusher/json'
    #print 'url:', url
    data = {}
    method = 'DELETE'
    for eid, entry in entry_dict.items():
        if entry.flow != flow.fid:
            continue
        print 'delete', entry
        data = '{"name":"%s"}' % (entry.eid)
        conn = sendhttp(host, url, data, method,)
        httpres = conn.getresponse()
        status = httpres.status
        reason = httpres.reason
        resdata = httpres.read()
        conn.close()
        print 'status: %s, reason: %s' % (status, reason)
        del entry_dict[eid]
        if int(status) != 200:
            print 'fail to del flow entry %s!!!!' % (entry.eid,) 
    #return status, reason, resdata
    return 'OK'
