"""
Unit testing for library file
"""

import unittest as ut
import json
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

    def exit_json(self, **kwargs):
        return json_out(kwargs)

    def fail_json(self, **kwargs):
        return json_out(kwargs)

    def run_command(self, command):
        """
        Runs a command and either "passes" or "fails" based on how the 
        self.command_pass flag is set.
        """
        if self.command_pass:
            return ('0', "Success", 'no error')
        else:
            return ('5', '', 'Error!')
        

class PN_ansible_lib_TEST(ut.TestCase):

    ## Tests for the PN_cli class and its methods
    
    def test_PN_cli_gen_command(self):

        # Test with no prefix, and defined username and password
        mod = Module(pn_cliusername='pluribus', pn_clipassword='password')
        cli = pn.PN_cli(mod, command='a-command')
        self.assertEqual(
            cli.gen_command(),
            '/usr/bin/cli --quiet --user pluribus:password a-command'
        )

        # Test with a custom prefix
        cli.command = 'vrouter-create'
        cli.prefix = 'prefix'
        self.assertEqual(
            cli.gen_command(),
            'prefix vrouter-create'
        )

        # Test when username and password are not supplied
        mod = Module()
        cli = pn.PN_cli(mod, command='a-command')
        self.assertEqual(
            cli.gen_command(),
            '/usr/bin/cli --quiet a-command'
        )


    def test_PN_cli_send_command(self):
        # Test for a command passing
        mod = Module()
        cli = pn.PN_cli(mod, command='a-command')
        self.assertEqual(
            cli.send_command(), 'Success'
        )

        # Test for a command failing, outputs correct json
        mod.command_pass = False
        out = {'changed': False,
                'error': '1',
                'failed': True,
                'msg': 'Operation Failed: /usr/bin/cli --quiet a-command',
                'stderr': 'Error!'}
        self.assertEqual(cli.send_command(), json_out(out))


    def test_PN_cli_check_command(self):
        mod = Module()
        cli = pn.PN_cli(mod, command='a-command')
        
        # Check that it can find success
        self.assertEqual(cli.check_command("Success"), True)

        # Check that method does not send false positives
        self.assertNotEqual(cli.check_command("Failure"), True)

        # If command isn't valid, then the call to send_command will call
        # exit_json and execution will end.


    def test_PN_cli_check_command_string(self):
        mod = Module()
        cli = pn.PN_cli(mod, command='a-command')

        # Check for success
        self.assertEquals(cli.check_command_string("Success", 'message'),
                          'message: Successful')

        # Check for failure
        mod.command_pass = False
        self.assertEquals(cli.check_command_string("Failure", 'message'),
                          'message: Failed')


    def test_PN_cli_send_exit(self):
        mod = Module()
        cli = pn.PN_cli(mod, command='a-command')

        # Status is 0 w/o ovrmsg
        self.assertEquals(cli.send_exit(0),
                          json_out({'msg': 'Operation Completed: a-command',
                                    'changed': False}))
        
        # Status is 0 w/ ovrmsg
        self.assertEquals(cli.send_exit(0, 'message'),
                          json_out({'msg': 'message', 'changed': False}))
        
        # Status is 1 w/o ovrmsg
        self.assertEquals(cli.send_exit(1),
                          json_out({'msg': 'Operation Completed: a-command',
                                    'changed': True}))
        
        # Status is 1 w/ ovrmsg
        self.assertEquals(cli.send_exit(1, 'message'),
                          json_out({'msg': 'message', 'changed': True}))
        
        # Status is not 1 or 0 w/o ovrmsg
        self.assertEquals(cli.send_exit(5),
                          json_out({'msg': 'Operation Failure: a-command'}))
        
        # Status is not 1 or 0 w/ ovrmsg
        self.assertEquals(cli.send_exit(5, 'message'),
                          json_out({'msg': 'Operation}))

        
if __name__ == '__main__':
    ut.main()
