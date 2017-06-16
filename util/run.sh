#!/bin/bash
#
# run | run.sh
#
# This script is designed to automate the typical process of making sure the
# remote library file is installed and running the ansible-playbook command.
# This script can also be used for pre-pending the relevant library methods to
# the playbook being run. Because playbooks are currently released with under the
# expectation that there will not be a library file on the remote host, all
# testing should use run <playbook> -a so that the relevant files are generated.
# However, for 'dirty' testing, it is often faster to run the playbooks raw,
# especially if the library file does not need to be updated.
#
# Usage: run <playbook> [-kaf]
# 
# Known "Features" (Bugs):
# This script only checks that the library file is present on the FIRST host
# listed in the HOSTFILE. For reliable preformance, either manually verify that
# pn_ansible_lib.py exists on all remotes or issue run ./copy_lib.sh before doing
# any development.
#

FILE=$1
UNAME="pluribus"
COMPATH="../ansible/common"
LIBPATH="../ansible/library"
PLAYPATH="../ansible/playbooks"
HOSTPATH="$PLAYPATH/hosts"
KEEPFLAG=0
IP='10.9.21.106'

echo -n "Enter Password for $UNAME: "
read -s PASS

case "$2" in
    -k|--keep-temp-modules)
	KEEPFLAG=1
	;;
    -a|--append)
	#TODO: Prepend the used functions at the top of the playbook files
	echo "appending"
	;;
    -f|--force-update)
	echo "forcing update to remote libraries"
	./copy_lib.sh -p $PASS
	;;
    *)
	# # Check that pn_ansible_lib hasn't been updated. If it has make a temp
	# # file and generate a new wrapper file
	# OLD=$(sum ._pal.tmp.py | awk '{print $1,$2}')
	# NEW=$(sum $COMPATH/pn_ansible_lib.py | awk '{print $1,$2}')
	# if [ "$OLD" != "$NEW" ]
	# then
	#     cp $COMPATH/pn_ansible_lib.py ._pal.tmp.py
	#     python generate_python_wrappers.py > AG_pn_ansible_lib.py
	#     ./copy_lib.sh -p $PASS
	# else
	#     # Check that the library file on the remote is up to date. If it
	#     # isn't then update the remote library function
	#     sum AG_pn_ansible_lib.py > loc.t
	#     echo test123 | ssh -tt pluribus@$IP > /dev/null 2>&1 sum /usr/lib/python2.7/pn_ansible_lib.py > rem.t
	#     LOC=$(cat loc.t | awk '{print $1,$2}')
	#     REM=$(tail -1 rem.t | awk '{print $1,$2}' | sed "s/$(printf '\r')\$//" | sed "s/^0//")
	#     rm loc.t
	#     rm rem.t
	#     if [ "$LOC" != "$REM" ]
	#     then
	# 	./copy_lib.sh -p $PASS
	#     fi
	# fi
	;;
esac

ansible-playbook $PLAYPATH/$1.yml -i $HOSTPATH -u $UNAME -K --ask-pass --ask-vault-pass -vvv
