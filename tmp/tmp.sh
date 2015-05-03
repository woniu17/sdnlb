#!/bin/bash
while true; do
    sudo ovs-ofctl dump-flows br0 table=0 | wc -l
    sleep 1s
done
