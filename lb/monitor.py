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
dynamic_provision = True

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

def get_to_delete_flow_list():
     global flow_dict
     global member_dict
     active_member_dict = {}
     for mid, member in member_dict.iteritems():
         if member.is_active():
             active_member_dict[mid] = member
     if len(active_member_dict) <= 0 or len(flow_dict) <= 0 :
        return []
     to_delete_flow_list = []
     avg_weight = 0.0
     for mid, member in active_member_dict.iteritems():
         avg_weight += member.weight
     avg_weight /= len(active_member_dict)
     for fid, flow in flow_dict.iteritems():
         member = active_member_dict[flow.member]
         if member.weight <= avg_weight:
             continue
         d1 = member.weight - avg_weight
         d2 = avg_weight - (member.weight - flow.weight)
         if d2 >= d1 :
           continue
         member.weight -= flow.weight
         to_delete_flow_list.append(flow)
     return to_delete_flow_list

'''
benchmark load of cluster
normal load, return 0
low load, return -1
high load, return 1
'''
def benchmark():
     global member_dict
     active_member_dict = {}
     for mid, member in member_dict.iteritems():
         if member.is_active():
             active_member_dict[mid] = member
     #select a standby member to active if high load
     standby_member = None
     for mid, member in member_dict.iteritems():
         if member.is_standby():
             standby_member = member
             break
     #select the active member with maximal weight to standby if low load
     active_member = None
     max_weight = 0.0
     for mid, member in active_member_dict.iteritems():
          if max_weight < member.weight :
              active_member = member
              max_weight = member.weight
     #get avg_weight to determine cluster load
     avg_weight = 0.0
     for mid, member in active_member_dict.iteritems():
         avg_weight += member.weight
     if len(active_member_dict) > 0 :
        avg_weight /= len(active_member_dict)

     if avg_weight < 25 and len(active_member_dict)>2 :
         return (-1, active_member)
     if avg_weight > 44 :
         return (1, standby_member)
     return  (0,)

def standby_member(member):
    print 'standby', member
    event = 'dynamic provision, standby %s' % (member,)
    #set to-standby member's runstatus STANDBY, that make sure new flow would not go to to-standby member
    actions = []
    m = member
    rs = LBMember.RUNSTATUS_STANDBY
    m_ = '{"id":"%s", "pool_id":"%s", "address":"%s", "port":"%s", "run_status":"%s"}' % (m.mid, m.pool, m.naddress, m.port, rs)
    status_reason_resdata = upd_member(m_)
    action = 'make %s into %s status' % (m, LBMember.STR_RUNSTATUS[rs])
    print 'action:', action
    actions.append(action)
    #del flows which go to to-standby member
    sync_flow()
    global flow_dict
    for fid, flow in flow_dict.items():
        if flow.member != m.mid:
            continue
        del_flow(flow)
        del flow_dict[fid]
        action = 'del %s' % (flow,)
        actions.append(action)
    global log_list
    log = {'time':time.strftime('%H:%M:%S'), 'event':event, 'actions':actions}
    log_list.append(log)
    sync_member()

def active_member(member):
    print 'active', member
    event = 'dynamic provision, active %s' % (member,)
    #set to-standby member's runstatus STANDBY, that make sure new flow would not go to to-standby member
    actions = []
    m = member
    rs = LBMember.RUNSTATUS_ACTIVE
    m_ = '{"id":"%s", "pool_id":"%s", "address":"%s", "port":"%s", "run_status":"%s"}' % (m.mid, m.pool, m.naddress, m.port, rs)
    status_reason_resdata = upd_member(m_)
    action = 'make %s into %s status' % (m, LBMember.STR_RUNSTATUS[rs])
    print 'action:', action
    actions.append(action)
    global log_list
    log = {'time':time.strftime('%H:%M:%S'), 'event':event, 'actions':actions}
    log_list.append(log)
    sync_member()

def balance_algorithm():
    print 'balance algorithm!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    global flow_dict
    global log_list
    if dynamic_provision :
        print 'dynamic_provision!!!!!!!!!!!!!!!!!!!!!!!!!'
        res = benchmark()
        if res[0] < 0 and res[1] :
            standby_member(res[1])
        elif res[0] > 0 and res[1] :
            active_member(res[1])
            return
            '''
            do not balance now, it will delete some flow because of the new active member
            '''

    to_delete_flow_list = get_to_delete_flow_list()
    if len(to_delete_flow_list) <= 0 :
        return False
    event = 'execute balance algorithm because of unbalanced status'
    actions = []
    for flow in to_delete_flow_list :
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
        host = '%s:%s' % (member.naddress, member.port)
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
    
