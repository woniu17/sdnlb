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
