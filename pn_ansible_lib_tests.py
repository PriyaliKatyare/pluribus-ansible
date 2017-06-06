"""
Unit testing for library file
"""

import unittest as ut
import json
import re
import ansible.library.pn_ansible_lib as pn

def json_out(input):
    return json.dumps(input, indent=4, sort_keys = True, separators=(',',': '))

class Module():
    """
    "Faking" Ansible interface so that all the tests will work without actually
    running anything through ansible itself. This allows the library to be unit
    tested locally. Any final testing should be run through ansible. These unit
    tests simply provide a simple way to check that all of the methods and 
    functions in the library work as expected.
    """
    
    def __init__(self, **kwargs):
        self.params = kwargs
        self.command_pass = True

        self.clusters = [] # Used to test cluster management
        self.vlans = [] # Used to test vlan management


    def exit_json(self, **kwargs):
        return json_out(kwargs)


    def fail_json(self, **kwargs):
        return json_out(kwargs)


    def run_command(self, command):
        """
        Runs a command and either "passes" or "fails" based on how the 
        self.command_pass flag is set.
        """
        command = ' '.join(command)

        r = re.compile('[A-Za-z\-// ]* cluster')
        if r.match(command):
            return self.handle_clusters(command)

        r = re.compile('[A-Za-z\-// ]* vlan')
        if r.match(command):
            return self.handle_vlans(command)
        
        if self.command_pass:
            return ('0', "Success", 'no error')
        else:
            return ('5', '', 'Error!')


    def handle_clusters(self, command):
        """
        """
        # cluster-create
        r = re.compile('[A-Za-z\-// ]* cluster-create name')
        if r.match(command):
            command = command.split()
            self.clusters.append({
                'cluster-name': command[-5],
                'cluster-node-1': command[-3],
                'cluster-node-2': command[-1]
            })
            return ('0', "Cluster %s created" % command[-5], 'no error')
        
        # cluster-delete
        r = re.compile('[A-Za-z\-// ]* cluster-delete name')
        if r.match(command):
            command = command.split()
            for cluster in self.clusters:
                if cluster['cluster-name'] == command[-1]:
                    self.clusters.remove(cluster)
                    return ('0', "Cluster %s removed" % command[-1], 'no error')
            return ('0', "Cluster was not deleted", 'Error!')
        
        # cluster-show
        r = re.compile('[A-Za-z\-// ]* cluster-show')
        if r.match(command):
            out = ""
            for cluster in self.clusters:
                out += " " + cluster['cluster-name']
            return ('0', out, 'no error')

        raise ValueError("Recieved bad command %s from caller" % command)


    def handle_vlans(self, command):
        """
        Let the Module class masquerede as a pretty vlan CLI handler, everyone
        likes to feel pretty sometimes. This method is only for unit testing the
        PN_cli.vlan(...) method. It sends back responses similar to those 
        recieved when querying the real CLI.
        :param command: The command that should be sent to the CLI.
        """
        # vlan-create
        r = re.compile('[A-Za-z\-// ]* vlan-create vlan-id')
        if r.match(command):
            command = command.split()
            self.vlans.append({
                'vlan-id': command[command.index('vlan-id') + 1],
            })
            return ('0', "Vlan %s created" % command[command.index('vlan-id') + 1], 'no error')

        # vlan-delete
        r = re.compile('[A-Za-z\-// ]* vlan-delete vlan-id')
        if r.match(command):
            command = command.split()
            for vlan in self.vlans:
                if vlan['vlan-id'] == command[command.index('vlan-id') + 1]:
                    self.vlans.remove(vlan)
                    return ('0', "Vlan %s removed" % \
                            command[command.index('vlan-id') + 1], 'no error')
            return ('0', "Vlan was not deleted", 'Error!')

        # vlan-modify
        r = re.compile('[A-Za-z\-// ]* vlan-modify vlan-id')
        if r.match(command):
            command = command.split()
            for vlan in self.vlans:
                if vlan['vlan-id'] == command[command.index('vlan-id') + 1]:
                    return ('0', 'Vlan %s has been modified' % \
                        command[command.index('vlan-id') + 1], 'no error')
            return ('0', "Vlan does not exist and cannot be modified", 'Error!')

        # vlan-show
        r = re.compile('[A-Za-z\-// ]* vlan-show')
        if r.match(command):
            out = ""
            for vlan in self.vlans:
                out += " " + vlan['vlan-id']
            return ('0', out, 'no error')

        raise ValueError("Recieved bad command \'%s\' from caller" % command)
        

class PN_ansible_lib_TEST(ut.TestCase):

    ## Tests for the PN_cli class and its methods
    
    def test_PN_cli_gen_command(self):

        # Test with no prefix, and defined username and password
        mod = Module(pn_cliusername='pluribus', pn_clipassword='password')
        cli = pn.PN_cli(mod)
        self.assertEqual(
            cli.gen_command('a-command'),
            '/usr/bin/cli --quiet --user pluribus:password a-command'
        )

        # Test with a custom prefix
        cli.command = 'vrouter-create'
        cli.prefix = 'prefix'
        self.assertEqual(
            cli.gen_command('vrouter-create'),
            'prefix vrouter-create'
        )

        # Test when username and password are not supplied
        mod = Module()
        cli = pn.PN_cli(mod)
        self.assertEqual(
            cli.gen_command('a-command'),
            '/usr/bin/cli --quiet a-command'
        )


    def test_PN_cli_send_command(self):
        # Test for a command passing
        mod = Module()
        cli = pn.PN_cli(mod)
        self.assertEqual(
            cli.send_command('a-command'), 'Success'
        )

        # Test for a command failing, outputs correct json
        mod.command_pass = False
        out = {'changed': False,
                'error': '1',
                'failed': True,
                'msg': 'Operation Failed: /usr/bin/cli --quiet a-command',
                'stderr': 'Error!'}
        self.assertEqual(cli.send_command('a-command'), json_out(out))


    def test_PN_cli_check_command(self):
        mod = Module()
        cli = pn.PN_cli(mod)
        
        # Check that it can find success
        self.assertEqual(cli.check_command('a-command', "Success"), True)

        # Check that method does not send false positives
        self.assertNotEqual(cli.check_command('a-command', "Failure"), True)

        # If command isn't valid, then the call to send_command will call
        # exit_json and execution will end.


    def test_PN_cli_check_command_string(self):
        mod = Module()
        cli = pn.PN_cli(mod)

        # Check for success
        self.assertEquals(cli.check_command_string('a-command', "Success", 'message'),
                          'message: Successful')

        # Check for failure
        mod.command_pass = False
        self.assertEquals(cli.check_command_string('a-command', "Failure", 'message'),
                          'message: Failed')


    def test_PN_cli_send_exit(self):
        mod = Module()
        cli = pn.PN_cli(mod)
        
        # Status is 0
        self.assertEquals(cli.send_exit(0, 'message'),
                          json_out({'msg': 'message', 'changed': False}))
        
        # Status is 1
        self.assertEquals(cli.send_exit(1, 'message'),
                          json_out({'msg': 'message', 'changed': True}))
        
        # Status is not 1 or 0
        self.assertEquals(cli.send_exit(5, 'message'),
                          json_out({'msg': 'message'}))


    def test_PN_cli_cluster(self):
        mod = Module()
        cli = pn.PN_cli(mod)

        # Create
        cli.cluster('create', cluster_name='test-cluster',
                    cluster_node_1='node-1', cluster_node_2='node-2')
        self.assertEquals(cli.cluster('exists', cluster_name='test-cluster'),
                          True)
        # Create wrong params
        # Delete
        self.assertEquals(cli.cluster('exists', cluster_name='test-cluster'),
                          True)
        cli.cluster('delete', cluster_name='test-cluster')
        self.assertEquals(cli.cluster('exists', cluster_name='test-cluster'),
                         False)
        # Delete wrong params
        # Exists
        self.assertNotEquals(cli.cluster('exists', cluster_name='new-cluster'),
                             True)
        # Exists wrong params
        # Show
        cli.cluster('create', cluster_name='test-cluster',
                    cluster_node_1='node-1', cluster_node_2='node-2')
        cli.cluster('create', cluster_name='new-cluster',
                    cluster_node_1='node-1', cluster_node_2='node-2')
        self.assertEquals(cli.cluster('show'), ' test-cluster new-cluster')


    def test_PN_cli_vlan(self):
        mod = Module()
        cli = pn.PN_cli(mod)

        # Create
        cli.vlan('create', vlan_id='5', vnet_name='test-vnet', vxlan='vxlan',
                 vxlan_mode='mode', public_vlan='public', scope='fabric')
        self.assertEquals(cli.vlan('exists', vlan_id='5'), True)
        
        # Delete
        self.assertEquals(cli.vlan('exists', vlan_id='5'), True)
        cli.vlan('delete', vlan_id=5, vnet_name='test-vnet')
        self.assertEquals(cli.vlan('exists', vlan_id='5'), False)
        
        # Exists
        self.assertNotEquals(cli.vlan('exists', vlan_id='10'), True)
        
        # Modiy
        cli.vlan('create', vlan_id='5', vnet_name='test-vnet', vxlan='vxlan',
                 vxlan_mode='mode', public_vlan='public', scope='fabric')
        cli.vlan('modify', vlan_id='5', description='modified')
        self.assertEquals(cli.vlan('exists', vlan_id='5'), True)
        cli.vlan('delete', vlan_id='5', vnet_name='test-vnet')
        
        # Show
        cli.vlan('create', vlan_id='7', vnet_name='test-vnet', vxlan='vxlan',
                 vxlan_mode='mode', public_vlan='public', scope='fabric')
        cli.vlan('create', vlan_id='8', vnet_name='test-vnet', vxlan='vxlan',
                 vxlan_mode='mode', public_vlan='public', scope='fabric')
        self.assertEquals(cli.vlan('show'), ' 7 8')


    def test_PN_cli_fabric(self):
        pass


if __name__ == '__main__':
    ut.main()
