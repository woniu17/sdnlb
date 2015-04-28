#!/bin/bash
#add lbvip
curl -d '{"id":"1", "name":"vip-01", "protocol":"icmp", "address":"10.0.0.200", "port":"80"}' \
 -X PUT http://127.0.0.1:8080/quantum/v1.0/vips/

#add pool
curl -d '{"id":"1", "name":"pool-01", "protocol":"icmp", "vip_id":"1"}' \
 -X PUT http://127.0.0.1:8080/quantum/v1.0/pools/

#add member 1
curl -d '{"id":"1", "pool_id":"1", "address":"10.0.0.1", "port":"80"}' \
 -X PUT http://127.0.0.1:8080/quantum/v1.0/members/

#add member 2
curl -d '{"id":"2", "pool_id":"1", "address":"10.0.0.2", "port":"80"}' \
 -X PUT http://127.0.0.1:8080/quantum/v1.0/members/

