#!/usr/bin/python
""" PN DCI """

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
module: pn_dci
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to implement a DCI.
description:
    This module is to plan and implement a DCI architecture.
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
    pn_current_switch:
      description:
        - Specify name of the current switch.
      required: True
      type: str
    pn_run_initial_setup:
      description:
        - Flag to accept eula
      required: True
      type: bool
    pn_spine_list:
      description:
        - Specify list of third party spine switches.
      required: True
      type: list
    pn_leaf_list:
      description:
        - Specify list of all DC leaf switches.
      required: True
      type: list
    pn_inband_ip:
      description:
        - Specify the inband ip address.
      required: False
      type: str
    pn_loopback_ip:
      description:
        - Specify the loopback interface ip.
      required: False
      type: str
    pn_bgp_ip:
      description:
        - Specify the bgp ip for creating neighbor.
      required: False
      type: str
    pn_bgp_redistribute:
      description:
        - Specify bgp_redistribute value to be added to vrouter.
      required: False
      type: str
      choices: ['none', 'static', 'connected', 'rip', 'ospf']
      default: 'connected'
    pn_bgp_maxpath:
      description:
        - Specify bgp_maxpath value to be added to vrouter.
      required: False
      type: str
      default: '16'
    pn_ibgp_vlan:
      description:
        - Specify vlan for iBGP configuration.
      required: False
      type: str
      default: '4040'
    pn_ibgp_ip_range:
      description:
        - Specify iBGP ip range to assigned during iBGP configuration.
      required: False
      type: str
      default: '75.75.75.0/30'
    pn_csv_data:
      description:
        - Specify VRRP and vxlan config data in the form of csv.
      required: False
      type: str
    pn_third_party_bgp_data:
      description:
        - Specify third party bgp config data in the form of csv.
      required: False
      type: str
"""

EXAMPLES = """
- name: Accept EULA, Join Fabric, Configure eBGP
  pn_dci:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_fabric_name: 'ansible_dci_fabric'
    pn_current_switch: "{{ inventory_hostname }}"
    pn_run_initial_setup: True
    pn_spine_list: "{{ groups['spine'] }}"
    pn_leaf_list: "{{ groups['leaf'] }}"
    pn_inband_ip: '172.18.0.0/24'
    pn_loopback_ip: '108.108.108.0/24'
    pn_bgp_ip: '100.1.1.0/30'
    pn_csv_data: "{{ lookup('file', '{{ dci_file }}') }}"
    pn_third_party_bgp_data: "{{ lookup('file', '{{ third_party_file }}') }}"

- name: Configure iBGP, VRRP and Vxlan
  pn_dci:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_fabric_name: 'ansible_dci_fabric'
    pn_current_switch: "{{ inventory_hostname }}"
    pn_run_initial_setup: False
    pn_spine_list: "{{ groups['spine'] }}"
    pn_leaf_list: "{{ groups['leaf'] }}"
    pn_inband_ip: '172.18.0.0/24'
    pn_loopback_ip: '108.108.108.0/24'
    pn_bgp_ip: '100.1.1.0/30'
    pn_csv_data: "{{ lookup('file', '{{ dci_file }}') }}"
    pn_third_party_bgp_data: "{{ lookup('file', '{{ third_party_file }}') }}"
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


def pn_cli(module):
    """
    Method to generate the cli portion to launch the Netvisor cli.
    :param module: The Ansible module to fetch username and password.
    :return: The cli string for further processing.
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    return cli


def run_cli(module, cli):
    """
    Method to execute the cli command on the target node(s) and returns the
    output.
    :param module: The Ansible module to fetch input parameters.
    :param cli: The complete cli string to be executed on the target node(s).
    :return: Output/Error or Success msg depending upon the response from cli.
    """
    cli = shlex.split(cli)
    out, err = module.run_command(cli)[1:]
    if out:
        return out

    if err:
        module.exit_json(
            error='1',
            failed=True,
            stderr=err.strip(),
            msg='Operation Failed: ' + str(cli),
            changed=False
        )
    else:
        return 'Success'


def auto_accept_eula(module):
    """
    Method to accept the EULA when we first login to a new switch.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of run_cli() method.
    """
    password = module.params['pn_clipassword']
    cli = ' /usr/bin/cli --quiet --skip-setup eula-show '
    cli = shlex.split(cli)
    out, err = module.run_command(cli)[1:]

    if err:
        cli = '/usr/bin/cli --quiet'
        cli += ' --skip-setup --script-password '
        cli += ' switch-setup-modify password ' + password
        cli += ' eula-accepted true '
        return run_cli(module, cli)
    elif out:
        return ' EULA has been accepted already '


def update_switch_names(module, switch_name):
    """
    Method to update switch names.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: Name to assign to the switch.
    :return: String describing switch name got modified or not.
    """
    cli = pn_cli(module)
    cli += ' switch-setup-show format switch-name '

    if switch_name in run_cli(module, cli).split()[1]:
        return ' Switch name is same as hostname! '

    cli = pn_cli(module)
    cli += ' switch-setup-modify switch-name ' + switch_name
    run_cli(module, cli)
    return ' Updated switch name to match hostname! '


def assign_inband_ip(module):
    """
    Method to assign in-band ips to switches.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing if in-band ip got assigned or not.
    """
    global CHANGED_FLAG
    inband_ip = module.params['pn_inband_ip']
    leaf_list = module.params['pn_leaf_list']
    current_switch = module.params['pn_current_switch']
    switch_position = leaf_list.index(current_switch) + 1

    address = inband_ip.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    ip = static_part + str(switch_position) + '.'
    ip += str(switch_position) + '/' + subnet

    cli = pn_cli(module)
    cli += 'switch-setup-modify in-band-ip %s ' % ip

    if 'Setup completed successfully' in run_cli(module, cli):
        CHANGED_FLAG.append(True)
        return ' %s: In-band ip assigned with ip %s \n' % (current_switch, ip)

    return ''


def create_switch_routes(module, inband_ip):
    """
    Method to create a switch routes
    :param module: The Ansible module to fetch input parameters.
    :param inband_ip: in-band ip of the switch.
    """
    inband_address = inband_ip.split(':')[1].split('.')
    static_part = str(inband_address[0]) + '.' + str(inband_address[1]) + '.'
    gateway_static_part = static_part + str(inband_address[2]) + '.'
    last_octet = str(inband_address[3]).split('/')
    subnet = last_octet[1]
    gateway_ip = gateway_static_part + str(int(last_octet[0]) + 1)
    switch_count = 1

    while switch_count <= len(module.params['pn_leaf_list']):
        network_ip = static_part + str(switch_count) + '.' + str(0)
        network_ip += '/' + subnet
        cli = pn_cli(module)
        cli += ' switch-route-create network %s gateway-ip %s ' % (
            network_ip, gateway_ip
        )
        switch_count += 1
        cli = shlex.split(cli)
        module.run_command(cli)


def configure_fabric(module, switch):
    """
    Method to configure (create/join) fabric.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the current switch.
    :return: String describing fabric creation/joining description.
    """
    global CHANGED_FLAG
    output = ''
    fabric_name = module.params['pn_fabric_name']
    switch_index = module.params['pn_leaf_list'].index(switch)

    address = module.params['pn_inband_ip'].split('.')
    inband_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    last_octet = str(address[3]).split('/')
    subnet = last_octet[1]

    if switch_index == 0:
        cli = pn_cli(module)
        clicopy = cli
        cli += 'fabric-show format name no-show-headers'
        existing_fabric = run_cli(module, cli).split()

        # Create fabric if not already created.
        if fabric_name not in existing_fabric:
            cli = clicopy
            cli += 'fabric-create name %s ' % fabric_name
            cli += ' fabric-network in-band control-network in-band '
            run_cli(module, cli)
            output += ' %s: Fabric %s created \n' % (switch, fabric_name)
            CHANGED_FLAG.append(True)
        else:
            output += ' %s: Fabric %s already exists \n' % (switch, fabric_name)

        # Indicate all subnets of the in-band interfaces of switches,
        # that will be part of the fabric.
        output += fabric_inband_net_create(module, inband_static_part,
                                           subnet, switch)
    else:
        switch_ip = inband_static_part + str(1) + '.' + str(1)
        # Join existing fabric.
        if 'Already' in join_fabric(module, switch_ip):
            output += ' %s: Already part of fabric %s \n' % (switch,
                                                             fabric_name)
        else:
            output += ' %s: Joined fabric %s \n' % (switch, fabric_name)
            CHANGED_FLAG.append(True)

    return output


def find_clustered_switches(module):
    """
    Method to find clustered switches from the input csv file.
    :param module: The Ansible module to fetch input parameters.
    :return: It returns a dict whose first value is list of pairs of cluster
    and second is list of switches in cluster.
    """
    csv_data = module.params['pn_csv_data']
    csv_data = csv_data.replace(' ', '')
    csv_data = csv_data.split('\n')
    cluster_dict_info = {}
    cluster_list = []
    cluster_switches = []

    for line in csv_data:
        if line != '':
            line = line.split(',')
            cluster_node_1 = line[2]
            cluster_node_2 = line[3]

            if not cluster_node_2.isdigit():
                temp_list = [cluster_node_1, cluster_node_2]
                if temp_list not in cluster_list:
                    cluster_switches.append(cluster_node_1)
                    cluster_switches.append(cluster_node_2)
                    cluster_list.append(temp_list)

    cluster_dict_info[0] = cluster_list
    cluster_dict_info[1] = cluster_switches

    return cluster_dict_info


def fabric_inband_net_create(module, inband_static_part, subnet, switch):
    """
    Method to create fabric in-band network.
    :param module: The Ansible module to fetch input parameters.
    :param inband_static_part: In-band ip address till second octet.
    :param subnet: Subnet mask of in-band ip address.
    :param switch: Name of the 1st switch in the DC.
    :return: String describing if fabric in-band network got created or not.
    """
    global CHANGED_FLAG
    output = ''
    leaf_list = module.params['pn_leaf_list']
    cli = pn_cli(module)
    clicopy = cli

    for leaf in leaf_list:
        switch_position = leaf_list.index(leaf) + 1
        inband_network_ip = inband_static_part + str(switch_position) + '.'
        inband_network_ip += str(switch_position)

        cli = clicopy
        cli += 'fabric-in-band-network-show format network no-show-headers'
        existing_networks = run_cli(module, cli).split()

        if inband_network_ip not in existing_networks:
            cli = clicopy
            cli += 'fabric-in-band-network-create network ' + inband_network_ip
            cli += ' netmask ' + subnet
            if 'Success' in run_cli(module, cli):
                output += ' %s: Fabric in-band network created for %s \n' % (
                    switch, inband_network_ip
                )
                CHANGED_FLAG.append(True)
        else:
            output += ' %s: Fabric in-band network %s already exists \n' % (
                switch, inband_network_ip
            )

    return output


def join_fabric(module, switch_ip):
    """
    Method to join existing fabric by pointing to in-band ip of first switch.
    :param module: The Ansible module to fetch input parameters.
    :param switch_ip: In-band ip of the first/originator switch.
    :return: The output of run_cli() method.
    """
    cli = pn_cli(module)
    clicopy = cli

    cli += ' fabric-info format name no-show-headers'
    cli = shlex.split(cli)
    out, err = module.run_command(cli)[1:]

    if err:
        cli = clicopy
        cli += ' fabric-join switch-ip %s ' % switch_ip
    elif out:
        return ' Already in a fabric \n'

    return run_cli(module, cli)


def create_vrouter(module, switch, bgp_as, router_id, bgp_nic_ip,
                   bgp_nic_l3_port, neighbor_ip, remote_as, in_band_nic_ip,
                   in_band_nic_netmask, fabric_network_address):
    """
    Method to create vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the current switch.
    :param bgp_as: BGP AS value of this switch.
    :param router_id: Router id to be assigned to this vrouter.
    :param bgp_nic_ip: Bgp_nic_ip for the vrouter creation.
    :param bgp_nic_l3_port: L3 port number connected to neighbor switch.
    :param neighbor_ip: Ip of the BGP neighbor node.
    :param remote_as: BGP AS value of the neighbor node.
    :param in_band_nic_ip: In-band nic ip of this switch.
    :param in_band_nic_netmask: Netmask of in-band nic ip.
    :param fabric_network_address: Fabric network address of the existing fabric
    :return: String describing if vrouter got created or if it already exists.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    clicopy = cli

    cli += ' vrouter-show format name no-show-headers '
    existing_vrouter_names = run_cli(module, cli).split()
    if vrouter_name not in existing_vrouter_names:
        cli = clicopy
        cli += ' fabric-comm-vrouter-bgp-create name %s ' % vrouter_name
        cli += ' bgp-as %s router-id %s ' % (bgp_as, router_id)
        cli += ' bgp-nic-ip %s ' % bgp_nic_ip
        cli += ' bgp-nic-l3-port %s ' % bgp_nic_l3_port
        cli += ' neighbor %s remote-as %s ' % (neighbor_ip, remote_as)
        cli += ' bfd in-band-nic-ip %s ' % in_band_nic_ip
        cli += ' in-band-nic-netmask %s ' % in_band_nic_netmask
        cli += ' fabric-network %s ' % fabric_network_address
        cli += ' allowas-in '
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Created %s \n' % (switch, vrouter_name)

    return ' %s: %s already exists \n' % (switch, vrouter_name)


def get_l3_port(module, neighbor_name):
    """
    Method to get l3 port number which is connected to given neighbor.
    :param module: The Ansible module to fetch input parameters.
    :param neighbor_name: Name of the bgp neighbor host.
    :return: l3 port number.
    """
    cli = pn_cli(module)
    cli += 'port-show hostname %s format port no-show-headers' % (
        neighbor_name
    )
    ports = run_cli(module, cli).split()

    cli = pn_cli(module)
    cli += 'trunk-show ports %s format trunk-id no-show-headers ' % (
        ports[0]
    )
    trunk_id = run_cli(module, cli)

    if len(trunk_id) == 0 or trunk_id == 'Success':
        return ports[0]

    return trunk_id


def configure_loopback_interface(module, switch, router_id):
    """
    Method to configure looack interface on a vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param router_id: Router id which is same as loopback ip.
    :return: String describing if loopback interface got configured or not
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-loopback-interface-show vrouter-name %s ' % vrouter_name
    cli += ' format ip no-show-headers '
    existing_ip = run_cli(module, cli)

    if router_id not in existing_ip:
        cli = clicopy
        cli += ' vrouter-loopback-interface-add vrouter-name %s ' % vrouter_name
        cli += ' ip %s ' % router_id
        run_cli(module, cli)

        cli = clicopy
        cli += ' vrouter-bgp-network-add vrouter-name %s ' % vrouter_name
        cli += ' network %s netmask 255.255.255.255 ' % router_id
        run_cli(module, cli)

        CHANGED_FLAG.append(True)
        return ' %s: Configured loopback interface with ip %s \n' % (switch,
                                                                     router_id)
    return ' %s: Loopback interface %s has been already configured \n' % (
        switch, router_id
    )


def configure_ebgp_connections(module, switch, third_party_data, bgp_nic_ip):
    """
    Method to configure eBGP connection to remaining third party neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param third_party_data: Third party BGP data in csv format.
    :param bgp_nic_ip: Ip of first bgp neighbor added.
    :return: String describing eBGP configuration.
    """
    global CHANGED_FLAG
    output = ''
    vrouter_name = switch + '-vrouter'
    skip_flag = False
    address = bgp_nic_ip.split('.')
    bgp_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    bgp_static_part += str(address[2]) + '.'
    bgp_last_octet = str(address[3]).split('/')
    bgp_subnet = bgp_last_octet[1]

    for row in third_party_data:
        row = row.split(',')
        if not skip_flag and row[4] == switch:
            skip_flag = True
            continue

        if skip_flag and row[4] == switch:
            neighbor_name = row[0]
            neighbor_ip = row[1]
            remote_as = row[2]

            address = neighbor_ip.split('.')
            static_part = str(address[0]) + '.' + str(address[1]) + '.'
            static_part += str(address[2]) + '.'
            last_octet = str(int(address[3]) - 1)
            ip = static_part + last_octet + '/' + bgp_subnet

            l3_port = get_l3_port(module, neighbor_name)

            cli = pn_cli(module)
            clicopy = cli
            cli += ' vrouter-interface-show vrouter-name %s ' % vrouter_name
            cli += ' format ip no-show-headers '
            exisiting_ip = run_cli(module, cli).split()

            if ip not in exisiting_ip:
                cli = clicopy
                cli += ' vrouter-interface-add vrouter-name %s ' % vrouter_name
                cli += ' l3-port %s ip %s ' % (l3_port, ip)
                run_cli(module, cli)
                output += ' %s: Added vrouter interface %s \n' % (switch, ip)
            else:
                output += ' %s: Vrouter interface %s already added \n' % (
                    switch, ip
                )

            cli = clicopy
            cli += ' vrouter-bgp-show vrouter-name %s ' % vrouter_name
            cli += ' format neighbor no-show-headers '
            exisiting_neighbor = run_cli(module, cli).split()

            if neighbor_ip not in exisiting_neighbor:
                cli = clicopy
                cli += ' vrouter-bgp-add vrouter-name %s ' % vrouter_name
                cli += ' neighbor %s remote-as %s bfd ' % (neighbor_ip,
                                                           remote_as)
                cli += ' allowas-in '
                run_cli(module, cli)
                output += ' %s: Added eBGP neighbor %s \n' % (switch,
                                                              neighbor_ip)

                cli = clicopy
                cli += ' vrouter-modify name %s ' % vrouter_name
                cli += ' bgp-max-paths %s ' % module.params['pn_bgp_max_path']
                cli += ' bgp-bestpath-as-path multipath-relax '
                run_cli(module, cli)
            else:
                output += ' %s: eBGP neighbor %s already added \n' % (
                    switch, neighbor_ip
                )

    return output


def create_vlan(module, vlan_id, switch, scope):
    """
    Method to create local vlan.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to create.
    :param switch: Name of the switch.
    :param scope: Scope of the vlan to create.
    :return: String describing vlan creation details.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s vlan-show format id no-show-headers ' % switch
    existing_vlan_ids = run_cli(module, cli).split()
    existing_vlan_ids = list(set(existing_vlan_ids))

    if vlan_id not in existing_vlan_ids:
        cli = clicopy
        cli += ' switch %s vlan-create id %s scope %s ' % (switch, vlan_id,
                                                           scope)
        run_cli(module, cli)
        CHANGED_FLAG.append(True)

        return ' %s: Vlan id %s with scope %s created \n' % (
            switch, vlan_id, scope
        )

    return ' %s: Vlan id %s with scope %s already exists \n' % (
        switch, vlan_id, scope
    )


def configure_ibgp_connection(module, switch, local_ip, remote_ip, remote_as):
    """
    Method to configure iBGP connection between cluster members.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param local_ip: Vrouter interface ip of local switch.
    :param remote_ip: Vrouter interface ip of remote switch.
    :param remote_as: Remote-as value of cluster.
    :return: String describing details of iBGP configuration made.
    """
    global CHANGED_FLAG
    output = ''
    vrouter_name = switch + '-vrouter'
    vlan_id = module.params['pn_ibgp_vlan']
    cli = pn_cli(module)
    clicopy = cli

    cli += ' switch %s vrouter-interface-show vrouter-name %s ' % (switch,
                                                                   vrouter_name)
    cli += ' format ip no-show-headers '
    exisiting_ip = run_cli(module, cli).split()

    if local_ip not in exisiting_ip:
        cli = clicopy
        cli += ' switch %s vrouter-interface-add vrouter-name %s ' % (
            switch, vrouter_name
        )
        cli += ' ip %s vlan %s ' % (local_ip, vlan_id)
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, local_ip, vrouter_name
        )
        CHANGED_FLAG.append(True)
    else:
        output += ' %s: iBGP interface %s already added \n' % (switch, local_ip)

    remote_ip = remote_ip.split('/')[0]
    cli = clicopy
    cli += ' switch %s vrouter-bgp-show vrouter-name %s ' % (switch,
                                                             vrouter_name)
    cli += ' format neighbor no-show-headers '
    exisiting_neighbor = run_cli(module, cli).split()

    if remote_ip not in exisiting_neighbor:
        cli = clicopy
        cli += ' switch %s vrouter-bgp-add vrouter-name %s ' % (switch,
                                                                vrouter_name)
        cli += ' neighbor %s remote-as %s next-hop-self bfd ' % (remote_ip,
                                                                 remote_as)
        run_cli(module, cli)
        output += ' %s: Added iBGP neighbor %s for %s \n' % (switch, remote_ip,
                                                             vrouter_name)
        CHANGED_FLAG.append(True)
    else:
        output += ' %s: iBGP neighbor %s already added \n' % (switch, remote_ip)

    return output


def create_cluster(module, name, cluster_list):
    """
    Method to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param name: The name of the cluster to create.
    :param cluster_list: List of cluster switches.
    :return: String describing if cluster got created or if it already exists.
    """
    global CHANGED_FLAG
    cluster_node1 = cluster_list[0]
    cluster_node2 = cluster_list[1]

    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % (
        cluster_node1)
    existing_clusters = run_cli(module, cli).split()
    if name not in existing_clusters:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (cluster_node1, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (cluster_node1,
                                                          cluster_node2)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: %s created successfully \n' % (cluster_node1, name)
    else:
        return ' %s: %s already exists \n' % (cluster_node1, name)


def modify_vrouter(module, switch, vrrp_id):
    """
    Method to add vrrp id to a vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the switch.
    :param vrrp_id: vrrp id to be assigned to vrouter.
    :return: String describing if vrrp id got assigned or not.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-show name %s format hw-vrrp-id ' % vrouter_name
    cli += ' no-show-headers '
    existing_vrrp_id = run_cli(module, cli).split()

    if vrrp_id not in existing_vrrp_id:
        cli = clicopy
        cli += ' switch %s vrouter-modify name %s ' % (switch, vrouter_name)
        cli += ' hw-vrrp-id %s ' % vrrp_id
        run_cli(module, cli)
        return ' %s: Assigned vrrp_id %s to %s \n' % (switch, vrrp_id,
                                                      vrouter_name)

    return ' %s: Vrrp-id %s already assigned to %s \n' % (switch, vrrp_id,
                                                          vrouter_name)


def create_vrouter_interface(module, switch, vrrp_ip, vlan_id, vrrp_id,
                             ip_count, vrrp_priority):
    """
    Method to add vrouter interface and assign IP to it along with
    vrrp_id and vrrp_priority.
    :param module: The Ansible module to fetch input parameters.
    :param switch: The switch name on which interfaces will be created.
    :param vrrp_ip: IP address to be assigned to vrouter interface.
    :param vlan_id: vlan_id to be assigned.
    :param vrrp_id: vrrp_id to be assigned.
    :param vrrp_priority: priority to be given(110 for active switch).
    :param ip_count: The value of fourth octet in the ip.
    :return: String describing if vrouter interface got added or not.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'
    ip_addr = vrrp_ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    vip = static_ip + '1' + '/' + subnet
    interface_ip = static_ip + ip_count + '/' + subnet

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vlan %s ip %s ' % (vlan_id, interface_ip)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' switch %s vrouter-interface-add vrouter-name %s ' % (
            switch, vrouter_name
        )
        cli += ' ip ' + interface_ip
        cli += ' vlan %s if data ' % vlan_id
        run_cli(module, cli)
        output = ' %s: Added vrouter interface with ip %s to %s \n' % (
            switch, interface_ip, vrouter_name
        )
        CHANGED_FLAG.append(True)
    else:
        output = ' %s: Vrouter interface %s already exists for %s \n' % (
            switch, interface_ip, vrouter_name
        )

    cli = clicopy
    cli += ' vrouter-interface-show vrouter-name %s ip %s vlan %s ' % (
        vrouter_name, interface_ip, vlan_id
    )
    cli += ' format nic no-show-headers '
    eth_port = run_cli(module, cli).split()
    eth_port.remove(vrouter_name)

    cli = clicopy
    cli += ' vrouter-interface-show vlan %s ip %s vrrp-primary %s ' % (
        vlan_id, vip, eth_port[0]
    )
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' switch %s vrouter-interface-add vrouter-name %s ' % (
            switch, vrouter_name
        )
        cli += ' ip ' + vip
        cli += ' vlan %s if data vrrp-id %s ' % (vlan_id, vrrp_id)
        cli += ' vrrp-primary %s vrrp-priority %s ' % (eth_port[0],
                                                       vrrp_priority)
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s to %s \n' % (
            switch, vip, vrouter_name
        )
        CHANGED_FLAG.append(True)

    else:
        output += ' %s: Vrouter interface %s already exists for %s \n' % (
            switch, vip, vrouter_name
        )

    return output


def add_vrouter_interface_for_non_cluster_switch(module, vrrp_ip, switch,
                                                 vlan_id):
    """
    Method to add vrouter interface for non clustered switches.
    :param module: The Ansible module to fetch input parameters.
    :param vrrp_ip: Vrouter interface ip to be added.
    :param switch: Name of non clustered switch.
    :param vlan_id: vlan id.
    :return: String describing if vrouter interface got added or not.
    """
    global CHANGED_FLAG
    vrouter_name = switch + '-vrouter'

    ip_addr = vrrp_ip.split('.')
    fourth_octet = ip_addr[3].split('/')
    subnet = fourth_octet[1]

    static_ip = ip_addr[0] + '.' + ip_addr[1] + '.' + ip_addr[2] + '.'
    gateway_ip = static_ip + '1' + '/' + subnet

    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show ip %s vlan %s ' % (gateway_ip, vlan_id)
    cli += ' format switch no-show-headers '
    existing_vrouter = run_cli(module, cli).split()
    existing_vrouter = list(set(existing_vrouter))

    if vrouter_name not in existing_vrouter:
        cli = clicopy
        cli += ' switch %s vrouter-interface-add vrouter-name %s ' % (
            switch, vrouter_name
        )
        cli += ' vlan ' + vlan_id
        cli += ' ip ' + gateway_ip
        run_cli(module, cli)
        CHANGED_FLAG.append(True)
        return ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch, gateway_ip, vrouter_name
        )

    return ' %s: Vrouter interface %s already exists on %s \n' % (
        switch, gateway_ip, vrouter_name
    )


def configure_vrrp(module):
    """
    Method to configure VRRP L3.
    :param module: The Ansible module to fetch input parameters.
    :return: Output string of configuration.
    """
    output = ''
    csv_data = module.params['pn_csv_data']
    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.split('\n')

    # Parse csv file data and configure VRRP.
    for row in csv_data_list:
        elements = row.split(',')
        cluster_list = []
        vlan_id = elements[0]
        vrrp_ip = elements[1]
        cluster_node1 = str(elements[2])
        if len(elements) > 5:
            # Configure VRRP for clustered switches
            cluster_node2 = str(elements[3])
            vrrp_id = elements[4]
            active_switch = str(elements[5])
            cluster_list.append(cluster_node1)
            cluster_list.append(cluster_node2)
            cluster_name = cluster_node1 + '-to-' + cluster_node2 + '-cluster'
            host_count = 1

            # Create a cluster and vlan with scope cluster
            output += create_cluster(module, cluster_name, cluster_list)
            output += create_vlan(module, vlan_id, cluster_node1, 'cluster')

            for switch in cluster_list:
                output += modify_vrouter(module, switch, vrrp_id)
                host_count += 1
                vrrp_priority = '110' if switch == active_switch else '100'
                output += create_vrouter_interface(module, switch, vrrp_ip,
                                                   vlan_id, vrrp_id,
                                                   str(host_count),
                                                   vrrp_priority)
        else:
            # Configure VRRP for non clustered switches.
            output += create_vlan(module, vlan_id, cluster_node1, 'local')
            output += add_vrouter_interface_for_non_cluster_switch(
                module, vrrp_ip, cluster_node1, vlan_id)

    return output


def add_vxlan_to_vlan(module, vlan_id, vxlan, switch):
    """
    Method to add vxlan mapping to vlan.
    :param module: The Ansible module to fetch input parameters.
    :param vlan_id: vlan id to be modified.
    :param vxlan: vxlan id to be assigned to vlan.
    :param switch: Name of the switch on which vlan is present.
    :return: String describing if vxlan for added or not.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' switch %s vlan-show id %s format vxlan ' % (switch, vlan_id)
    cli += ' no-show-headers '
    existing_vxlan = run_cli(module, cli).split()

    if vxlan not in existing_vxlan:
        cli = pn_cli(module)
        cli += ' switch %s vlan-modify id %s vxlan %s ' % (switch, vlan_id,
                                                           vxlan)
        run_cli(module, cli)
        return ' %s: Added vxlan %s to vlan %s \n' % (switch, vxlan, vlan_id)

    return ' %s: Vxlan %s has been added to vlan %s \n' % (switch, vxlan,
                                                           vlan_id)


def get_vrouter_interface_ip(module, switch, vlan):
    """
    Method to get vrouter interface ip to be used as local ip.
    :param module: The Ansible module to fetch input parameters.
    :param switch: Name of the local switch.
    :param vlan: Vlan id for which to find vrouter interface ip.
    :return: Vrouter interface ip.
    """
    vrouter_name = switch + '-vrouter'
    cli = pn_cli(module)
    cli += ' switch %s vrouter-interface-show vrouter-name %s ' % (switch,
                                                                   vrouter_name)
    cli += ' vlan %s format ip no-show-headers ' % vlan
    output = run_cli(module, cli).split()
    output = list(set(output))
    output.remove(vrouter_name)
    address = output[0].split('.')
    ip = address[0] + '.' + address[1] + '.'
    ip += address[2] + '.' + str(1)
    return ip


def create_tunnel(module, local_switch, tunnel_name, scope, local_ip, remote_ip,
                  peer_switch=None):
    """
    Method to create tunnel to carry vxlan traffic.
    :param module: The Ansible module to fetch input parameters.
    :param local_switch: Name of the switch on which tunnel will be created.
    :param tunnel_name: Name of the tunnel to create.
    :param scope: Scope of the tunnel to create.
    :param local_ip: Local vrouter interface ip.
    :param remote_ip: Remote vrouter interface ip.
    :param peer_switch: Name of the peer clustered switch. In case of
    unclustered switch, this will be None.
    :return: String describing if tunnel got created or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' switch %s tunnel-show format name no-show-headers ' % local_switch
    existing_tunnels = run_cli(module, cli).split()

    if tunnel_name not in existing_tunnels:
        cli = pn_cli(module)
        cli += ' switch %s tunnel-create name %s scope %s ' % (local_switch,
                                                               tunnel_name,
                                                               scope)
        cli += ' local-ip %s remote-ip %s ' % (local_ip, remote_ip)
        cli += ' vrouter-name %s ' % (local_switch + '-vrouter')

        if peer_switch is not None:
            cli += ' peer-vrouter-name %s ' % (peer_switch + '-vrouter')

        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: %s created successfully \n ' % (local_switch,
                                                         tunnel_name)
        else:
            return ' %s: Could not create %s \n' % (local_switch, tunnel_name)

    return ' %s: %s already exists \n' % (local_switch, tunnel_name)


def add_vxlan_to_tunnel(module, vxlan, tunnel_name, switch):
    """
    Method to add vxlan to created tunnel so that it can carry vxlan traffic.
    :param module: The Ansible module to fetch input parameters.
    :param vxlan: vxlan id to add to tunnel.
    :param tunnel_name: Name of the tunnel on which vxlan will be added.
    :param switch: Name of the switch on which tunnel exists.
    :return: String describing if vxlan got added to tunnel or not.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    cli += ' switch %s tunnel-vxlan-show format switch no-show-headers ' % (
        switch)
    existing_tunnel_vxlans = run_cli(module, cli).split()

    if tunnel_name not in existing_tunnel_vxlans:
        cli = pn_cli(module)
        cli += ' switch %s tunnel-vxlan-add name %s vxlan %s ' % (switch,
                                                                  tunnel_name,
                                                                  vxlan)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Added vxlan %s to %s \n' % (switch, vxlan, tunnel_name)

        return ' %s: Could not add vxlan %s to %s \n' % (switch, vxlan,
                                                         tunnel_name)

    return ' %s: vxlan %s already added to %s \n' % (switch, vxlan,
                                                     tunnel_name)


def configure_vxlan(module):
    """
    Method to configure vxlan.
    :param module: The Ansible module to fetch input parameters.
    :return: Output string of configuration.
    """
    output = ''
    vxlan_switches_list = []
    csv_data = module.params['pn_csv_data']
    csv_data = csv_data.replace(" ", "")
    csv_data_list = csv_data.split('\n')

    for row in csv_data_list:
        elements = row.split(',')
        vlan_id = elements[0]
        leaf_switch_1 = elements[2]
        if len(elements) == 7:
            leaf_switch_2 = elements[3]
            vxlan_id = elements[6]
            vxlan_switches_list.append([leaf_switch_1, leaf_switch_2, vlan_id])
            output += add_vxlan_to_vlan(module, vlan_id, vxlan_id,
                                        leaf_switch_1)
            output += add_vxlan_to_vlan(module, vlan_id, vxlan_id,
                                        leaf_switch_2)
        elif len(elements) == 4:
            vxlan_id = elements[3]
            vxlan_switches_list.append([leaf_switch_1, vlan_id])
            output += add_vxlan_to_vlan(module, vlan_id, vxlan_id,
                                        leaf_switch_1)

    for row in csv_data_list:
        elements = row.split(',')
        vlan_id = elements[0]
        leaf_switch_1 = elements[2]

        if len(elements) == 7 or len(elements) == 4:
            if len(elements) == 7:
                leaf_switch_2 = elements[3]
                vxlan_id = elements[6]
                cluster = [leaf_switch_1, leaf_switch_2, vlan_id]
                scope = 'cluster'
            else:
                leaf_switch_2 = None
                vxlan_id = elements[3]
                cluster = [leaf_switch_1, vlan_id]
                scope = 'local'

            for switches in vxlan_switches_list:
                if switches == cluster:
                    continue
                else:
                    tunnel_name = leaf_switch_1 + '-' + switches[0] + '-tunnel'
                    local_ip = get_vrouter_interface_ip(module, leaf_switch_1,
                                                        vlan_id)
                    if len(switches) == 3:
                        remote_vlan = switches[2]
                    else:
                        remote_vlan = switches[1]

                    remote_ip = get_vrouter_interface_ip(module, switches[0],
                                                         remote_vlan)

                    output += create_tunnel(module, leaf_switch_1, tunnel_name,
                                            scope, local_ip, remote_ip,
                                            leaf_switch_2)

                    output += add_vxlan_to_tunnel(module, vxlan_id, tunnel_name,
                                                  leaf_switch_1)

    return output


def configure_ibgp_vrrp_vxlan(module):
    """
    Method to configure iBGP, VRRP and Vxlan for DCI.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing details of all configurations.
    """
    global CHANGED_FLAG
    output = ''
    cluster_dict_info = find_clustered_switches(module)
    cluster_list = cluster_dict_info[0]

    # Configure iBGP connection between clusters
    for cluster in cluster_list:
        cluster_node1 = cluster[0]
        cluster_node2 = cluster[1]
        vlan_id = module.params['pn_ibgp_vlan']
        vlan_scope = 'local'
        ibgp_ip_range = module.params['pn_ibgp_ip_range']
        subnet_count = 0

        # Create local vlans on both cluster nodes.
        output += create_vlan(module, vlan_id, cluster_node1, vlan_scope)
        output += create_vlan(module, vlan_id, cluster_node2, vlan_scope)

        address = ibgp_ip_range.split('.')
        static_part = str(address[0]) + '.' + str(address[1]) + '.'
        static_part += str(address[2]) + '.'
        last_octet = str(address[3]).split('/')
        subnet = last_octet[1]

        ip_count = subnet_count * 4
        node1_ip = static_part + str(ip_count + 1) + '/' + subnet
        node2_ip = static_part + str(ip_count + 2) + '/' + subnet
        subnet_count += 1

        # Get the bgp-as values of cluster nodes.
        third_party_data = module.params['pn_third_party_bgp_data'].replace(' ',
                                                                            '')
        third_party_data = third_party_data.split('\n')
        for row in third_party_data:
            row = row.split(',')
            if row[4] == cluster_node1 or row[4] == cluster_node2:
                bgp_as = row[3]
                break

        # Configure iBGP connection.
        output += configure_ibgp_connection(module, cluster_node1, node1_ip,
                                            node2_ip, bgp_as)

        output += configure_ibgp_connection(module, cluster_node2, node2_ip,
                                            node1_ip, bgp_as)

    # Configure VRRP to be used for VTEP HA
    output += configure_vrrp(module)

    # Configure vxlan tunnels
    output += configure_vxlan(module)

    return output


def implement_dci(module):
    """
    Method to implement initial DCI setup: fabric creation/join and eBGP.
    :param module: The Ansible module to fetch input parameters.
    :return: String describing details of DCI implementation.
    """
    global CHANGED_FLAG
    output = ''
    current_switch = module.params['pn_current_switch']
    bgp_ip = module.params['pn_bgp_ip']
    leaf_list = module.params['pn_leaf_list']
    loopback_ip = module.params['pn_loopback_ip']
    third_party_data = module.params['pn_third_party_bgp_data'].replace(' ', '')
    third_party_data = third_party_data.split('\n')

    address = bgp_ip.split('.')
    bgp_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    bgp_static_part += str(address[2]) + '.'
    bgp_last_octet = str(address[3]).split('/')
    bgp_subnet = bgp_last_octet[1]

    address = loopback_ip.split('.')
    loopback_static_part = str(address[0]) + '.' + str(address[1]) + '.'

    # Calculate router-id to be assigned to vrouter.
    switch_index = leaf_list.index(current_switch)
    router_count = switch_index + 1
    router_id = loopback_static_part + str(router_count) + '.'
    router_id += str(router_count)

    # Calculate in-band-nic-ip and in-band-nic-netmask for vrouter creation.
    cli = pn_cli(module)
    cli += ' switch-setup-show format in-band-ip no-show-headers '
    inband_ip = run_cli(module, cli)
    address = inband_ip.split(':')[1]
    address = address.replace(' ', '')
    address = address.split('.')
    inband_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    inband_static_part += str(address[2]) + '.'
    inband_last_octet = str(address[3]).split('/')
    inband_nic_ip = inband_static_part + str(int(inband_last_octet[0]) + 1)
    inband_nic_netmask = inband_last_octet[1]

    # Get the neighbor ip and remote-as value of the first neighbor
    # Third party csv format: (third party switch name, neighbor-ip,
    # bgp-as of third party switch, remote-as, neighbor switch name)
    neighbor_name, neighbor_ip, remote_as, bgp_as = None, None, None, None
    for row in third_party_data:
        row = row.split(',')
        if row[4] == current_switch:
            neighbor_name = row[0]
            neighbor_ip = row[1]
            remote_as = row[2]
            bgp_as = row[3]
            break

    if neighbor_name is None or neighbor_ip is None or remote_as is None:
        return ' %s: Could not find remote bgp data \n' % current_switch

    # Calculate bgp-nic-l3-port number connected to first neighbor
    bgp_nic_l3_port = get_l3_port(module, neighbor_name)

    # Calculate fabric-network address
    fabric_network_address = str(address[0]) + '.' + str(address[1]) + '.'
    fabric_network_address += str(1) + '.' + str(0) + '/'
    fabric_network_address += inband_nic_netmask

    address = neighbor_ip.split('.')
    n_static_part = str(address[0]) + '.' + str(address[1]) + '.'
    n_static_part += str(address[2]) + '.'
    n_last_octet = str(int(address[3]) - 1)
    bgp_nic_ip = n_static_part + n_last_octet + '/' + bgp_subnet

    # Create and configure vrouter on this switch.
    output += create_vrouter(module, current_switch, bgp_as, router_id,
                             bgp_nic_ip, bgp_nic_l3_port, neighbor_ip,
                             remote_as, inband_nic_ip, inband_nic_netmask,
                             fabric_network_address)

    # Configure other eBGP connection to third party switches
    output += configure_ebgp_connections(module, current_switch,
                                         third_party_data, bgp_nic_ip)

    # Configure loopback interface for debugging purpose.
    output += configure_loopback_interface(module, current_switch, router_id)

    # Create a switch routes to all other switches
    if switch_index != 0:
        create_switch_routes(module, inband_ip)
        time.sleep(10)

    # Configure fabric
    output += configure_fabric(module, current_switch)

    return output


def toggle_40g_local(module):
    """
    Method to toggle 40g ports to 10g ports.
    :param module: The Ansible module to fetch input parameters.
    :return: The output messages for assignment.
    """
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    cli += ' lldp-show format local-port no-show-headers '
    local_ports = run_cli(module, cli).split()

    cli = clicopy
    cli += ' port-config-show speed 40g '
    cli += ' format port no-show-headers '
    ports_40g = run_cli(module, cli)
    if len(ports_40g) > 0 and ports_40g != 'Success':
        ports_40g = ports_40g.split()
        ports_to_modify = list(set(ports_40g) - set(local_ports))

        for port in ports_to_modify:
            next_port = str(int(port) + 1)
            cli = clicopy
            cli += ' port-show port %s format bezel-port' % next_port
            cli += ' no-show-headers'
            bezel_port = run_cli(module, cli).split()[0]

            if '.2' in bezel_port:
                end_port = int(port) + 3
                range_port = port + '-' + str(end_port)

                cli = clicopy
                cli += ' port-config-modify port %s ' % port
                cli += ' disable '
                output += 'port ' + port + ' disabled'
                output += run_cli(module, cli)

                cli = clicopy
                cli += ' port-config-modify port %s ' % port
                cli += ' speed 10g '
                output += 'port ' + port + ' converted to 10g'
                output += run_cli(module, cli)

                cli = clicopy
                cli += ' port-config-modify port %s ' % range_port
                cli += ' enable '
                output += 'port range_port ' + range_port + '  enabled'
                output += run_cli(module, cli)

        time.sleep(10)

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_fabric_name=dict(required=False, type='str'),
            pn_run_initial_setup=dict(required=True, type='bool'),
            pn_current_switch=dict(required=False, type='str'),
            pn_spine_list=dict(required=True, type='list'),
            pn_leaf_list=dict(required=True, type='list'),
            pn_inband_ip=dict(required=False, type='str',
                              default='172.16.0.0/24'),
            pn_loopback_ip=dict(required=False, type='str',
                                default='109.109.109.0/24'),
            pn_bgp_ip=dict(required=False, type='str', default='100.1.1.0/24'),
            pn_bgp_redistribute=dict(required=False, type='str',
                                     default='connected'),
            pn_bgp_max_path=dict(required=False, type='str', default='16'),
            pn_ibgp_vlan=dict(required=False, type='str', default='4040'),
            pn_ibgp_ip_range=dict(required=False, type='str',
                                  default='75.75.75.0/30'),
            pn_csv_data=dict(required=False, type='str'),
            pn_third_party_bgp_data=dict(required=False, type='str'),
        )
    )

    current_switch = module.params['pn_current_switch']
    message = ''
    global CHANGED_FLAG

    if module.params['pn_run_initial_setup']:
        # Auto accept EULA
        if 'Setup completed successfully' in auto_accept_eula(module):
            message += ' %s: EULA accepted \n' % current_switch
            CHANGED_FLAG.append(True)
        else:
            message += ' %s: EULA has already been accepted \n' % current_switch

        # Update switch names to match host names from hosts file
        if 'Updated' in update_switch_names(module, current_switch):
            CHANGED_FLAG.append(True)

        # Toggle 40g ports to 10g
        if toggle_40g_local(module):
            message += ' %s: Toggled 40G ports to 10G \n' % current_switch
            CHANGED_FLAG.append(True)

        # Assign in-band ip
        message += assign_inband_ip(module)

        # Implement Data Center Interconnect
        message += implement_dci(module)
    else:
        # Configure iBGP, VRRP and vxlan
        message += configure_ibgp_vrrp_vxlan(module)

    # Exit the module and return the required JSON
    module.exit_json(
        stdout=message,
        error='0',
        failed=False,
        changed=True if True in CHANGED_FLAG else False
    )


if __name__ == '__main__':
    main()
