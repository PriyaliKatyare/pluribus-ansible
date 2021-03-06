#!/usr/bin/python
""" PN Switch Config Reset """

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

import shlex
import time

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_switch_config_reset
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
description: Module to reset a switch.
options:
    pn_cliusername:
      description:
        - Provide login username if user is not root.
      required: True
      type: str
    pn_clipassword:
      description:
        - Provide login password if user is not root.
      required: True
      type: str
    pn_host_list:
      description:
        - Specify list of all hosts/switches.
      required: True
      type: list
    pn_host_ips:
      description:
        - Specify ips of all hosts/switches separated by comma.
      required: True
      type: str
"""

EXAMPLES = """
- name: Reset switches
    pn_switch_config_reset:
      pn_cliusername: "{{ USERNAME }}"
      pn_clipassword: "{{ PASSWORD }}"
      pn_host_list: "{{ groups['all'] }}"
      pn_host_ips: "{{ groups['all'] |
        map('extract', hostvars, ['ansible_host']) | join(',') }}"

"""

RETURN = """
summary:
  description: It contains output along with switch name.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
unreachable:
  description: Indicates whether host was unreachable to connect.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
exception:
  description: Describes error/exception occurred while executing CLI command.
  returned: always
  type: str
task:
  description: Name of the task getting executed on switch.
  returned: always
  type: str
msg:
  description: Indicates whether configuration made was successful or failed.
  returned: always
  type: str
"""


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(argument_spec=dict(
        pn_cliusername=dict(required=True, type='str'),
        pn_clipassword=dict(required=True, type='str', no_log=True),
        pn_host_list=dict(required=True, type='list'),
        pn_host_ips=dict(required=True, type='str'),
    ))

    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    switch_list = module.params['pn_host_list']
    switch_ips = module.params['pn_host_ips']

    switch_ips = switch_ips.split(',')
    result, reset_ips = [], []
    count = 0
    changed_flag, unreachable_flag = [], []

    ssh_prefix = "ssh -o StrictHostKeyChecking=no"

    for ip in switch_ips:
        cli = 'sshpass -p %s ' % password
        cli += '%s %s@%s ' % (ssh_prefix, username, ip)

        cli = shlex.split(cli)
        rc, out, err = module.run_command(cli)
        err = err.lower()

        if 'permission denied' in err:
            result.append({
                'switch': switch_list[count],
                'output': 'Switch has been already reset'
            })
        elif 'no route to host' in err:
            unreachable_flag.append(True)
            result.append({
                'switch': switch_list[count],
                'output': 'Switch is unreachable'
            })
        elif 'permission denied' not in err and not rc:
            cli = 'sshpass -p %s %s %s@%s ' % (password, ssh_prefix, username, ip)
            cli += 'shell /usr/bin/cli --quiet '
            cli += '--user %s:%s --no-login-prompt ' % (username, password)
            cli += 'switch-config-reset'

            cli = shlex.split(cli)
            module.run_command(cli)
            changed_flag.append(True)
            reset_ips.append(ip)

            result.append({
                'switch': switch_list[count],
                'output': 'Switch reset completed'
            })
        else:
            cli = 'sshpass -p %s %s %s@%s ' % (password, ssh_prefix, username, ip)
            cli += 'shell /usr/bin/cli --quiet '
            cli += '--user %s:%s --no-login-prompt ' % (username, password)
            cli += 'switch-config-reset'                

            cli = shlex.split(cli)
            module.run_command(cli)
            changed_flag.append(True)
            reset_ips.append(ip)

            result.append({
                'switch': switch_list[count],
                'output': 'Switch reset completed. (This is an unhandled case. Please forward the log to the technical team)\n RC: %s\n ERR: %s\n OUT: %s' % (rc, err, out)
            })

        count += 1

    if reset_ips:
        # Wait 180 secs for nvOS to come up
        time.sleep(180)

        # Check until we are able to ssh into switches
        for ip in reset_ips:
            epocs = 0
            while epocs <= 6:
                cli = 'sshpass -p %s ' % password
                cli += '%s %s@%s ' % (ssh_prefix, username, ip)

                cli = shlex.split(cli)
                rc, out, err = module.run_command(cli)

                if 'permission denied' in err.lower():
                    break

                time.sleep(10)
                epocs += 1

    # Exit the module and return the required JSON
    module.exit_json(
        unreachable=True if True in unreachable_flag else False,
        msg='Switch config reset completed successfully',
        summary=result,
        exception='',
        task='Switch config reset',
        failed=False,
        changed=True if True in changed_flag else False
    )

if __name__ == '__main__':
    main()

