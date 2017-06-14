"""
PN Ansible Library

This library is where we keep all cli manipulation functions which can be used in
modules to execute the tasks that we need done. 

**ALL FUNCTIONS THAT ARE CLI MANIPULATIONS SHOULD BE HERE, NOT IN A MODULE FILE**
We do this because we never know when a function we may think we will only use
once will become useful for a future module. By keeping all of the functions 
together we can avoid future re-factoring.

Make sure you run **ALL** tests if something in this file is changed. Because
there are many files which rely on the functions defined here, we must make sure
every module still works.

Also make sure that you run changes through pylint before pushing. This file 
should **ALWAYS** be PEP8 conforment with good coding style.

To use the functions in this library, include the following in your import 
header:

> import pn_ansible_lib as pn

then to use a function that is defined in the library use:

> pn.function_name(foo, bar)

"""

import shlex

def calc_link_ip_addr(addr, cidr, supernet):
    """
    Calculates link IP addresses for layer 3 fabric.
    :param addr:
    :param cidr:
    :param supernet:
    :return: A list of all avaliable IP addresses that can be assigned to the
    vrouter interfaces for the layer 3 fabric.
    """

    supernet_mapping = {
        27: 2,
        28: 14,
        29: 6,
        30: 2
    }

    addr = [int(x) for x in addr.split('.')]
    cidr = int(cidr)
    supernet = int(supernet)

    mask = [0, 0, 0, 0]
    for i in range(cidr):
        mask[i / 8] += (1 << (7 - i % 8))

    network = []
    for i in range(4):
        network.append(addr[i] & mask[i])

    broadcast = network
    for i in range(32 - cidr):
        broadcast[3 - i / 8] += (1 << (i % 8))

    avaliable_ips = []
    host = int(addr[3]) - ((int(addr[3]) % (supernet_mapping[supernet] + 2)))
    count = 0

    third_oct = network[2]
    
    while third_oct <= broadcast[2]:
        ip_list = []
        while count <  broadcast[3]:
            hostmin = host + 1
            hostmax = host + supernet_mapping[supernet]
            while hostmin <= hostmax:
                ip_list.append(hostmin)
                hostmin += 1
            host = hostmax + 2
            count += host

        ip_address = [broadcast[0], broadcast[1], third_oct]
        for i in range(len(ip_list)):
            avaliable_ips.append('.'.join(str(x) for x in ip_address)
                                 + ".%s/%s" % (ip_list[i], supernet))

        host = count = 0
        third_oct += 1

    return avaliable_ips


class PN_cli:
    """
    This is class designed to abstract the Pluribus CLI.
    """
    
    def __init__(self, module, prefix=''):
        """
        Initializes a PN_cli class. This class is used to interact with the
        command line of the destination switch.
        :param module: The ansible module instance, we need this to run commands
        throuh ssh on the destination host.
        :param prefix: The command prefix. This will be used when you are 
        repeatadly issuing commands with the same prefix, it allows less typing
        from the caller. By default the prefix will be '/usr/bin/cli --quiet' and
        '/usr/bin/cli --quiet --user {username}:{password}' if pn_cliusername and
        pn_clipassword are defined in the module parameters.
        :param command:
        """
        
        self.prefix = prefix

        if not prefix:
            self.prefix = '/usr/bin/cli --quiet'
            if ('pn_cliusername' in module.params) and \
               ('pn_clipassword' in module.params):
                self.prefix += ' --user %s:%s ' % (module.params['pn_cliusername']\
                                                 , module.params['pn_clipassword'])


        self.module = module


    def format(self, format):
        """
        Creates a format string to send to the CLI
        :param format: The string formatting option you would like back from the 
        cli.
        :return: A string in the form " format {format} no-show-headers".
        """
        
        return " format %s no-show-headers" % format


    def gen_command(self, command, prepend=''):
        """
        Concatenate the prefix with the command. This method isn't inteded to be
        used outside of the PN_cli class.
        :param command: The command to be concatenated with the prefix and 
        prepend strings.
        :param prepend: Anything to be prepended. This is used for generating
        output messages.
        :return: A concatenated string with the prefix and command
        """
        
        return ' '.join((prepend + " " + self.prefix + " " + command).split())

    
    def send_command(self, command, expect_output=True):
        """
        Send a command to the CLI on the destination host. Runs the current 
        instance's command on the destination host and returns the result. If the
        cli returns an error and does not execute the command Ansible will exit
        with a json error.
        :param command: The command to send to the cli.
        :return: The output sent back by the CLI
        """

        # TODO: Check for error instead of output
        command = shlex.split(self.gen_command(command))
        out, err = self.module.run_command(command)[1:]
        
        # TODO: Use module.fail_json?
        if expect_output and out:
            return out

        elif not expect_output and not out:
            return ""

        self.module.exit_json(
            error='1',
            failed=True,
            stderr = err.strip(),
            msg="Operation Failed: " + ' '.join(map(str, command)),
            changed=False
        )


    def check_command(self, command, string):
        """
        Replaces some instances of run_cli that check for a string in the output
        of the cli response. Returns a boolean, for the legacy version of this
        method which returns a string. Look at check_command_string.
        :param command: The command whose output will be checked.
        :param string: The string to search for in the CLI output.
        :return: True if string is in the output, False otherwise.
        """
        
        out = self.send_command(command)
        return True if out.find(string) > -1 else False


    def check_command_string(self, command, string, message):
        """
        Legacy version of the check_command method. For newer modules, this
        method should not be used, and should be replaced by the check_command
        method. This method should only be used for updating old modules where
        time is not avaliable for a ground-up rewrite.
        :param command: The command whose output will be checked.
        :param string: The string to search for in the CLI output.
        :param message: The message to be returned, typically the command being
        attempted.
        :return: {message}: [ Failed | Successful ]
        """
        
        if self.check_command(command, string):
            return "%s: Successful" % message

        return "%s: Failed" % message

    
    def send_exit(self, status, message, **kwargs):
        """
        Sends a module exit_json to Ansible.
        :param status: The status to be returned. Status 0 if success but no
        changes (idepotency), 1 is success and things were changed. Any other
        status is a general failure.
        :param message: The message to be sent back in the JSON response.
        :param kwargs: Unpacks all key word arguments into the module's exit json
        method. 
        """

        change = False
        
        if status is 0 or status is 1:
            
            if status is 1:
                change = True

            # Return statement not necessary, however it makes unit testing much
            # easier.
            return self.module.exit_json(
                msg=message,
                changed=change,
                **kwargs
            )
        
        # Return statement not necessary, however it makes unit testing much
        # easier.
        return self.module.fail_json(
            msg=message,
            **kwargs
        )


    def auto_accept_eula(self):
        """
        Accepts the EULA when Ansible logs into a new switch. This method is
        referenced from the auto_accept_eula in pn_initial_ztp.py
        :return: The output from the cli command sent to the target.
        """
        
        return self.send_command("--skip-setup --script-password "
                                 "switch-setup-modify password %s eula-accepted"
                                 " true" % module.params['password'])


    def vcfm_json(self, status_int, message, summary, task, status, **kwargs):
        """
        Outputs the required json for vcf-m applications. Follows standards
        outlined by: 
        confluence.pluribusnetworks.com/pages/viewpage.action?pageId=12452428
        This method is a specific implementation of the PN_cli.send_exit()
        method. See PN_cli.send_exit() for more information on the general 
        version of this funtion.
        :param status_int: Ansible status. 0 is success but no changes.
        (idempotency). 1 is success and things were changed. Any other status
        is a general failure.
        :param message: The status message to be sent back in the JSON output.
        :param summary: An array of dictionaries. Each dictionary has two 
        entries, "output" and "switch". Output is the CLI output returned by the
        switch. Switch is the name of the switch that the output was returned 
        from.
        :param task: A string that describes the Ansible task that was executed
        by the switch.
        :param status: An integer for the status of the execution. This value
        will either be 0 or 1. 0 means success and 1 means failure. This is a
        different value than status_int. This can be confusing, but status_int is
        a switch for the send_exit() method, and status is a status for vcfm.
        :param kwargs: Any additional output keyword arguments, these are passed
        as is to the modules's exit_json or fail_json methods.
        """

        self.send_exit(status,
                       message,
                       summary=summary,
                       task=task,
                       status=status,
                       **kwargs)


    def aks(self, kwargs, command, option):
        """
        Add Kwargs Simple
        """
        if option in kwargs:
            command += " %s %s" % (option.replace('_','-'), kwargs[check])


    def aka(self, kwargs, command, option, list):
        """
        Add Kwargs Array
        """
        if option in kwargs:
            for item in list:
                if item == kwargs['option']:
                    command += " %s %s" % (option.replace('_','-', item))


    def akb(self, kwargs, command, option, bool):
        """
        Add Kwargs Bool
        """
        if option in kwargs:
            command += " %s", bool[0] if kwargs[option] else bool[1]


    def cluster(self, action, **kwargs):
        """
        Handles commands related to clusters on the CLI. Does not do idempotency
        logic. Idempotency logic must be implemented in the module itself.
        Issues: Does not support validate | no-validate command line option when
        creating a cluster.
        :param action: The action to preform [ create | delete | exists | show ].
        :param kwargs: Keyword arguments to the method, see the ONVL command
        guide for relevant arguments based on the action. Note that all '-' must
        be converted to a '_' in keyword arguments to follow python syntax rules.
        :return: Depends on action, create and delete return nothing, exists 
        returns a boolean and show returns the output from the cli.
        """

        command = ''
        self.aks(kwargs, command, 'switch')

        #TODO: Add error checking for key word arguments

        # Handles logic to create a cluster
        if action is 'create':
            if not ('cluster_name' in kwargs and \
                    'cluster_node_1' in kwargs and \
                    'cluster_node_2' in kwargs):
                self.send_exit(5, "Must specify a name and two nodes to" \
                               " create a cluster")
            
            self.send_command("cluster-create name %s cluster-node-1 %s" \
                              " cluster-node-2 %s" % (kwargs['cluster_name'],
                                                      kwargs['cluster_node_1'],
                                                      kwargs['cluster_node_2'])
                              )
            return

        # Handles logic to delete a cluster
        elif action is 'delete':
            if not ('cluster_name' in kwargs):
                self.send_exit(5, "Must specify a name to delete a cluster")

            self.send_command("cluster-delete name %s" % kwargs['cluster_name'])
            
            return

        # Handles logic to check that a cluster exists
        elif action is 'exists':
            if 'cluster_name' not in kwargs:
                self.send_exit(5, "Cannot find a cluster without a cluster name")

            return True if kwargs['cluster_name'] in self.cluster('').split() else False

        # Returns the names of all clusters if action isn't recognized
        command = 'cluster-show' + self.format("name")
        return self.send_command(command)

        
    def vlan(self, action, **kwargs):
        """
        Handles CLI commands related to vlans. Does not handle any idempotency
        logic. Idempotency must be implemented in the module itself. Note: This
        method does not preform argument type checking, and assumes that all of
        the keyword arguments have the correct type.
        :param action: The action to preform [ create | delete | exists | show ].
        :param kwargs: Keyword arguments to the method, see the ONVL command
        guide for relevant arguments based on the action. Note that all '-' must
        be converted to a '_' in keyword arguments to follow python syntax rules.
        :return: Depends on the action. Create and delete return nothing, exists
        returns a boolean and show retuns the 'vlan-show' output from the CLI.
        """

        command = ''
        self.aks(kwargs, command, 'switch')

        # TODO: Add error checking for the keyword arguments
        
        # Create a vlan
        if action == 'create':
            if not ('vlan_id' in kwargs and 'vnet_name' in kwargs and \
                    'vxlan' in kwargs and 'vxlan_mode' in kwargs and \
                    'public_vlan' in kwargs and 'scope' in kwargs):
                self.send_exit(5, 'Create vlan is missing parameters')

            command += 'vlan-create'

            for option in ['vlan-id', 'vnet_name', 'vxlan',
                           'vxlan-mode', 'public-vlan', 'scope']:
                command += " %s %s" % (option, kwargs[option.replace('-','_')])
            
            if 'description' in kwargs:
                command += " description %s" % kwargs['description']

            if 'stats' in kwargs:
                if kwargs['stats']:
                    command += " stats"
                else:
                    command += " no-stats"

            if 'ports' in kwargs:
                command += " ports %s" % kwargs['ports']

            if 'untagged_ports' in kwargs:
                command += " untagged-ports %s" % kwargs['untagged_ports']

            self.send_command(command)
            return

        # Delete a vlan
        elif action == 'delete':
            if not ('vlan_id' in kwargs and 'vnet_name' in kwargs):
                self.send_exit(5, 'Deleting a vlan requires id and name')

            self.send_command("vlan-delete vlan-id %s vnet %s" % (
                kwargs['vlan_id'], kwargs['vnet_name']))
            return

        # Modify an existing vlan
        elif action == 'modify':
            if not ('vlan_id' in kwargs):
                self.send_exit(5, 'Must supply an id to vlan-modify')

            command += "vlan-modify vlan-id %s" % kwargs['vlan_id']

            self.aks(kwargs, command, 'description')
            self.aks(kwargs, command, 'vxlan')
            self.aks(kwargs, command, 'vnet')

            self.send_command(command)
            return

        # Check if a vlan exists
        elif action == 'exists':
            if not 'vlan_id' in kwargs:
                self.send_exit(5, "Must provide an id to search for")
                
            if kwargs['vlan_id'] in self.vlan('show').split():
                return True

            return False

        # Fall through and send a show command if the action isn't recognized
        return self.send_command('vlan-show' + self.format('id'))


    def vrouter(self, action, **kwargs):
        """
        Handles the management of vrouters through the CLI. This method does not 
        handle any any idempotency logic. The responsibility of implementing
        idempotency falls to the caller. This method also does not currently do
        ANY error checking on the key word arguments.
        :param action:
        :param kwargs:
        :return:
        """

        command = ''
        self.aks(kwargs, command, 'switch')
        
        if action == 'create':
            if not ('name' in kwargs and 'vnet' in kwargs):
                self.send_exit(5, 'Vrouter create is missing parameters')

            command += "vrouter-create name %s vnet %s" % (kwargs['name'],
                                                           kwargs['vnet'])

            if 'dedicated_vnet_service' in kwargs:
                if kwargs['dedicated_vnet_service']:
                    command += ' dedicated-vnet-service'
                else:
                    if 'shared_vnet_mgr' not in kwargs:
                        self.send_exit(5, 'A shared vrouter needs a manager')
                    
                    command += "shared-vnet-service shared-vnet-mgr %s" % \
                               kwargs['shared_vnet_mgr']

            if 'service' in kwargs:
                if kwargs['service']:
                    command += ' enable'
                else:
                    command += 'disable'

            self.aks(kwargs, command, 'storage_pool')
            self.aka(kwargs, command, 'router_type', ['hardware', 'software'])
            self.aks(kwargs, command, 'hw_vrrp_id')
            self.aks(kwargs, command, 'bgp_as')
            self.aks(kwargs, command, 'router_id')
            self.aka(kwargs, command, 'proto_multi', ['none', 'vmrp', 'pim-ssm'])
            self.aka(kwargs, command, 'bgp_redistribute',
                     ['static', 'connected', 'rip', 'ospf'])

            # TODO: Other command options need to be implemented

            self.send_command(command)
            return
                
        elif action == 'delete':
            if not ('name' in kwargs):
                self.send_exit(5, 'Need to specify a vrouter to delete')

            self.send_command(command)
            return

        elif action == 'modify':
            pass

        elif action == 'exists':
            pass
        
        # If action isn't recognized return the output from a show command
        return self.send_command('vrouter-show' + self.format('name'))


    def vrouter_bgp(self, action, **kwargs):
        """
        """
        
        command = ''
        self.aks(kwargs, command, 'switch')
        pass


    def vrouter_interface_config(self, action, **kwargs):
        """
        Handle vrouter interface configs on the CLI. This method covers the
        vrouter-interface-config-add, vrouter-interface-config-modify and
        vrouter-interface-config-remove commands from the CLI.
        """
        
        command = ''
        self.aks(kwargs, command, 'switch')

        if action == 'add':
            pass
        elif action == 'modify':
            pass
        elif action == 'remove':
            pass
        pass

    
    def vrouter_interface(self, action, **kwargs):
        """
        Handle managing vrouter-interfaces on the CLI. This method covers the
        vrouter-interface-add, vrouter-interface-modify and 
        vrouter-interface-remove commands. This method does not do any type or
        value checking on the parameters that are givin to it.
        :param action: The action to preform with the vrouter interface. Maps
        add, modify and remove to create, modify and delete to match with other
        CLI action methods. [ add | create | modify | exists | remove | delete ]
        :param kwargs: Keyword arguments. See ONVL product documentation for a
        list of options for these commands.
        :return:
        """

        command = ''
        self.aks(kwargs, command, 'switch')

        if action == 'add' or action == 'create':
            if 'vrouter-name' not in kwargs:
                self.send_exit(5, 'Must specify a vrouter for the vrouter interface')

            command += 'vrouter-interface-add'
            
            self.aks(kwargs, command, 'vrouter-name')
            self.aks(kwargs, command, 'ip')
            self.aks(kwargs, command, 'netmask')
            self.aka(kwargs, command, 'assignment',
                     ['none', 'dhcp', 'dhcpv6', 'autov6'])
            self.aka(kwargs, command, 'vlan-type', ['public', 'private'])
            self.aks(kwargs, command, 'vxlan')
            self.aka(kwargs, command, 'if', ['mgmt', 'data', 'span'])
            self.aks(kwargs, command, 'alias-on')
            self.akb(kwargs, command, 'exclusive', ['exclusive', 'no-exclusive'])
            self.akb(kwargs, command, 'nic-enable', ['nic-enable', 'nic-disable'])
            self.aks(kwargs, command, 'vrrp-id')
            self.aks(kwargs, command, 'vrrp-primary')
            self.aks(kwargs, command, 'vrrp-priority')
            self.aks(kwargs, command, 'vrrp-adv-int')
            self.aks(kwargs, command, 'l3-port')
            self.aks(kwargs, command, 'mtu')

            return self.send_command(command)

        elif action == 'modify':
            if 'vrouter-name' not in kwargs:
                self.send_exit(5, 'Must specify a vrouter interface to modify')

            command += 'vrouter-interface-modify'
                
            self.aks(kwargs, command, 'vrouter-name')
            self.aks(kwargs, command, 'nic-string')
            self.aks(kwargs, command, 'ip')
            self.aks(kwargs, command, 'netmask')
            self.aka(kwargs, command, 'assignment',
                     ['none', 'dhcp', 'dhcpv6', 'autov6'])
            self.aka(kwargs, command, 'vlan-type', ['public', 'private'])
            self.aks(kwargs, command, 'vxlan')
            self.aka(kwargs, command, 'if', ['mgmt', 'data', 'span'])
            self.aks(kwargs, command, 'alias-on')
            self.akb(kwargs, command, 'exclusive', ['exclusive', 'no-exclusive'])
            self.akb(kwargs, command, 'nic-enable', ['nic-enable', 'nic-disable'])
            self.aks(kwargs, command, 'vrrp-id')
            self.aks(kwargs, command, 'vrrp-primary')
            self.aks(kwargs, command, 'vrrp-priority')
            self.aks(kwargs, command, 'vrrp-adv-int')
            self.aks(kwargs, command, 'l3-port')
            self.aks(kwargs, command, 'secondary-macs')
            self.aks(kwargs, command, 'mtu')

            return self.send_command(command)
            
        elif action == 'exists':
            if 'vrouter-name' not in kwargs:
                self.send_exit(5, 'Must specify a vrouter interface to check')

        elif action == 'remove' or action == 'delete':
            if 'vrouter-name' not in kwargs:
                self.send_exit(5, 'Must specify a vrouter to delete interface from')

            command += 'vrouter-interface-remove'

            self.aks(kwargs, command, 'vrouter-name')
            self.aks(kwargs, command, 'nic-string')

            return self.send_command(command)

        # Fall through to vrouter-interface-show


    def loopback_interface(self, action, **kwargs):
        """
        """

        command = ''
        self.aks(kwargs, command, 'switch')
        
        pass


    def trunk(self, action, **kwargs):
        """
        Handle trunk actions through the CLI
        :param action:
        :param kwargs:
        :return:
        """

        command = ''
        self.aks(kwargs, command, 'switch')
        
        if action == 'create':
            pass

        elif action == 'exists':
            if 'name' not in kwargs:
                self.send_exit(5, "Need to specify the name of a trunk to find")

            command += 'trunk create'
            
            self.aks(kwargs, command, 'name')

        elif action == 'delete':
            pass

        elif action == 'modify':
            pass

        # Fall through to trunk-show


    def switch_setup(self, action, **kwargs):
        """
        """

        command = ''
        self.aks(kwargs, command, 'switch-name')

        if action == 'modify':

            command += 'switch-setup-modify'

            self.aks(kwargs, command, 'mgmt-ip')
            self.aks(kwargs, command, 'mgmt-netmask')
            self.aks(kwargs, command, 'gateway-ip')
            self.aks(kwargs, command, 'dns-ip')
            self.aks(kwargs, command, 'dns-secondary-ip')
            self.aks(kwargs, command, 'domain-name')
            self.aks(kwargs, command, 'ntp-serer')

        elif action == 'show':
            pass

        self.send_exit(5, "switch_setup accepts modify or show as actions")


    def fabric(self, action, **kwargs):
        """
        Handle fabric actions on the CLI.
        :param action: The action to preform [ create | join | node-show | show ]
        :param kwargs: Keyword arguments to the method, see the ONVL command
        guide for relevant arguments based on the action. Note that all '-' must
        be converted to '_' in the keyword arguments to follow python syntax 
        rules.
        :return:
        """

        command = ''
        self.aks(kwargs, command, 'switch')
        
        if action == 'node-show':
            return self.send_command('fabric-node-show' + self.format('name'))
        
        elif action == 'create':
            if 'name' not in kwargs:
                self.send_exit(5, 'Must specify a fabric name to '
                               'create a fabric')

            command += "fabric-create %s" % kwargs['name']

            self.aks(kwargs, command, 'repeer-to-cluster-node')
            self.aks(kwargs, command, 'vlan')
            self.aks(kwargs, command, 'password')
            self.aka(kwargs, command, 'fabric-network', ['in-band', 'mgmt'])
            self.aka(kwargs, command, 'fabric-advertisement-network',
                     ['inband-mgmt', 'inband-only'])
            self.akb(kwargs, command, 'conflicts',
                     ['delete-conflicts', 'abort-on-conflict'])

            return self.send_command(command)
                
        elif action == 'join':
            if 'name' not in kwargs and 'switch-ip' not in kwargs:
                self.send_exit(5, 'Must specify a name or switch-ip to join a '
                               'fabric')

            command += 'fabric-join'
            
            if 'name' in kwargs:
                command += " name %s" % kwargs['name']

            else:
                command += " switch-ip %s" % kwargs['switch-ip']

            self.aks(kwargs, command, 'vlan')
            self.aks(kwargs, command, 'password')
            self.aks(kwargs, command, 'repeer-to-cluster-node')
            self.akb(kwargs, command, 'conflicts',
                     ['delete-conflicts', 'abort-on-conflict'])

            return self.send_command(command)

        elif action == 'exists':
            if 'name' not in kwargs:
                self.send_exit(5, 'Must specify a fabric name to check that '
                               'a fabric exists')

            if kwargs['name'] in self.fabric('fabric-show'):
                return True

            return False

        elif action == 'join':
            pass

        elif action == 'unjoin':
            pass
        
        # fall through to fabric-show
        command += 'fabric-show'

        self.aks(kwargs, command, 'name')
        self.aks(kwargs, command, 'switch-ip')
        self.aks(kwargs, command, 'vlan')
        self.aks(kwargs, command, 'tid')

        return self.send_command(command)
