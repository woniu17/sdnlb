# Create your views here.
#encoding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from models import *
from dbtool import *
import json

def init():
    sync_host()
    sync_vip()
    sync_pool()
    sync_member()
    vip = '{"id":"1", "name":"vip-01", "protocol":"icmp", "address":"10.0.0.200", "port":"80"}'
    pool = '{"id":"1", "name":"pool-01", "protocol":"icmp", "vip_id":"1"}'
    member_01 = '{"id":"10.0.0.1", "pool_id":"1", "address":"10.0.0.1", "port":"80"}'
    member_02 = '{"id":"10.0.0.2", "pool_id":"1", "address":"10.0.0.2", "port":"80"}'
    if len(LBVip.objects.all()) <= 0:
        add_vip(vip)
        add_pool(pool)
        add_member(member_01)
        add_member(member_02)
        sync_vip()
        sync_pool()
        sync_member()

def home(request):

    init()
    host_list = Host.objects.all()
    vip_list = LBVip.objects.all()
    return render(request, 'lb/index.html', {'host_list':host_list, 'vip_list':vip_list})

def ajax_del_member(request):
    print 'ajax del member'
    if 'mid' not in request.POST:
      return HttpResponse('{"status":"-1", "reason":"form has not mid","data":"no"}', mimetype='application/javascript')
    mid = request.POST['mid']
    member = '{"member":"%s"}' % (mid,)
    return HttpResponse('{"status":"0", "reason":"success", "data":"no"}', mimetype='application/javascript')
    status_reason_data = del_member(member)
    return status_reason_data
    pass

def ajax_del_pool(request):
    pass

def ajax_del_vip(request):
    pass

def ajax_add_member(request):
    if 'member' not in request.POST:
      return '{"status":"-1", "reason":"form has not member","data":"no"}'
    member = request.POST['member']
    member_ = json.loads(member)
    valid = check_member(member_)
    if not valid:
      return '{"status":"-1", "reason":"member info not complete: %s","data":"no"}' % (member,)
    status_reason_data = add_member(member)
    return status_reason_data
    pass

def ajax_add_pool(request):
    pass

def ajax_add_vip(request):
    pass

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

def ajax_upd_pool(request):
    pass

def ajax_upd_vip(request):
    pass

