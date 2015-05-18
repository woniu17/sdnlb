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
DYNAMIC_PROVISION = True
DELAY_DYNAMIC_PROVISION = 0

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

def determine_balance():
     global flow_dict
     global member_dict
     active_member_dict = {}
     for mid, member in member_dict.iteritems():
         if member.is_active():
             active_member_dict[mid] = member
     if len(active_member_dict) <= 1 :
          return True
     min_weight = 100000000
     max_weight = 0
     for mid, member in active_member_dict.iteritems():
         if member.weight < min_weight :
             min_weight = member.weight
         if member.weight > max_weight :
             max_weight = member.weight
     #determine if balance
     return (max_weight - min_weight ) < 3


def balance_member_weight():
    global flow_dict
    global member_dict
    #get active member
    active_member_dict = {}
    for mid, member in member_dict.iteritems():
        if member.is_active():
            active_member_dict[mid] = member
    if len(active_member_dict) <= 0 or len(flow_dict) <= 0 :
       return [] #no actions
    #get average weight among members
    avg_weight = 0.0
    for mid, member in active_member_dict.iteritems():
        avg_weight += member.weight
    avg_weight /= len(active_member_dict)
    #get flows which make load balance after being deleted
    to_delete_flow_list = []
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
    #delete flows
    actions = []
    for flow in to_delete_flow_list :
        del_flow(flow)
        action = 'del %s' % (flow,)
        print 'action:', action
        actions.append(action)
        del flow_dict[flow.fid]
    return actions

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
     max_weight = -1
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

     if avg_weight < 25 and len(active_member_dict) > 2 :
         return (-1, active_member)
     if avg_weight > 44 :
         return (1, standby_member)
     return  (0,)

def standby_member(member):
    print 'standby', member
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
    actions_ = del_flow_by_mid(m.mid)
    actions.extend(actions_)
    #log event
    global log_list
    event = 'dynamic provision, standby %s' % (member,)
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

def dynamic_provision():
    print 'DYNAMIC_PROVISION!!!!!!!!!!!!!!!!!!!!!!!!!'
    res = benchmark()
    print res
    if res[0] < 0 and res[1] :
        standby_member(res[1])
    elif res[0] > 0 and res[1] :
        active_member(res[1])
    #delay dynamic provision to make sure that flows have been redistribute
    global DELAY_DYNAMIC_PROVISION
    if res[0] != 0 :
        DELAY_DYNAMIC_PROVISION = 2

'''
sync member, flow
so when add/del/update member or flow, pause it
'''
def member_monitor():
    #sync flow statistic
    sync_flow()
    #update server status
    global member_dict
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
    #dynamic provision
    global DELAY_DYNAMIC_PROVISION
    if DYNAMIC_PROVISION :
        #delay dynamic provision to make sure that flows have been redistribute
        if DELAY_DYNAMIC_PROVISION > 0 :
            DELAY_DYNAMIC_PROVISION -= 1
        else :
            dynamic_provision()

    #balance algorithm
    balance = determine_balance()
    if balance is True :
        return
    print 'balance member weight!!!!!!!!!!!!!!!!!!!!!!!!!!!!!'
    event = 'execute balance algorithm because of unbalanced status'
    actions = balance_member_weight()
    log = {'time':time.strftime('%H:%M:%S'), 'event':event, 'actions':actions}
    global log_list
    log_list.append(log)

def monitor_daemon(right_now):
    global PAUSE_MONITOR
    current_thread = threading.currentThread()
    print '[At %s, %s] monitor daemon...' % (current_thread, time.strftime('%H:%M:%S'))
    if right_now:
        if PAUSE_MONITOR:
            print 'PAUSE MONITOR!!!!!!!!!!!!!'
        else :
            member_monitor()
        time.sleep(10)
    global MONITOR_DAEMON
    MONITOR_DAEMON = threading.Thread(target=monitor_daemon, args=(True,) )
    MONITOR_DAEMON.setDaemon(True)
    MONITOR_DAEMON.start()
    return
    
