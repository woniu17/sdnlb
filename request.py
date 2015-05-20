#!/usr/bin/env python
import threading, time
import commands

def request(url, interface):
    cmd = 'curl %s --interface %s' % (url, interface)
    status, output = commands.getstatusoutput(cmd)
    print status, output
    pass

def start():
    for i in xrange(128, 218):
        url = 'http://10.0.0.200/index.html'
        interface = '%d.0.0.%d' % (i, i)
        req = threading.Thread(target=request, args=(url, interface))
        req.setDaemon(True)
        req.start()


if __name__ == '__main__' :
    while True :
        start()
