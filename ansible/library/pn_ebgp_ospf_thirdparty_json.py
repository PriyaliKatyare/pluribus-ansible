#!/usr/bin/python
""" PN CLI EBGP/OSPF with 3rd party spine switches """

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

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_ebgp_ospf_third_party
author: 'Pluribus Networks (devops@pluribusnetworks.com)'
short_description: Module to configure eBGP/OSPF with 3rd party spine switches.
description: It performs following steps:
    EBGP:
      - Assigning bgp_as
      - Configuring bgp_redistribute
      - Configuring bgp_maxpath
      - Assign ebgp_neighbor
      - Assign router_id
      - Create leaf_cluster
      - Add iBGP neighbor for clustered leaf
    OSPF:
      - Find area_id for leafs
      - Assign ospf_neighbor for leaf cluster
      - Assign ospf_neighbor
      - Assign ospf_redistribute
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
    pn_leaf_list:
      description:
        - Specify list of leaf hosts
      required: False
      type: list
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
    pn_bgp_as_range:
      description:
        - Specify bgp_as_range value to be added to vrouter.
      required: False
      type: str
      default: '65000'
    pn_routing_protocol:
      description:
        - Specify which routing protocol to specify.
      required: False
      type: str
      choices: ['ebgp', 'ospf']
    pn_ibgp_ip_range:
      description:
        - Specify ip range for ibgp interface.
      required: False
      type: str
      default: '75.75.75.0/30'
    pn_ibgp_vlan:
      description:
        - Specify vlan for ibgp interface.
      required: False
      type: str
      default: '4040'
    pn_bfd:
      description:
        - Specify bfd flag for the ebgp neighbor.
      required: False
      type: bool
      default: False
    pn_ospf_area_id:
      description:
        - Specify area_id value to be added to vrouter for ospf.
      required: False
      type: str
      default: '0'
"""

EXAMPLES = """
- name: Configure eBGP/OSPF with 3rd party spine switches
  pn_ebgp_ospf_third_party:
    pn_cliusername: "{{ USERNAME }}"
    pn_clipassword: "{{ PASSWORD }}"
    pn_leaf_list: "{{ groups['leaf'] }}"
"""

RETURN = """
summary:
  description: It contains output of each configuration along with switch name.
  returned: always
  type: str
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
unreachable:
  description: Indicates whether switch was unreachable to connect.
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
    rc, out, err = module.run_command(cli)
    results = []
    if out:
        return out

    if err:
        json_msg = {
            'switch': '',
            'output': u'Operation Failed: {}'.format(' '.join(cli))
        }
        results.append(json_msg)
        module.exit_json(
            unreachable=False,
            failed=True,
            exception=err.strip(),
            summary=results,
            task='Configure eBGP/OSPF with existing spine switches',
            msg='eBGP/OSPF configuration failed',
            changed=False
        )
    else:
        return 'Success'


def find_bgp_as_dict(module):
    """
    Method to find bgp-as for all switches and store it in a dictionary.
    :param module: The Ansible module to fetch input parameters.
    :return: Dictionary containing switch: bgp_as key value pairs.
    """
    leaf_list = module.params['pn_leaf_list']
    bgp_as = int(module.params['pn_bgp_as_range'])
    cluster_leaf_list = []
    cli = pn_cli(module)
    clicopy = cli
    dict_bgp_as = {}

    cli += ' cluster-show format name no-show-headers'
    cluster_list = run_cli(module, cli).split()

    if 'Success' not in cluster_list:
        for cluster in cluster_list:
            cli = clicopy
            cli += ' cluster-show name %s' % cluster
            cli += ' format cluster-node-1,cluster-node-2 no-show-headers'
            cluster_nodes = run_cli(module, cli).split()

            if cluster_nodes[0] in leaf_list and cluster_nodes[1] in leaf_list:
                bgp_as += 1
                dict_bgp_as[cluster_nodes[0]] = str(bgp_as)
                dict_bgp_as[cluster_nodes[1]] = str(bgp_as)
                cluster_leaf_list.append(cluster_nodes[0])
                cluster_leaf_list.append(cluster_nodes[1])

    non_clustered_leaf_list = list(set(leaf_list) - set(cluster_leaf_list))
    for leaf in non_clustered_leaf_list:
        bgp_as += 1
        dict_bgp_as[leaf] = str(bgp_as)

    return dict_bgp_as


def vrouter_interface_ibgp_add(module, switch_name, interface_ip, neighbor_ip,
                               remote_as):
    """
    Method to create interfaces and add ibgp neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: The name of the switch to run interface.
    :param interface_ip: Interface ip to create a vrouter interface.
    :param neighbor_ip: Neighbor_ip for the ibgp neighbor.
    :param remote_as: Bgp-as for remote switch.
    :return: String describing if ibgp neighbours got added or already exists.
    """
    global CHANGED_FLAG
    output = ''
    vlan_id = module.params['pn_ibgp_vlan']

    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s vlan-show format id no-show-headers ' % switch_name
    existing_vlans = run_cli(module, cli).split()

    if vlan_id not in existing_vlans:
        cli = clicopy
        cli += ' switch %s vlan-create id %s scope local ' % (switch_name,
                                                              vlan_id)
        run_cli(module, cli)

        output += ' %s: Created vlan with id %s \n' % (switch_name, vlan_id)
        CHANGED_FLAG.append(True)

    cli = clicopy
    cli += ' vrouter-show location %s format name' % switch_name
    cli += ' no-show-headers'
    vrouter = run_cli(module, cli).split()[0]

    cli = clicopy
    cli += ' vrouter-interface-show ip %s vlan %s' % (interface_ip, vlan_id)
    cli += ' format switch no-show-headers'
    existing_vrouter_interface = run_cli(module, cli).split()

    if vrouter not in existing_vrouter_interface:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name %s ip %s vlan %s ' % (
            vrouter, interface_ip, vlan_id
        )
        run_cli(module, cli)

        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch_name, interface_ip, vrouter
        )
        CHANGED_FLAG.append(True)

    neighbor_ip = neighbor_ip.split('/')[0]
    cli = clicopy
    cli += ' vrouter-bgp-show remote-as ' + remote_as
    cli += ' neighbor %s format switch no-show-headers' % neighbor_ip
    already_added = run_cli(module, cli).split()

    if vrouter not in already_added:
        cli = clicopy
        cli += ' vrouter-bgp-add vrouter-name %s' % vrouter
        cli += ' neighbor %s remote-as %s next-hop-self' % (neighbor_ip,
                                                            remote_as)
        if module.params['pn_bfd']:
            cli += ' bfd '

        if 'Success' in run_cli(module, cli):
            output += ' %s: Added iBGP neighbor %s for %s \n' % (switch_name,
                                                                 neighbor_ip,
                                                                 vrouter)
            CHANGED_FLAG.append(True)

    return output


def assign_ibgp_interface(module, dict_bgp_as):
    """
    Method to create interfaces and add ibgp neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param dict_bgp_as: The dictionary containing bgp-as of all switches.
    :return: The output of vrouter_interface_ibgp_add() method.
    """
    output = ''
    ibgp_ip_range = module.params['pn_ibgp_ip_range']
    subnet_count = 0
    supernet = 30

    cli = pn_cli(module)
    clicopy = cli

    address = ibgp_ip_range.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'

    cli += ' cluster-show format name no-show-headers '
    cluster_list = run_cli(module, cli).split()

    if len(cluster_list) > 0 and cluster_list[0] != 'Success':
        for cluster in cluster_list:
            cli = clicopy
            cli += ' cluster-show name %s format cluster-node-1' % cluster
            cli += ' no-show-headers'
            cluster_node_1 = run_cli(module, cli).split()[0]

            ip_count = subnet_count * 4
            ip1 = static_part + str(ip_count + 1) + '/' + str(supernet)
            ip2 = static_part + str(ip_count + 2) + '/' + str(supernet)

            cli = clicopy
            cli += ' cluster-show name %s format cluster-node-2' % cluster
            cli += ' no-show-headers'
            cluster_node_2 = run_cli(module, cli).split()[0]

            remote_as = dict_bgp_as[cluster_node_1]
            output += vrouter_interface_ibgp_add(module, cluster_node_1,
                                                 ip1, ip2, remote_as)
            output += vrouter_interface_ibgp_add(module, cluster_node_2,
                                                 ip2, ip1, remote_as)

            subnet_count += 1
    else:
        output += ' No leaf clusters present to add iBGP \n'

    return output


def add_bgp_neighbor(module):
    """
    This method add bgp_neighbor to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :return: The output of the adding bgp-neighbor
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli
    remote_as = module.params['pn_bgp_as_range']

    for leaf in module.params['pn_leaf_list']:
        weight_allowas_flag = 0

        cli = clicopy
        cli += ' vrouter-show location %s ' % leaf
        cli += ' format name no-show-headers '
        vrouter = run_cli(module, cli).split()[0]

        cli = clicopy
        cli += ' cluster-show format name no-show-headers'
        cluster_list = run_cli(module, cli).split()
        for cluster in cluster_list:
            if leaf in cluster:
                weight_allowas_flag = 1
                break

        cli = clicopy
        cli += ' vrouter-interface-show vrouter-name %s ' % vrouter
        cli += ' format l3-port no-show-headers '
        port_list = run_cli(module, cli).split()
        port_list = list(set(port_list))
        port_list.remove(vrouter)

        for port in port_list:
            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s l3-port %s ' % (
                 vrouter, port)
            cli += 'format ip no-show-headers'
            ip = run_cli(module, cli).split()
            ip = list(set(ip))
            ip.remove(vrouter)
            ip = ip[0]

            ip = ip.split('.')
            static_part = str(ip[0]) + '.' + str(ip[1]) + '.'
            static_part += str(ip[2]) + '.'
            last_octet = str(ip[3]).split('/')
            remote_ip_lastoctet = int(last_octet[0]) + 1
            remote_ip = static_part + str(remote_ip_lastoctet)

            cli = clicopy
            cli += ' vrouter-bgp-show'
            cli += ' neighbor %s format switch no-show-headers ' % (
                remote_ip)
            already_added = run_cli(module, cli).split()

            if vrouter in already_added:
                output += ''
            else:
                cli = clicopy
                cli += ' vrouter-bgp-add vrouter-name ' + vrouter
                cli += ' neighbor %s remote-as %s ' % (remote_ip,
                                                       remote_as)
                if module.params['pn_bfd']:
                    cli += ' bfd '

                if weight_allowas_flag == 1:
                    cli += ' weight 100 allowas-in '

                if 'Success' in run_cli(module, cli):
                    output += ' %s: Added BGP Neighbour %s for %s \n' % (
                        leaf, remote_ip, vrouter
                    )
                    CHANGED_FLAG.append(True)

    return output


def assign_router_id(module, vrouter_names):
    """
    Method to assign router-id to vrouters which is same as loopback ip.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter_names: List of vrouter names.
    :return: String describing if router id got assigned or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    if len(vrouter_names) > 0:
        for vrouter in vrouter_names:
            cli = clicopy
            cli += ' vrouter-loopback-interface-show vrouter-name ' + vrouter
            cli += ' format ip no-show-headers '
            loopback_ip = run_cli(module, cli).split()

            if 'Success' not in loopback_ip and len(loopback_ip) > 0:
                loopback_ip.remove(vrouter)
                cli = clicopy
                cli += ' vrouter-modify name %s router-id %s ' % (
                    vrouter, loopback_ip[0])

                if 'Success' in run_cli(module, cli):
                    cli = clicopy
                    cli += ' vrouter-show name ' + vrouter
                    cli += ' format location no-show-headers '
                    switch = run_cli(module, cli).split()[0]

                    output += ' %s: Added router id %s to %s \n' % (
                        switch, loopback_ip[0], vrouter)

                    CHANGED_FLAG.append(True)

    return output


def configure_bgp(module, vrouter_names, dict_bgp_as, bgp_max, bgp_redis):
    """
    Method to add bgp_as, bgp_max_path and bgp_redistribute to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :param dict_bgp_as: Dictionary containing the bgp-as for all the switches.
    :param vrouter_names: List of vrouter names.
    :param bgp_max: Maxpath for bgp.
    :param bgp_redis: Bgp redistribute for bgp.
    :return: String describing if bgp config got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-show name ' + vrouter
        cli += ' format location no-show-headers '
        switch = run_cli(module, cli).split()[0]

        cli = clicopy
        cli += ' vrouter-modify name %s ' % vrouter
        cli += ' bgp-as %s ' % dict_bgp_as[switch]
        cli += ' bgp-max-paths %s ' % bgp_max
        cli += ' bgp-redistribute %s ' % bgp_redis
        if 'Success' in run_cli(module, cli):
            output += ' %s: Added bgp_redistribute %s ' % (switch, bgp_redis)
            output += 'bgp_as %s bgp_maxpath %s to %s\n' % (dict_bgp_as[switch],
                                                            bgp_max, vrouter)
            CHANGED_FLAG.append(True)

    return output


def find_non_clustered_leafs(module):
    """
    Method to find leafs which are not part of any cluster.
    :param module: The Ansible module to fetch input parameters.
    :return: List of non clustered leaf switches.
    """
    non_clustered_leafs = []
    cli = pn_cli(module)
    cli += ' cluster-show format cluster-node-1,cluster-node-2 '
    cli += ' no-show-headers '
    clustered_nodes = run_cli(module, cli).split()

    for leaf in module.params['pn_leaf_list']:
        if leaf not in clustered_nodes:
            non_clustered_leafs.append(leaf)

    return non_clustered_leafs


def create_cluster(module, name, node1, node2):
    """
    Method to create a cluster between two switches.
    :param module: The Ansible module to fetch input parameters.
    :param name: The name of the cluster to create.
    :param node1: First node of the cluster.
    :param node2: Second node of the cluster.
    :return: String describing if cluster got created or not.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s cluster-show format name no-show-headers ' % node1
    cluster_list = run_cli(module, cli).split()
    if name not in cluster_list:
        cli = clicopy
        cli += ' switch %s cluster-create name %s ' % (node1, name)
        cli += ' cluster-node-1 %s cluster-node-2 %s ' % (node1, node2)
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Created %s \n' % (node1, name)
    else:
        return ''


def create_leaf_clusters(module):
    """
    Method to create cluster between two physically connected leaf switches.
    :param module: The Ansible module to fetch input parameters.
    :return: Output of create_cluster() method.
    """
    output = ''
    non_clustered_leafs = find_non_clustered_leafs(module)
    non_clustered_leafs_count = 0
    cli = pn_cli(module)
    clicopy = cli

    while non_clustered_leafs_count == 0:
        if len(non_clustered_leafs) == 0:
            non_clustered_leafs_count += 1
        else:
            node1 = non_clustered_leafs[0]
            non_clustered_leafs.remove(node1)

            cli = clicopy
            cli += ' switch %s lldp-show ' % node1
            cli += ' format sys-name no-show-headers '
            system_names = run_cli(module, cli).split()
            system_names = list(set(system_names))

            cli = clicopy
            cli += ' switch %s fabric-node-show ' % node1
            cli += ' format name no-show-headers '
            nodes_in_fabric = run_cli(module, cli).split()
            nodes_in_fabric = list(set(nodes_in_fabric))

            for system in system_names:
                if system not in nodes_in_fabric:
                    system_names.remove(system)

            terminate_flag = 0
            node_count = 0
            while (node_count < len(system_names)) and (terminate_flag == 0):
                node2 = system_names[node_count]
                if node2 in non_clustered_leafs:
                    # Cluster creation
                    cluster_name = node1 + '-to-' + node2 + '-cluster'
                    output += create_cluster(module, cluster_name, node1, node2)

                    non_clustered_leafs.remove(node2)
                    terminate_flag += 1

                node_count += 1

    return output


def configure_ospf_bfd(module, vrouter, ip):
    """
    Method to add ospf_bfd to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter: The vrouter name to add ospf bfd.
    :param ip: The interface ip to associate the ospf bfd.
    :return: String describing if OSPF BFD got added or if it already exists.
    """
    global CHANGED_FLAG
    cli = pn_cli(module)
    clicopy = cli
    cli += ' vrouter-interface-show vrouter-name %s' % vrouter
    cli += ' ip %s format nic no-show-headers ' % ip
    nic_interface = run_cli(module, cli).split()
    nic_interface = list(set(nic_interface))
    nic_interface.remove(vrouter)

    cli = clicopy
    cli += ' vrouter-interface-config-show vrouter-name %s' % vrouter
    cli += ' nic %s format ospf-bfd no-show-headers ' % nic_interface[0]
    ospf_status = run_cli(module, cli).split()
    ospf_status = list(set(ospf_status))

    cli = clicopy
    cli += ' vrouter-show name ' + vrouter
    cli += ' format location no-show-headers '
    switch = run_cli(module, cli).split()[0]

    if 'Success' in ospf_status:
        cli = clicopy
        cli += ' vrouter-interface-config-add vrouter-name %s' % vrouter
        cli += ' nic %s ospf-bfd enable' % nic_interface[0]
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Added OSPF BFD config to %s \n' % (switch, vrouter)
    elif 'enable' not in ospf_status:
        ospf_status.remove(vrouter)
        cli = clicopy
        cli += ' vrouter-interface-config-modify vrouter-name %s' % vrouter
        cli += ' nic %s ospf-bfd enable' % nic_interface[0]
        if 'Success' in run_cli(module, cli):
            CHANGED_FLAG.append(True)
            return ' %s: Enabled OSPF BFD for %s \n' % (switch, vrouter)
    else:
        return ''


def find_area_id_leaf_switches(module):
    """
    Method to find area_id for all leaf switches and store it in a dictionary.
    :param module: The Ansible module to fetch input parameters.
    :return: Dictionary containing area_id of all leaf switches.
    """
    leaf_list = module.params['pn_leaf_list']
    ospf_area_id = int(module.params['pn_ospf_area_id'])
    cluster_leaf_list = []
    cli = pn_cli(module)
    clicopy = cli
    dict_area_id = {}

    cli += ' cluster-show format name no-show-headers'
    cluster_list = run_cli(module, cli).split()

    if 'Success' not in cluster_list:
        for cluster in cluster_list:
            cli = clicopy
            cli += ' cluster-show name %s' % cluster
            cli += ' format cluster-node-1,cluster-node-2 no-show-headers'
            cluster_nodes = run_cli(module, cli).split()

            if cluster_nodes[0] in leaf_list and cluster_nodes[1] in leaf_list:
                ospf_area_id += 1
                dict_area_id[cluster_nodes[0]] = str(ospf_area_id)
                dict_area_id[cluster_nodes[1]] = str(ospf_area_id)
                cluster_leaf_list.append(cluster_nodes[0])
                cluster_leaf_list.append(cluster_nodes[1])

    non_clustered_leaf_list = list(set(leaf_list) - set(cluster_leaf_list))
    for leaf in non_clustered_leaf_list:
        ospf_area_id += 1
        dict_area_id[leaf] = str(ospf_area_id)

    return dict_area_id


def add_ospf_neighbor(module, dict_area_id):
    """
    This method add ospf_neighbor to the vrouter.
    :param module: The Ansible module to fetch input parameters.
    :param dict_area_id: Dictionary containing area_id of leafs.
    :return: The output of the adding ospf-neighbor.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    if len(module.params['pn_leaf_list']) > 0:
        for leaf in module.params['pn_leaf_list']:
            cli = clicopy
            cli += ' vrouter-show location %s' % leaf
            cli += ' format name no-show-headers'
            vrouter_leaf = run_cli(module, cli).split()[0]

            cli = clicopy
            cli += ' vrouter-interface-show vrouter-name %s ' % vrouter_leaf
            cli += ' format l3-port no-show-headers '
            port_list = run_cli(module, cli).split()
            port_list = list(set(port_list))
            port_list.remove(vrouter_leaf)

            ospf_area_id = dict_area_id[leaf]

            for port in port_list:
                cli = clicopy
                cli += ' vrouter-interface-show vrouter-name %s l3-port %s' % (
                     vrouter_leaf, port
                )
                cli += ' format ip no-show-headers'
                ip = run_cli(module, cli).split()
                ip = list(set(ip))
                ip.remove(vrouter_leaf)
                ip = ip[0]

                ip = ip.split('.')
                static_part = str(ip[0]) + '.' + str(ip[1]) + '.'
                static_part += str(ip[2]) + '.'
                last_octet = str(ip[3]).split('/')
                netmask = last_octet[1]

                last_octet_ip_mod = int(last_octet[0]) % 4
                ospf_last_octet = int(last_octet[0]) - last_octet_ip_mod
                ospf_network = static_part + str(ospf_last_octet) + '/'
                ospf_network += netmask
                ip_leaf = static_part + last_octet[0]

                cli = clicopy
                cli += ' vrouter-ospf-show'
                cli += ' network %s format switch no-show-headers ' % (
                    ospf_network)
                already_added = run_cli(module, cli).split()

                if vrouter_leaf in already_added:
                    output += ''
                else:
                    if module.params['pn_bfd']:
                        output += configure_ospf_bfd(module, vrouter_leaf,
                                                     ip_leaf)

                    cli = clicopy
                    cli += ' vrouter-ospf-add vrouter-name ' + vrouter_leaf
                    cli += ' network %s ospf-area %s' % (ospf_network,
                                                         ospf_area_id)

                    if 'Success' in run_cli(module, cli):
                        output += ' %s: Added OSPF neighbor to %s \n ' % (
                            leaf, vrouter_leaf
                        )
                        CHANGED_FLAG.append(True)

    return output


def add_ospf_redistribute(module, vrouter_names):
    """
    Method to add ospf_redistribute to the vrouters.
    :param module: The Ansible module to fetch input parameters.
    :param vrouter_names: List of vrouter names.
    :return: String describing if ospf-redistribute got added or not.
    """
    global CHANGED_FLAG
    output = ''
    cli = pn_cli(module)
    clicopy = cli

    for vrouter in vrouter_names:
        cli = clicopy
        cli += ' vrouter-modify name %s' % vrouter
        cli += ' ospf-redistribute static,connected'
        if 'Success' in run_cli(module, cli):
            cli = clicopy
            cli += ' vrouter-show name ' + vrouter
            cli += ' format location no-show-headers '
            switch = run_cli(module, cli).split()[0]

            output += ' %s: Added ospf_redistribute to %s \n' % (switch,
                                                                 vrouter)
            CHANGED_FLAG.append(True)

    return output


def vrouter_leafcluster_ospf_add(module, switch_name, interface_ip,
                                 ospf_network, ospf_area_id):
    """
    Method to create interfaces and add ospf neighbors.
    :param module: The Ansible module to fetch input parameters.
    :param switch_name: The name of the switch to run interface.
    :param interface_ip: Interface ip to create a vrouter interface.
    :param ospf_network: Ospf network for the ospf neighbor.
    :param ospf_area_id: The area_id for ospf neighborship.
    :return: String describing if ospf neighbors got added or not.
    """
    global CHANGED_FLAG
    output = ''
    vlan_id = module.params['pn_iospf_vlan']

    cli = pn_cli(module)
    clicopy = cli
    cli += ' switch %s vlan-show format id no-show-headers ' % switch_name
    existing_vlans = run_cli(module, cli).split()

    if vlan_id not in existing_vlans:
        cli = clicopy
        cli += ' switch %s vlan-create id %s scope local ' % (switch_name,
                                                              vlan_id)
        run_cli(module, cli)
        output = ' %s: Created vlan with id %s \n' % (switch_name, vlan_id)
        CHANGED_FLAG.append(True)

    cli = clicopy
    cli += ' vrouter-show location %s format name' % switch_name
    cli += ' no-show-headers'
    vrouter = run_cli(module, cli).split()[0]

    cli = clicopy
    cli += ' vrouter-interface-show ip %s vlan %s' % (interface_ip, vlan_id)
    cli += ' format switch no-show-headers'
    existing_vrouter_interface = run_cli(module, cli).split()

    if vrouter not in existing_vrouter_interface:
        cli = clicopy
        cli += ' vrouter-interface-add vrouter-name %s ip %s vlan %s ' % (
            vrouter, interface_ip, vlan_id
        )
        run_cli(module, cli)
        output += ' %s: Added vrouter interface with ip %s on %s \n' % (
            switch_name, interface_ip, vrouter
        )
        CHANGED_FLAG.append(True)

    cli = clicopy
    cli += ' vrouter-ospf-show'
    cli += ' network %s format switch no-show-headers ' % ospf_network
    already_added = run_cli(module, cli).split()

    if vrouter in already_added:
        pass
    else:
        interface_ip_without_supernet = interface_ip.split('/')[0]
        if module.params['pn_bfd']:
            output += configure_ospf_bfd(module, vrouter,
                                         interface_ip_without_supernet)
        cli = clicopy
        cli += ' vrouter-ospf-add vrouter-name ' + vrouter
        cli += ' network %s ospf-area %s' % (ospf_network, ospf_area_id)

        if 'Success' in run_cli(module, cli):
            output += ' %s: Added OSPF neighbor %s to %s \n' % (
                switch_name, ospf_network, vrouter
            )
            CHANGED_FLAG.append(True)

    return output


def assign_leafcluster_ospf_interface(module, dict_area_id):
    """
    Method to create interfaces and add ospf neighbor for leaf cluster.
    :param module: The Ansible module to fetch input parameters.
    :param dict_area_id: Dictionary containing area_id of leafs.
    :return: The output of vrouter_interface_ibgp_add() method.
    """
    output = ''
    iospf_ip_range = module.params['pn_iospf_ip_range']
    subnet_count = 0
    supernet = 30

    cli = pn_cli(module)
    clicopy = cli

    address = iospf_ip_range.split('.')
    static_part = str(address[0]) + '.' + str(address[1]) + '.'
    static_part += str(address[2]) + '.'

    cli += ' cluster-show format name no-show-headers '
    cluster_list = run_cli(module, cli).split()

    if len(cluster_list) > 0 and cluster_list[0] != 'Success':
        for cluster in cluster_list:
            cli = clicopy
            cli += ' cluster-show name %s format cluster-node-1' % cluster
            cli += ' no-show-headers'
            cluster_node_1 = run_cli(module, cli).split()[0]

            ip_count = subnet_count * 4
            ip1 = static_part + str(ip_count + 1) + '/' + str(supernet)
            ip2 = static_part + str(ip_count + 2) + '/' + str(supernet)
            ospf_network = static_part + str(ip_count) + '/' + str(supernet)

            cli = clicopy
            cli += ' cluster-show name %s format cluster-node-2' % cluster
            cli += ' no-show-headers'
            cluster_node_2 = run_cli(module, cli).split()[0]

            ospf_area_id = dict_area_id[cluster_node_1]
            output += vrouter_leafcluster_ospf_add(module, cluster_node_1,
                                                   ip1, ospf_network,
                                                   ospf_area_id)
            output += vrouter_leafcluster_ospf_add(module, cluster_node_2,
                                                   ip2, ospf_network,
                                                   ospf_area_id)

            subnet_count += 1
    else:
        output += ' No leaf clusters present to add iOSPF \n'

    return output


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str', no_log=True),
            pn_leaf_list=dict(required=False, type='list'),
            pn_bgp_as_range=dict(required=False, type='str', default='65000'),
            pn_bgp_redistribute=dict(required=False, type='str',
                                     choices=['none', 'static', 'connected',
                                              'rip', 'ospf'],
                                     default='connected'),
            pn_bgp_maxpath=dict(required=False, type='str', default='16'),
            pn_bfd=dict(required=False, type='bool', default=False),
            pn_ibgp_ip_range=dict(required=False, type='str',
                                  default='75.75.75.0/24'),
            pn_ibgp_vlan=dict(required=False, type='str', default='4040'),
            pn_iospf_vlan=dict(required=False, type='str', default='4040'),
            pn_iospf_ip_range=dict(required=False, type='str',
                                   default='75.75.75.0/24'),
            pn_ospf_area_id=dict(required=False, type='str', default='0'),
            pn_routing_protocol=dict(required=False, type='str',
                                     choices=['ebgp', 'ospf'], default='ebgp'),
        )
    )

    global CHANGED_FLAG
    routing_protocol = module.params['pn_routing_protocol']

    # Get the list of vrouter names.
    cli = pn_cli(module)
    cli += ' vrouter-show format name no-show-headers '
    vrouter_names = run_cli(module, cli).split()

    message = assign_router_id(module, vrouter_names)
    message += create_leaf_clusters(module)

    if routing_protocol == 'ebgp':
        dict_bgp_as = find_bgp_as_dict(module)
        message += configure_bgp(module, vrouter_names, dict_bgp_as,
                                 module.params['pn_bgp_maxpath'],
                                 module.params['pn_bgp_redistribute'])
        message += add_bgp_neighbor(module)
        message += assign_ibgp_interface(module, dict_bgp_as)
    elif routing_protocol == 'ospf':
        dict_area_id = find_area_id_leaf_switches(module)
        message += add_ospf_neighbor(module, dict_area_id)
        message += add_ospf_redistribute(module, vrouter_names)
        message += assign_leafcluster_ospf_interface(module, dict_area_id)

    results = []
    for switch in module.params['pn_leaf_list']:
        replace_string = switch + ': '

        for line in message.splitlines():
            if replace_string in line:
                json_msg = {
                    'switch': switch,
                    'output': (line.replace(replace_string, '')).strip()
                }
                results.append(json_msg)

    # Exit the module and return the required JSON.
    module.exit_json(
        unreachable=False,
        msg='eBGP/OSPF configuration succeeded',
        summary=results,
        exception='',
        failed=False,
        changed=True if True in CHANGED_FLAG else False,
        task='Configure eBGP/OSPF with existing spine switches'
    )

if __name__ == '__main__':
    main()

