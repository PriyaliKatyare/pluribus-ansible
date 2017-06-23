#!/usr/bin/python

"""
This python script is to validate an output of a Ansible playbook.
It validates whether output of a playbook is a valid JSON object or not.
It also checks if all the required fields mentioned under in
`fields_to_check` variable are present in the JSON object or not.

Example Usage:
python pn_validate_json.py playbook.yml

To validate pn_initial_ztp.yml playbook, run this script as:
python pn_validate_json.py pn_initial_ztp.yml

This script takes playbook name as input and returns a string describing if
output of the playbook is a valid/invalid JSON object and if all required
fields (like status, summary, msg etc) are present in the JSON object or not.
"""

import json
import shlex
import subprocess
import sys

if len(sys.argv) != 2:
    msg = 'Execution Error: Please provide Ansible playbook name!\n'
    msg += 'Example usage: python validate_json.py playbook.yml'
    exit(msg)

playbook = sys.argv[1]
command = ' ansible-playbook -i hosts ' + playbook
command += ' --vault-password-file ~/.vault_pass.txt '

print('')
print('Started executing playbook {}'.format(playbook))
print('')
print('A message will appear when playbook execution is finished')
print('')
print('Kindly wait until then as it may take some time')
print('')

std_out = subprocess.check_output(shlex.split(command))

print('Finished executing playbook {}'.format(playbook))
print('')
print('Validating JSON output')
print('')

delimiter = "Pausing for 2 seconds\n"
delimiter += "(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)"

json_object_list = std_out.split(delimiter)
json_object_list = json_object_list[:-1]

msg = ''
print('Validation Complete')
print('')

for json_object in json_object_list:
    try:
        json.loads(json_object)
    except ValueError:
        exit('Result: Output of {} is an INVALID JSON object'.format(playbook))

    fields_to_check = [r'"task":', r'"summary":', r'"msg":', r'"status":']
    extra_fields = [r'"output":', r'"switch":']

    if r'"status": "0"' in json_object:
        fields_to_check += extra_fields
    elif r'"status": "1"' in json_object:
        for field in extra_fields:
            if field in json_object:
                msg += 'Since value of status is 1, '
                msg += '{} field should not be present '.format(field)
                msg += 'in the JSON output\n'

    for field in fields_to_check:
        if field not in json_object:
            msg += '{} field is missing from the JSON output\n'.format(field)

print('Result: Output of {} is a VALID JSON object'.format(playbook))

if msg == '':
    print('And, all the required fields are present in this JSON object')
    print('')
else:
    print('But,')
    exit(msg)

