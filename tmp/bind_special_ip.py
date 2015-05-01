import urllib2, httplib, socket

class BindableHTTPConnection(httplib.HTTPConnection):
    def connect(self):
    	"""Connect to the host and port specified in __init__."""
    	self.sock = socket.socket()
    	self.sock.bind((self.source_ip, 0))
    	if isinstance(self.timeout, float):
    		self.sock.settimeout(self.timeout)
    	self.sock.connect((self.host,self.port))

def BindableHTTPConnectionFactory(source_ip):
    def _get(host, port=None, strict=None, timeout=0):
    	bhc=BindableHTTPConnection(host, port=port, strict=strict, timeout=timeout)
    	bhc.source_ip=source_ip
    	return bhc
    return _get

class BindableHTTPHandler(urllib2.HTTPHandler):
    def http_open(self, req):
    	return self.do_open(BindableHTTPConnectionFactory('211.80.196.236'), req)

opener = urllib2.build_opener(BindableHTTPHandler)
print opener.open("http://www.baidu.com/").read() # Will fail, 128.0.0.1 can't reach google.com.
