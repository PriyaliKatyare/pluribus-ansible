#!/bin/bash

# README:
#
# This script will push an updated pn_ansible_lib.py file to all of the
# destinations in the hosts file located at HOSTPATH. It will log into
# every switch using UNAME@address through ssh. This will cause you to type in a
# lot of password if you don't have ssh keys set up. I HIGHLY reccomend setting
# up your host keys before you use this script.ls
# 

UNAME="pluribus"
HOSTPATH="ansible/playbooks/hosts"

echo -n "Enter Password for $UNAME: "
read PASS

grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' $HOSTPATH | while read -r line; do
    echo "removing old pn_ansible_lib.py from $UNAME@$line"
    echo "pushing pn_ansible_lib.py to $UNAME@$line"
    scp ansible/library/pn_ansible_lib.py $UNAME@$line:~
    echo $PASS | ssh -tt $UNAME@$line sudo -S cp pn_ansible_lib.py /usr/lib/python2.7/pn_ansible_lib.py
done
