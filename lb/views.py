# Create your views here.
#encoding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from models import *
from dbtool import *

def init():
    sync_host()
    sync_vip()
    sync_pool()
    sync_member()
    vip = '{"id":"1", "name":"vip-01", "protocol":"icmp", "address":"10.0.0.200", "port":"80"}'
    pool = '{"id":"1", "name":"pool-01", "protocol":"icmp", "vip_id":"1"}'
    member_01 = '{"id":"1", "pool_id":"1", "address":"10.0.0.1", "port":"80"}'
    member_02 = '{"id":"2", "pool_id":"1", "address":"10.0.0.2", "port":"80"}'
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

def del_member(request):
    pass
