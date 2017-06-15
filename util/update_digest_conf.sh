#!/bin/bash

cd ../

grep -oP 'nvOS_data_apply_upgrades unable to find conversion from\K.*' /var/nvOS/log/nvOSd.log | grep -oP ' to \K.*' | tail -1 > temp.txt
cat temp.txt > /var/nvOS/etc/digest.conf
rm temp.txt
service svc-nvOSd restart
