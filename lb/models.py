from django.db import models

import socket, struct

# Create your models here.
class Host(models.Model):
    hid = models.AutoField(primary_key=True) 
    ipv4 = models.CharField(max_length=17, null=True)
    mac = models.CharField(max_length=18, null=True)

    def __unicode__(self,):
      return 'Host %d, ip: %s, mac: %s' % (self.hid, self.ipv4, self.mac,)

class LBVip(models.Model):
    vid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, null=True)
    protocol = models.CharField(max_length=10, null=True)
    address = models.CharField(max_length=17, null=True)
    port = models.CharField(max_length=10, null=True)

    @property
    def naddress(self,):
        naddress = socket.inet_ntoa(struct.pack('I',socket.htonl(int(self.address))))
        return naddress
    
    @naddress.setter
    def naddress(self, address):
        self.address = socket.ntohl(struct.unpack("I",socket.inet_aton(str(address)))[0])
    
    def __unicode__(self,):
      return '[LBVIP %d: %s][%s:%s]' % (self.vid, self.name, self.naddress, self.port)


class LBPool(models.Model):
    pid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, null=True)
    protocol = models.CharField(max_length=10, null=True)
    vip = models.ForeignKey(LBVip)
    
    def __unicode__(self,):
      return 'LBPool %d[%s]' % (self.pid, self.name,)


class LBMember(models.Model):
    mid = models.CharField(max_length=17, primary_key=True)
    address = models.CharField(max_length=17, null=True)
    naddress = models.CharField(max_length=17, null=True)
    port = models.CharField(max_length=10, null=True)
    pool = models.ForeignKey(LBPool)
    
    @property
    def naddress(self,):
        naddress = socket.inet_ntoa(struct.pack('I',socket.htonl(int(self.address))))
        return naddress
    
    @naddress.setter
    def naddress(self, address):
        self.address = socket.ntohl(struct.unpack("I",socket.inet_aton(str(address)))[0])
    
    def __unicode__(self,):
      return 'LBMember %s[%s:%s]' % (self.mid, self.naddress, self.port)


