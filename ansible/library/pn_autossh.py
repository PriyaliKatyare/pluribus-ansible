#!/usr/bin/python
""" PN module for auto SSH key setup """

#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#

import os
import shlex
import paramiko
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_autossh
author: "Pluribus Networks (devops@pluribusnetworks.com)"
version: 1.0
short_description: Module to auto setup SSH keys between localhost and remote nodes.
description:
  - This module checks for SSH keys on localhost and generates them if they don't exist.
    The public key of the localhost is then pushed to the remote nodes for password-less
    authentication.
options:
  pn_user:
    description:
      - Provide remote user name.
    required: True
    type: str
  pn_ssh_password:
    description:
      - Provide SSH login password.
    required: True
    type: str
  pn_hosts_csv:
     description:
       - Provide topology information in a csv file in (hostname, ip) format.
     required: True
     type: str
  pn_overwrite:
     description:
       - Flag that inform if /.ssh/authorized_keys file should be overwritten or appended.
     required: False
     type: bool
     default: False
  pn_filepath:
     description:
       - File path to save the keys on localhost.
     required: True
     type: str
"""

EXAMPLES = """
- name: Auto setup SSH keys
  pn_autossh:
    pn_user: "{{ remote_user }}"
    pn_ssh_password: "{{ PASSWORD }}"
    pn_hosts.csv: "{{ lookup('file', '{{ csv_file }}') }}"
    pn_overwrite: False
    pn_filepath: "{{ lookup('env','HOME') + '/.ssh/id_rsa' }}"
"""

RETURN = """
stdout:
  description: the set of responses from the vlan command.
  returned: always
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""


def deploy_key(sshkey, address, username, password, overwrite):
    """
    :param sshkey: The sshkey id
    :param address: The address of the destination host
    :param username: The user we will be connecting as
    :param password: The password for the user
    :param overwrite: Boolean, if enabled, deploy_key will overwite the
        authorized keys in ~/.ssh/authorized_keys
    :return: A string informing the caller that the keys were pushed to the host
    """

    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(address, username=username, password=password)
    client.exec_command('mkdir -p ~/.ssh/')

    if overwrite is True:
        client.exec_command('echo "%s" > ~/.ssh/authorized_keys' % sshkey)
    else:
        client.exec_command('echo "%s" >> ~/.ssh/authorized_keys' % sshkey)

    client.exec_command('chmod 644 ~/.ssh/authorized_keys')
    client.exec_command('chmod 700 ~/.ssh/')
    return "Keys Pushed to host: %s \n" % address


def generate_key(path, module):
    """
    :param path: The path to the input keyfile
    :param module: The module where the run_command function is located
    :return: A string informing the caller that the keys were generated
    """

    cmd = 'ssh-keygen -t rsa -f %s -q -N %s' % (path, '""')
    cmd = shlex.split(cmd)
    out, err = module.run_command(cmd)[1:]

    if out:
        return out
    if err:
        module.exit_json(
            error='1',
            failed=True,
            stderr=err.strip(),
            msg='Operation Failed: Could not generate keys!',
            changed=False
        )
    else:
        return 'SSH Keys generated on localhost \n'


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_user=dict(required=True, type='str'),
            pn_ssh_password=dict(required=True, type='str'),
            pn_hosts_csv=dict(required=True, type='str'),
            pn_overwrite=dict(required=False, type='bool', default=False),
            pn_filepath=dict(required=True, type='str')
        )
    )
    message = ''
    user = module.params['pn_user']
    ssh_password = module.params['pn_ssh_password']
    csv_data = module.params['pn_hosts_csv']
    filepath = module.params['pn_filepath']
    overwrite = module.params['pn_overwrite']

    if not os.path.exists(filepath):
        message += generate_key(filepath, module)

    filepath_pub = str(filepath) + '.pub'
    key = open(filepath_pub).read()

    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.splitlines()

    for item in csv_data_list:
        host = item.split(',')[1]
        message += deploy_key(key, host, user, ssh_password, overwrite)

    module.exit_json(
        stdout=message,
        msg="Operation Completed",
        changed=True
    )


if __name__ == '__main__':
    main()
