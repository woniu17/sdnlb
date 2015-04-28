# Create your views here.
#encoding=utf-8
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, render
from models import *

import httplib, urllib
def sendhttp(host, url='/', data=None, method='GET', headers=None):
    if headers == None:
        headers = { 'Content-type':'application/x-www-form-urlencoded', 'Accept':'text/plain', }
    conn = httplib.HTTPConnection(host)
    conn.request(method, url, data, headers)
    return conn

def update_host_list(host_list):
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

def home(request):

    host = '127.0.0.1:8080'
    url = '/wm/device/'
    data = None
    conn = sendhttp(host, url, data,)
    httpres = conn.getresponse()
    print httpres.status
    print httpres.reason
    import json
    host_list = json.loads(httpres.read())
    if int(httpres.status) == 200:
        update_host_list(host_list)
    host_list = Host.objects.all()
    return render(request, 'lb/index.html', {'host_list':host_list,})

