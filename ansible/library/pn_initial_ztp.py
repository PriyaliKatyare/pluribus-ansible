#!/usr/bin/python
""" PN CLI Zero Touch Provisioning (ZTP) """

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

import pn_ansible_lib as pn
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_initial_ztp
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: CLI command to do zero touch provisioning.
description:
    Zero Touch Provisioning (ZTP) allows you to provision new switches in your
    network automatically, without manual intervention.
    It performs following steps:
        - Accept EULA
        - Disable STP
        - Enable all ports
        - Create/Join fabric
        - Enable STP
options:
    pn_cliusername:
        description:
          - Provide login username if user is not root.
        required: False
        type: str
    pn_clipassword:
      description:
        - Provide login password if user is not root.
      required: False
      type: str
    pn_fabric_name:
      description:
        - Specify name of the fabric.
      required: False
      type: str
    pn_fabric_network:
      description:
        - Specify fabric network type as either mgmt or in-band.
      required: False
      type: str
      choices: ['mgmt', 'in-band']
      default: 'mgmt'
    pn_fabric_control_network:
      description:
        - Specify fabric control network as either mgmt or in-band.
      required: False
      type: str
      choices: ['mgmt', 'in-band']
      default: 'mgmt'
    pn_toggle_40g:
      description:
        - Flag to indicate if 40g ports should be converted to 10g ports or not.
      required: False
      default: True
      type: bool
    pn_spine_list:
      description:
        - Specify list of Spine hosts
      required: False
      type: list
    pn_leaf_list:
      description:
        - Specify list of leaf hosts
      required: False
      type: list
    pn_inband_ip:
      description:
        - Inband ips to be assigned to switches starting with this value.
      required: False
      default: 172.16.0.0/24.
      type: str
    pn_current_switch:
      description:
        - Name of the switch on which this task is currently getting executed.
      required: False
      type: str
    pn_static_setup:
      description:
        - Flag to indicate if static values should be assign to
        following switch setup params.
      required: False
      default: False
      type: bool
    pn_mgmt_ip:
      description:
        - Specify MGMT-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_mgmt_ip_subnet:
      description:
        - Specify subnet mask for MGMT-IP value to be assign if
        pn_static_setup is True.
      required: False
      type: str
    pn_gateway_ip:
      description:
        - Specify GATEWAY-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_dns_ip:
      description:
        - Specify DNS-IP value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_dns_secondary_ip:
      description:
        - Specify DNS-SECONDARY-IP value to be assign if pn_static_setup is True
      required: False
      type: str
    pn_domain_name:
      description:
        - Specify DOMAIN-NAME value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_ntp_server:
      description:
        - Specify NTP-SERVER value to be assign if pn_static_setup is True.
      required: False
      type: str
    pn_web_api:
      description:
        - Flag to enable web api.
      default: True
      type: bool
    pn_stp:
      description:
        - Flag to enable STP at the end.
      required: False
      default: False
      type: bool
"""

EXAMPLES = """
- name: Auto accept EULA, Disable STP, enable ports and create/join fabric
    pn_initial_ztp:
      pn_cliusername: "{{ USERNAME }}"
      pn_clipassword: "{{ PASSWORD }}"
      pn_fabric_name: 'ztp-fabric'
      pn_current_switch: "{{ inventory_hostname }}"
      pn_spine_list: "{{ groups['spine'] }}"
      pn_leaf_list: "{{ groups['leaf'] }}"
"""

RETURN = """
stdout:
  description: The set of responses for each command.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
failed:
  description: Indicates whether or not the execution failed on the target.
  returned: always
  type: bool
"""

CHANGED_FLAG = []

def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=True, type='str'),
            pn_fabric_network=dict(required=False, type='str',
                                   choices=['mgmt', 'in-band'],
                                   default='mgmt'),
            pn_fabric_control_network=dict(required=False, type='str',
                                           choices=['mgmt', 'in-band'],
                                           default='mgmt'),
            pn_toggle_40g=dict(required=False, type='bool', default=True),
            pn_spine_list=dict(required=False, type='list', default=[]),
            pn_leaf_list=dict(required=False, type='list', default=[]),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_current_switch=dict(required=False, type='str'),
            pn_static_setup=dict(required=False, type='bool', default=True),
            pn_mgmt_ip=dict(required=False, type='str'),
            pn_mgmt_ip_subnet=dict(required=False, type='str'),
            pn_gateway_ip=dict(required=False, type='str'),
            pn_dns_ip=dict(required=False, type='str'),
            pn_dns_secondary_ip=dict(required=False, type='str'),
            pn_domain_name=dict(required=False, type='str'),
            pn_ntp_server=dict(required=False, type='str'),
            pn_web_api=dict(type='bool', default=True),
            pn_stp=dict(required=False, type='bool', default=False),
        )
    ) 

    cli = pn.PN_cli(module)
    
    changed = False
    cli.auto_accept_eula()

    # Make sure the switch has the correct name
    if module.params['pn_current_switch'] not in \
       cli.switch_setup_show(format='switch-name', show_headers=False):
        cli.switch_setup_modify(switch_name=module.params['pn_current_switch'])
        changed = True

    # Configure the switch
    if module.params['pn_static_setup']:
        #TODO: Can't pass parameters like this, none will pass
        #TODO: Verify setup to determine idempotency
        cli.switch_setup_modify(**module.params)

    fabric = cli.fabric_show(format='name',show_headers=False).split()
    
    # Make sure the switches are connected to the correct fabric
    if module.params['pn_fabric_name'] not in fabric:
        # TODO: un-join from existing fabrics and move to the correct fabric
        cli.fabric_create(name=module.params['pn_fabric_name'])
        changed = True

    if module.params['pn_fabric_control_network'] not in cli.fabric_info(format='control-network').split():
        cli.fabric_local_modify(control_network=module.params['pn_fabric_control_network'])
        changed = True

    # Enable the web api
    if module.params['pn_web_api']:
        cli.admin_service_modify(web=True, _if='mgmt')
        changed = True

    # Disable STP
    if 'yes' not in cli.stp_show(format='enable', show_headers=False).split():
        cli.stp_modify(enable=False)
        changed = True

    # Enable Ports
    if 'off' in cli.port_config_show(format='enable',
                                     show_headers=False).split():
        ports = cli.port_config_show(format='enable', show_headers=False)
        out40g = cli.port_config_show(format='port', speed='40g', show_headers=False)
        remove10g = []

        if len(out40g) > 0 and out40g != 'Success':
            out40g = out40g.split()
            for port_num in out40g:
                remove10g.append(port_num + '1')
                remove10g.append(port_num + '2')
                remove10g.append(port_num + '3')

        ports = list(set(out.split()) - set(remove10g))
        if ports:
            ports = ','.join(ports)
            cli.port_config_modify(port=ports, enable=True)
            changed = True

    # Toggle 40g ports to 10g
    if module.params['pn_toggle_40g']:
        loc_ports = cli.lldp_show(format='local-port', show_headers=False)
        ports_40g = cli.port_config_show(speed='40g', show_headers=False)

        if len(ports_40g) > 0 and ports_40g != 'Success':
            modify = set(ports_40g.split()) - set(loc_ports.split())

            for port in modify:
                next = str(int(port) + 1)
                bezel_port = cli.port_show(format='bezel-port', show_headers=False)

                if '.2' in bezel_port:
                    range_p = port + '-' + str(int(port) + 3)
                    cli.port_config_modify(port=port, enable=False, speed='10g')
                    cli.port_config_modify(port=range_port, enable=True)
                    changed = True

    
    # Assign in-band ips.
    address = module.params['pn_inband_ip'].split('.')
    switch_list = []
    
    if module.params['pn_spine_list']:
        switch_list += module.params['pn_spine_list']

    if module.params['pn_leaf_list']:
        switch_list += module.params['pn_spine_list']

    if switch_list:
        ip_count = switches_list.index(module.params['pn_current_switch']) + 1
        ip = '.'.join(address[:2]) + str(ip_count) + '/' + str(address[3]).split('/')[1]
        cli.switch_setup_modify(in_band_ip=ip)
        changed = True
    
    # message += assign_inband_ip(module)

    if module.params['pn_stp']:
        if 'yes' not in cli.stp_show(format='enable', show_headers=False):
            cli.stp_modify(enable=True)
            changed = True
    
    # Exit the module and return the required JSON
    module.exit_json(
        stdout="out",
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()
