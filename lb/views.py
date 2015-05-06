# Create your views here.
#encoding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from models import *
from dbtool import *
import json
import functools
import monitor

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
def log(f):
    @functools.wraps(f)
    def fn(*args, **argskw):
        print 'call lb.%s' % (f.__name__, )
        return f(*args, **argskw)
    return fn

@log
def init():
    sync_host()
    sync_vip()
    sync_pool()
    sync_member()
    sync_flow()
    vip = '{"id":"1", "name":"vip-01", "protocol":"icmp", "address":"10.0.0.200", "port":"80"}'
    pool = '{"id":"1", "name":"pool-01", "protocol":"icmp", "vip_id":"1"}'
    member_01 = '{"id":"10.0.0.1", "pool_id":"1", "address":"10.0.0.1", "port":"80"}'
    member_02 = '{"id":"10.0.0.2", "pool_id":"1", "address":"10.0.0.2", "port":"80"}'
    if len(LBVip.objects.all()) <= 0:
        add_vip(vip)
        add_pool(pool)
        #add_member(member_01)
        #add_member(member_02)
        sync_vip()
        sync_pool()
        sync_member()
        sync_flow()

@log
@check_daemon
def home(request):

    init()
    host_list = Host.objects.all()
    vip_list = LBVip.objects.all()
    return render(request, 'lb/index.html', {'host_list':host_list, 'vip_list':vip_list})

@log
@check_daemon
def ajax_del_member(request):
    print 'ajax del member'
    if 'mid' not in request.POST:
      return HttpResponse('{"status":"-1", "reason":"form has not mid","data":"no"}', mimetype='application/javascript')
    mid = request.POST['mid']
    #print 'member:', mid
    status_reason_resdata = del_member(mid)
    res = '{"status":"%s", "reason":"%s", "data":"%s"}' % status_reason_resdata
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
    status_reason_data = add_member(member)
    res = '{"status":"%s", "reason":"%s", "data":"%s"}' % status_reason_data
    print 'res:', res
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
    from django.core import serializers
    member_list = serializers.serialize('json', LBMember.objects.all())
    return HttpResponse(member_list, mimetype='application/javascript')
    pass

