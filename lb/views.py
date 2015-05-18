# Create your views here.
#encoding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from models import *
from dbtool import *
import json
import monitor
from tool import *
import time
import json

def check_daemon(f):
    @functools.wraps(f)
    def fn(*args, **argskw):
        print 'check daemon'
        if monitor.MONITOR_DAEMON and monitor.MONITOR_DAEMON.is_alive():
            print 'daemon is alive'
            return f(*args, **argskw)

        print 'monitor.MONITOR_DAEMON:', monitor.MONITOR_DAEMON
        print 'daemon is not alive, start it!!!'
        monitor.monitor_daemon(right_now = False)
        return f(*args, **argskw)
    return fn

@log
def init():
    global host_dict
    global vip_dict
    global pool_dict
    sync_host()
    sync_vip()
    sync_pool()
    sync_member()
    vip = '{"id":"1", "name":"vip-01", "protocol":"icmp", "address":"10.0.0.200", "port":"80"}'
    pool = '{"id":"1", "name":"pool-01", "protocol":"icmp", "vip_id":"1"}'
    #member_01 = '{"id":"10.0.0.1", "pool_id":"1", "address":"10.0.0.1", "port":"80"}'
    #member_02 = '{"id":"10.0.0.2", "pool_id":"1", "address":"10.0.0.2", "port":"80"}'
    if len(vip_dict) <= 0:
        add_vip(vip)
        add_pool(pool)
        #add_member(member_01)
        #add_member(member_02)
        sync_vip()
        sync_pool()
        sync_member()
        #sync_flow()

@log
@check_daemon
def home(request):
    init()
    global host_dict
    global vip_dict
    global pool_dict
    global log_list
    host_list = sorted(host_dict.values(), key=lambda h: h.mac)
    return render(request, 'lb/index.html', {'host_list':host_list, 'vip_list':vip_dict.values(), 'pool_list':pool_dict.values(),})

@log
@check_daemon
def ajax_del_member(request):
    global member_dict
    global flow_dict
    monitor.PAUSE_MONITOR = True
    if 'mid' not in request.POST:
      return HttpResponse('{"status":"-1", "reason":"form has not mid","data":"no"}', mimetype='application/javascript')
    mid = request.POST['mid']
    member = member_dict[mid]
    actions = []
    #set to-del member's runstatus TOSTOP, that make sure new flow would not go to to-del member
    m = member
    rs = LBMember.RUNSTATUS_TOSTOP
    m_ = '{"id":"%s", "pool_id":"%s", "address":"%s", "port":"%s", "run_status":"%s"}' % (m.mid, m.pool, m.naddress, m.port, rs)
    status_reason_resdata = upd_member(m_)
    action = 'make %s into %s status' % (m, LBMember.STR_RUNSTATUS[rs])
    actions.append(action)
    #del flows which go to to-del member
    actions_ = del_flow_by_mid(mid)
    actions.extend(actions_)
    #safely remove to-del member
    status_reason_resdata = del_member(mid)
    res = '{"status":"%s", "reason":"%s", "data":"%s"}' % status_reason_resdata
    #delay dynamic provision to make sure that flows have been redistribute
    monitor.DELAY_DYNAMIC_PROVISION = 2
    #log event
    event = 'del member %s:%s' % (member.mid, member.port)
    actions.append(event)
    global log_list
    log = {'time':time.strftime('%H:%M:%S'), 'event':event, 'actions':actions}
    log_list.append(log)
    #sync member and flow
    sync_member()
    sync_flow()
    monitor.PAUSE_MONITOR = False
    return HttpResponse(res, mimetype='application/javascript')
    pass

@log
@check_daemon
def ajax_del_pool(request):
    pass

@log
@check_daemon
def ajax_del_vip(request):
    pass

@log
@check_daemon
def ajax_add_member(request):
    global member_dict
    global flow_dict
    #check data's validation
    if 'member' not in request.POST:
        res = '{"status":"-1", "reason":"form has not member","data":"no"}'
        print 'res:', res
        return HttpResponse(res, mimetype='application/javascript')
    member = request.POST['member']
    member_ = json.loads(member)
    valid = check_member(member_)
    if not valid:
        res = '{"status":"-1", "reason":"member info not complete: %s","data":"no"}' % (member,)
        print 'res:', res
        return HttpResponse(res, mimetype='application/javascript')
    mid = member_['id']
    #if mid is exist, deny to add member
    if mid in member_dict:
        res = '{"status":"-1", "reason":"member %s has exsit","data":"no"}' % (member,)
        print 'res:', res
        return HttpResponse(res, mimetype='application/javascript')
    #add member
    monitor.PAUSE_MONITOR = True
    member_dict[mid] = LBMember()
    member_dict[mid].mid = mid
    status_reason_data = add_member(member)
    res = '{"status":"%s", "reason":"%s", "data":"%s"}' % status_reason_data
    print 'res:', res
    sync_member()
    #execute balance_member_weight
    actions_ = monitor.balance_member_weight()
    #delay dynamic provision to make sure that flows have been redistribute
    monitor.DELAY_DYNAMIC_PROVISION = 2
    #log event
    event = 'add member %s:%s' % (member_['id'], member_['port'])
    actions = []
    actions.append(event)
    actions.extend(actions_)
    global log_list
    log = {'time':time.strftime('%H:%M:%S'), 'event':event, 'actions':actions}
    log_list.append(log)
    monitor.PAUSE_MONITOR = False
    return HttpResponse(res, mimetype='application/javascript')
    pass

@log
@check_daemon
def ajax_add_pool(request):
    pass

@log
@check_daemon
def ajax_add_vip(request):
    pass

@log
@check_daemon
def ajax_upd_member(request):
    if 'member' not in request.POST:
      return '{"status":"-1", "reason":"form has not member","data":"no"}'
    member = request.POST['member']
    member_ = json.loads(member)
    valid = check_member(member_)
    #mid of member which is to update
    if 'member' not in member_:
        valid = False
    if not valid:
      return '{"status":"-1", "reason":"member info not complete: %s","data":"no"}' % (member,)
    status_reason_data = upd_member(member)
    return status_reason_data
    pass

@log
@check_daemon
def ajax_upd_pool(request):
    pass

@log
@check_daemon
def ajax_upd_vip(request):
    pass

@log
@check_daemon
def ajax_get_member_list(request):
    global member_dict
    global flow_dict
    global log_list
    from django.core import serializers
    member_list = sorted(member_dict.values(), key=lambda m: m.mid)
    member_list = serializers.serialize('json',member_list )
    #print member_list
    flow_list = sorted(flow_dict.values(), key=lambda f: f.fid)
    flow_list = serializers.serialize('json',flow_list )
    #print flow_list
    log_list_ = json.dumps(log_list)
    resdata = '{"member_list" : %s, "flow_list" : %s, "log_list":%s}' % (member_list, flow_list, log_list_)
    return HttpResponse(resdata, mimetype='application/javascript')
    pass

