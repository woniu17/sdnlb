#encoding=utf-8
import json
import httplib, urllib
from models import *
CONTROLLER_HOST = '127.0.0.1:8080'

def sendhttp(host, url='/', data=None, method='GET', headers=None):
    if headers == None:
        headers = { 'Content-type':'application/x-www-form-urlencoded', 'Accept':'text/plain', }
    conn = httplib.HTTPConnection(host)
    conn.request(method, url, data, headers)
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

    LBVip.objects.all().delete()
    for vip in vip_list:
        v = LBVip()
        v.vid = int(vip['id'])
        v.name = vip['name']
        v.protocol = vip['protocol']
        v.address = vip['address']
        v.port = vip['port']
        v.save()
        print v

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

    LBPool.objects.all().delete()
    for pool in pool_list:
        p = LBPool()
        p.pid = int(pool['id'])
        p.name = pool['name']
        #p.protocol = pool['protocol']
        p.vip = LBVip.objects.get(vid=int(pool['vipId']))
        p.save()
        print p

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
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        return
    member_list = json.loads(resdata)

    LBMember.objects.all().delete()
    for member in member_list:
        m = LBMember()
        m.mid = int(member['id'])
        m.address = member['address']
        m.port = member['port']
        m.pool = LBPool.objects.get(pid=int(member['poolId']))
        m.save()
        print m

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
    if int(status) != 200:
        return
    vip_ = json.loads(resdata)
    print 'add vip: %s' % (vip_,) 

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
    if int(status) != 200:
        return
    pool_ = json.loads(resdata)
    print 'add pool: %s' % (pool_,) 
    
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
    if int(status) != 200:
        return
    member_ = json.loads(resdata)
    print 'add member: %s' % (member_,) 

def del_member(member):
    global CONTROLLER_HOST
    host = CONTROLLER_HOST
    url = '/quantum/v1.0/members/'
    data = member
    method = 'DELETE'
    conn = sendhttp(host, url, data, method,)
    httpres = conn.getresponse()
    status = httpres.status
    reason = httpres.reason
    resdata = httpres.read()
    conn.close()
    print 'status: %s, reason: %s' % (status, reason)
    if int(status) != 200:
        return
    res = 'success' if int(resdata) == 0 else 'failure'
    print 'del member %s %s' % (member, res) 
    res = True if int(resdata) == 0 else False
    return res
