#encoding=utf-8
import json
import httplib, urllib
from models import *
from django.core.exceptions import ObjectDoesNotExist
CONTROLLER_HOST = '127.0.0.1:8080'

def sendhttp(host, url='/', data=None, method='GET', headers=None):
    if method == 'PUT' or method == 'POST':
        #headers = { 'Content-type':'application/javascript', 'Accept':'text/plain', }
        pass
    conn = httplib.HTTPConnection(host)
    print 'method:', method, 'host:', host, 'url:',url, 'data:', data
    #conn.request(method, url, data, headers)
    conn.request(method, url, data,)
    return conn

def sync_host():
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
    host_list = json.loads(resdata)

    Host.objects.all().delete()
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
        print 'ipv4 = %s, mac = %s' % (ipv4, mac)
        host = Host()
        host.ipv4 = ipv4
        host.mac = mac
        host.save()

def sync_vip():
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
    v_list = LBVip.objects.all()
    for v in v_list:
        v.fresh = False
        v.save() #must save, because the filter(fresh=False) will retrive from db

    #refresh LBVip
    for vip in vip_list:
        v = None
        try :
            v = LBVip.objects.get(vid=vip['id'])
        except ObjectDoesNotExist:
            print 'vip' ,vip['id'], 'does not exist'
            v = LBVip()
            v.vid = vip['id']
        v.name = vip['name']
        v.protocol = vip['protocol']
        v.address = vip['address']
        v.port = vip['port']
        v.fresh = True
        v.save()
        print v

    #delete unfreshed LBVip
    v_list.filter(fresh=False).delete()

def sync_pool():
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
    p_list = LBPool.objects.all()
    for p in p_list:
        p.fresh = False
        p.save() #must save, because the filter(fresh=False) will retrive from db

    #refresh LBPool
    for pool in pool_list:
        p = None
        try :
            p = LBPool.objects.get(pid=pool['id'])
        except ObjectDoesNotExist:
            print 'pool' ,pool['id'], 'does not exist'
            p = LBPool()
            p.pid = pool['id']
        p.name = pool['name']
        #p.protocol = pool['protocol']
        p.vip = LBVip.objects.get(vid=int(pool['vipId']))
        p.fresh = True
        p.save()
        print p

    #delete unfreshed LBPool
    p_list.filter(fresh=False).delete()

def sync_member():
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
    print 'member_list.length:' , len(member_list)

    #set all LBMember unfresh
    m_list = LBMember.objects.all()
    for m in m_list:
        m.fresh = False
        m.save() #must save, because the filter(fresh=False) will retrive from db

    #refresh LBMember
    for member in member_list:
        m = None
        try :
            m = LBMember.objects.get(mid=member['id'])
        except ObjectDoesNotExist:
            print 'member' ,member['id'], 'does not exist'
            m = LBMember()
            m.mid = member['id']

        m.address = member['address']
        m.port = member['port']
        m.pool = LBPool.objects.get(pid=int(member['poolId']))
        m.fresh = True
        m.save()
        print m
    #delete unfreshed LBMember
    #print 'm_list.length:', len(m_list)
    #print 'm_list.fresh(False).length:', len(m_list.filter(fresh=False))
    m_list.filter(fresh=False).delete()


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

def push_flow():
    flow_list = LBFlow.objects.all()
    for flow in flow_list:
        flow.weight = float(flow.packet_count) / 4.0
        flow.save()

    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/lbflow/'
    data = '{'
    first = True
    for flow in LBFlow.objects.all():
        if not first:
            data += ','
        data += '"network_id":"%s", "weight":"%s", "member":"%s"' % (flow.get_network_id(), flow.weight, flow.member.mid)
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

def sync_flow():
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    
    LBFlow.objects.all().delete()
    LBFlowEntry.objects.all().delete()
    #get flow entry info1
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
        return
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
    #get flow entry info2
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
        return
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


    #get flow entry
    fe_list = []
    for eid, info1 in info1_dict.iteritems():
        fe = LBFlowEntry()
        fe.eid = str(eid)
        fe.info1 = str(info1)
        pinswmatch = fe.pinswmatch
        #print 'pinswmatch:', pinswmatch
        fe.info2 = str(info2_dict[pinswmatch])
        #print 'fe.packet_count:', fe.packet_count
        #print 'fe.fid:', fe.fid
        fe_list.append(fe)

    flow_dict = {}
    mid_dict = {}
    for fe in fe_list:
        fid = fe.get_fid()
        if fid not in flow_dict:
            flow_dict[fid] = LBFlow()
            flow_dict[fid].fid = fid
            #flow_dict[fid].save()
        flow = flow_dict[fid]
        fe.flow = flow

        if fid in mid_dict:
            continue
        if fe.eid.find('inbound') < 0:
            continue
        info1 = eval(fe.info1)
        if 'instructions' not in info1:
            continue
        inst = info1['instructions']
        if 'instruction_apply_actions' not in inst:
            continue
        actions = inst['instruction_apply_actions']
        if 'ipv4_dst' not in actions:
            continue
        mid_dict[fid] = actions['ipv4_dst']
        #fe.save()

    for fid, flow in flow_dict.iteritems():
        mid = mid_dict[fid] 
        try :
            member = LBMember.objects.get(mid=mid)
            flow.member = member
            flow.save()
        except ObjectDoesNotExist:
            print 'no member', mid
            pass
    for fe in fe_list:
        fe.save()
    for fid, flow in flow_dict.iteritems():
        break
        #print 'fid:', fid, '; flow:', flow
        inbound_entry_list = flow.inbound_entry_list
        for entry in inbound_entry_list:
           print 'inbound entry:', entry
        outbound_entry_list = flow.outbound_entry_list
        for entry in outbound_entry_list:
           print 'outbound entry:', entry
    push_flow()

        

    '''
    #set all LBMember unfresh
    m_list = LBMember.objects.all()
    for m in m_list:
        m.fresh = False
        m.save() #must save, because the filter(fresh=False) will retrive from db

    #refresh Flow
    for member in member_list:
        m = None
        try :
            m = LBMember.objects.get(mid=member['id'])
        except ObjectDoesNotExist:
            print 'member' ,member['id'], 'does not exist'
            m = LBMember()
            m.mid = member['id']

        m.address = member['address']
        m.port = member['port']
        m.pool = LBPool.objects.get(pid=int(member['poolId']))
        m.fresh = True
        m.save()
        print m
    #delete unfreshed LBMember
    #print 'm_list.length:', len(m_list)
    #print 'm_list.fresh(False).length:', len(m_list.filter(fresh=False))
    m_list.filter(fresh=False).delete()
    '''

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

def del_vip(vip):
    print 'to be implememt'
    pass

def del_pool(pool):
    print 'to be implememt'
    pass
  
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

def upd_vip(vip):
    status, reason, resdata = add_vip(vip)
    if int(status) == 200:
        vip_ = json.loads(resdata)
        print 'update vip: %s [last add-operation is actually update-operation]' % (vip_,) 
    return status, reason, resdata

def upd_vip(pool):
    status, reason, resdata = add_pool(pool)
    if int(status) == 200:
        pool_ = json.loads(resdata)
        print 'update pool: %s [last add-operation is actually update-operation]' % (pool_,) 
    return status, reason, resdata

def upd_member(member):
    status, reason, resdata = add_member(member)
    if int(status) == 200:
        member_ = json.loads(resdata)
        print 'update member: %s [last add-operation is actually update-operation]' % (member_,) 
    return status, reason, resdata

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

def del_flow(flow):
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/wm/staticflowpusher/json'
    #print 'url:', url
    data = {}
    method = 'DELETE'
    entry_list = flow.lbflowentry_set.all()
    for entry in entry_list:
        print 'entry', entry.eid
        data = '{"name":"%s"}' % (entry.eid)
        conn = sendhttp(host, url, data, method,)
        httpres = conn.getresponse()
        status = httpres.status
        reason = httpres.reason
        resdata = httpres.read()
        conn.close()
        print 'status: %s, reason: %s' % (status, reason)
        if int(status) != 200:
            print 'fail to del flow entry %s!!!!' % (entry.eid,) 
    #return status, reason, resdata
    return 'OK'
  
