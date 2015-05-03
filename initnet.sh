#!/bin/bash
sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0
sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6653
sudo ifconfig br0 10.0.0.254 netmask 255.255.255.0

sudo ovs-vsctl del-br br1
sudo ovs-vsctl add-br br1
sudo ovs-vsctl set-controller br1 tcp:127.0.0.1:6653

#connect br0 and br1
sudo ovs-vsctl \
add-port br0 patch01 \
-- set interface patch01 type=patch options:peer=patch10
sudo ovs-vsctl \
add-port br1 patch10 \
-- set interface patch10 type=patch options:peer=patch01

#for debian-01(10.0.0.1/24)
sudo ip tuntap del mode tap br0-eth1
sudo ip tuntap add mode tap br0-eth1
sudo ip link set br0-eth1 up
sudo ovs-vsctl add-port br0 br0-eth1

#for debian-02(10.0.0.2/24)
sudo ip tuntap del mode tap br0-eth2
sudo ip tuntap add mode tap br0-eth2
sudo ip link set br0-eth2 up
sudo ovs-vsctl add-port br0 br0-eth2

#for debian-03(10.0.0.3/24)
sudo ip tuntap del mode tap br0-eth3
sudo ip tuntap add mode tap br0-eth3
sudo ip link set br0-eth3 up
sudo ovs-vsctl add-port br0 br0-eth3

#for debian-04(10.0.0.4/24)
sudo ip tuntap del mode tap br0-eth4
sudo ip tuntap add mode tap br0-eth4
sudo ip link set br0-eth4 up
sudo ovs-vsctl add-port br0 br0-eth4

#for debian-00(10.0.0.100/24)
sudo ip tuntap del mode tap br1-eth0
sudo ip tuntap add mode tap br1-eth0
sudo ip link set br1-eth0 up
sudo ovs-vsctl add-port br1 br1-eth0

#VBoxManage startvm debian-01 --type gui
#VBoxManage startvm debian-02 --type gui
#VBoxManage startvm debian-03 --type gui
