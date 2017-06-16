"""
Unit testing for library file
"""

import unittest as ut
import json
import ansible.common.pn_ansible_lib as pn


def json_out(string):
    """
    Dumps json from the supplied arguments (kwargs)
    """

    return json.dumps(string, indent=4, sort_keys=True, separators=(',', ': '))


class Module(object):
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

        self.clusters = []  # Used to test cluster management
        self.vlans = []     # Used to test vlan management

    def exit_json(self, **kwargs):
        """
        Return json as if the module exited normally
        """

        return json_out(kwargs)

    def fail_json(self, **kwargs):
        """
        Return a failed json output
        """

        return json_out(kwargs)

    def run_command(self, command):
        """
        Runs a command and either "passes" or "fails" based on how the
        self.command_pass flag is set.
        """

        command = ' '.join(command)

        if self.command_pass:
            return ('0', "Success", 'no error')

        return ('5', '', 'Error!')


class PnAnsibleLib_TEST(ut.TestCase):
    """
    Tests for the PnCli class methods
    """

    def test_gen_command(self):
        """
        test PnCli.gen_command
        """
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

    def test_send_command(self):
        """
        test PnCli.send_command
        """
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

    def test_check_command(self):
        """
        test PnCli.check_command
        """
        mod = Module()
        cli = pn.PN_cli(mod)

        # Check that it can find success
        self.assertEqual(cli.check_command('a-command', "Success"), True)

        # Check that method does not send false positives
        self.assertNotEqual(cli.check_command('a-command', "Failure"), True)

        # If command isn't valid, then the call to send_command will call
        # exit_json and execution will end.

    def test_check_command_string(self):
        """
        test PnCli.check_command_string
        """
        mod = Module()
        cli = pn.PN_cli(mod)

        # Check for success
        self.assertEquals(cli.check_command_string('a-command', "Success",
                                                   'message'),
                          'message: Successful')

        # Check for failure
        mod.command_pass = False
        self.assertEquals(cli.check_command_string('a-command', "Failure",
                                                   'message'),
                          'message: Failed')

    def test_send_exit(self):
        """
        test PnCli.send_exit
        """
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


if __name__ == '__main__':
    ut.main()
