#!/bin/bash

# README:
#
# This script will push an updated pn_ansible_lib.py file to all of the
# destinations in the hosts file located at HOSTPATH. It will log into
# every switch using UNAME@address through ssh. This will cause you to type in a
# lot of password if you don't have ssh keys set up. I HIGHLY reccomend setting
# up your host keys before you use this script.ls
#
# simply run ./copy_lib.sh

UNAME="pluribus"
HOSTPATH="ansible/playbooks/hosts"

case "$1" in
    -p|--password)
	PASS=$2
	;;
    *)
	echo -n "Enter Password for $UNAME: "
	read -s PASS
	;;
esac

echo "Generating library file"
rm AG_pn_ansible_lib.py
python generate_python_wrappers.py > tmp
cat ansible/library/pn_ansible_lib.py tmp > AG_pn_ansible_lib.py
rm tmp

grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}' $HOSTPATH | while read -r line; do
    echo "removing old pn_ansible_lib.py from $UNAME@$line"
    echo $PASS | ssh -tt $UNAME@$line sudo rm /usr/lib/python2.7/pn_ansible_lib.py > /dev/null 2>&1
    echo $PASS | ssh -tt $UNAME@$line sudo rm /usr/lib/python2.7/pn_ansible_lib.pyc > /dev/null 2>&1
    
    echo "pushing pn_ansible_lib.py to $UNAME@$line"
    scp AG_pn_ansible_lib.py $UNAME@$line:~ > /dev/null 2>&1
    echo $PASS | ssh -tt $UNAME@$line sudo -S cp AG_pn_ansible_lib.py /usr/lib/python2.7/pn_ansible_lib.py > /dev/null 2>&1
done

echo "Done"
