#!/bin/bash
sudo ovs-vsctl del-br br0
sudo ovs-vsctl add-br br0
sudo ovs-vsctl set-controller br0 tcp:127.0.0.1:6653

sudo ip tuntap del mode tap br0-eth1
sudo ip tuntap add mode tap br0-eth1
sudo ip link set br0-eth1 up
sudo ovs-vsctl add-port br0 br0-eth1

sudo ip tuntap del mode tap br0-eth2
sudo ip tuntap add mode tap br0-eth2
sudo ip link set br0-eth2 up
sudo ovs-vsctl add-port br0 br0-eth2

sudo ip tuntap del mode tap br0-eth3
sudo ip tuntap add mode tap br0-eth3
sudo ip link set br0-eth3 up
sudo ovs-vsctl add-port br0 br0-eth3

sudo ip tuntap del mode tap br0-eth0
sudo ip tuntap add mode tap br0-eth0
sudo ip link set br0-eth0 up
sudo ovs-vsctl add-port br0 br0-eth0
sudo ifconfig br0-eth0 10.0.0.100 netmask 255.255.255.0

VBoxManage startvm debian-01 --type gui
VBoxManage startvm debian-02 --type gui
VBoxManage startvm debian-03 --type gui
