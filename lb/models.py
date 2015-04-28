from django.db import models

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
    
    def __unicode__(self,):
      return 'LBVip %d' % (self.vid,)


class LBPool(models.Model):
    pid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20, null=True)
    protocol = models.CharField(max_length=10, null=True)
    vip = models.ForeignKey(LBVip)
    
    def __unicode__(self,):
      return 'LBPool %d' % (self.pid,)


class LBMember(models.Model):
    mid = models.AutoField(primary_key=True)
    address = models.CharField(max_length=17, null=True)
    port = models.CharField(max_length=10, null=True)
    pool = models.ForeignKey(LBPool)
    
    def __unicode__(self,):
      return 'LBMember %d' % (self.mid,)


