#!/usr/bin/python

import sys,os
import time
import commands
import threading, time
import httplib, urllib
from models import *
from dbtool import *

MONITOR_DAEMON = None
PAUSE_MONITOR = False

def update_server_status(member, server_status):
    #print server_status
    #print member.naddress
    now = time.strftime('%H:%M:%S')
    member.update_time = now
    line_list = server_status.split('\n');
    para_list = []
    for line in line_list:
        para_list.append(line.split(':')[-1].strip())
    i = 0
    #print para_list[i]
    member.req_count = int(para_list[i])
    i = i+1
    #print para_list[i]
    member.kb_count = int(para_list[i])
    i = i+1
    #print para_list[i]
    member.cpu_load = float(para_list[i])
    i = i+1
    #print para_list[i]
    member.uptime = int(para_list[i])
    i = i+1
    #print para_list[i]
    member.req_per_sec = float(para_list[i])
    i = i+1
    #print para_list[i]
    member.byte_per_sec = float(para_list[i])
    i = i+1
    #print para_list[i]
    member.byte_per_req = float(para_list[i])
    i = i+1
    #print para_list[i]
    member.busy_workers = int(para_list[i])
    i = i+1
    #print para_list[i]
    member.idle_workers = int(para_list[i])
    i = i+1
    pass

def balance_algorithm():
    print 'balance algorithm!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    global flow_dict
    global log_list
    to_delete_flow_list = get_to_delete_flow_list()
    if len(to_delete_flow_list) <= 0 :
        return False
    event = 'execute balance algorithm because of unbalanced status'
    actions = []
    for flow in to_delete_flow_list :
        print flow
        del_flow(flow)
        action = 'del %s' % (flow,)
        print 'action:', action
        actions.append(action)
        del flow_dict[flow.fid]
    log = {'time':time.strftime('%H:%M:%S'), 'event':event, 'actions':actions}
    log_list.append(log)

'''
sync member, flow
so when add/del/update member or flow, pause it
'''
def member_monitor():
    global member_dict
    global PAUSE_MONITOR
    if PAUSE_MONITOR:
        print 'PAUSE MONITOR!!!!!!!!!!!!!'
        return
    #sync flow statistic
    sync_flow()
    #update server status
    for mid, member in member_dict.iteritems():
        #TODO about synchronization
        host = member.naddress
        url = '/server-status?auto'
        method = 'GET'
        data = None
        conn = httplib.HTTPConnection(host)
        conn.request(method, url, data,)
        httpres = conn.getresponse()
        status = httpres.status
        reason = httpres.reason
        resdata = httpres.read()
        conn.close()
        if status == 200 :
            update_server_status(member, resdata)
    #check if is blanced
    balance_algorithm()
    return

def monitor_daemon(right_now):
    current_thread = threading.currentThread()
    if right_now:
        print '[At %s, %s] start  geting server status from member server...' % (current_thread, time.strftime('%H:%M:%S'))
        member_monitor()
        print '[At %s, %s] finish geting server status from member server...' % (current_thread, time.strftime('%H:%M:%S'))
        time.sleep(10)
    global MONITOR_DAEMON
    MONITOR_DAEMON = threading.Thread(target=monitor_daemon, args=(True,) )
    MONITOR_DAEMON.setDaemon(True)
    print '[At %s, %s] start daemon %s' % (current_thread, time.strftime('%H:%M:%S'), MONITOR_DAEMON,)
    MONITOR_DAEMON.start()
    return
    
