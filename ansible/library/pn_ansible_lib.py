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

class PN_cli:
    """
    This is class designed to abstract the Pluribus CLI.
    """
    
    def __init__(self, module, prefix='', command=''):
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

                
        self.command = command if command else ''
        self.module = module
        self.success_message = "Operation Completed: "
        self.failure_message = "Operation Failure: "


    def gen_command(self, prepend=''):
        """
        Concatenate the prefix with the command. This method isn't inteded to be
        used outside of the PN_cli class.
        :param prepend: Anything to be prepended. This is used for generating
        output messages.
        :return: A concatenated string with the prefix and command
        """
        
        return ' '.join((prepend + " " + self.prefix + " " + self.command).split())

    
    def send_command(self):
        """
        Send a command to the CLI on the destination host. Runs the current 
        instance's command on the destination host and returns the result. If the
        cli returns an error and does not execute the command Ansible will exit
        with a json error.
        :return: The output sent back by the CLI
        """
        
        command = shlex.split(self.gen_command())
        out, err = self.module.run_command(command)[1:]

        # TODO: Use module.fail_json?
        return out if out else self.module.exit_json(
            error='1',
            failed=True,
            stderr = err.strip(),
            msg="Operation Failed: " + ' '.join(map(str, command)),
            changed=False
        )


    def check_command(self, string):
        """
        Replaces some instances of run_cli that check for a string in the output
        of the cli response. Returns a boolean, for the legacy version of this
        method which returns a string. Look at check_command_string.
        :param string: The string to search for in the CLI output.
        :return: True if string is in the output, False otherwise.
        """
        
        out = self.send_command()
        return True if out.find(string) > -1 else False


    def check_command_string(self, string, message):
        """
        Legacy version of the check_command method. For newer modules, this
        method should not be used, and should be replaced by the check_command
        method. This method should only be used for updating old modules where
        time is not avaliable for a ground-up rewrite.
        :param string: The string to search for in the CLI output.
        :param message: The message to be returned, typically the command being
        attempted.
        :return: {message}: [ Failed | Successful ]
        """
        
        if self.check_command(string):
            return "%s: Successful" % message

        return "%s: Failed" % message

    
    def send_exit(self, status, ovrmsg=''):
        """
        Sends a module exit_json to Ansible.
        :param status: The status to be returned. Status 0 if success but no
        changes (idepotency), 1 is success and things were changed. Any other
        status is a general failure
        :param ovrmsg: String that overwrites the default message sent back to
        Ansible.
        """

        message = ''
        change = False
        
        if status is 0 or status is 1:
            message = ovrmsg if ovrmsg else self.success_message + self.command
            
            if status is 1:
                change = True

            # Return statement not necessary, however it makes unit testing much
            # easier.
            return self.module.exit_json(
                msg=message,
                changed=change
            )

        message = ovrmsg if ovrmsg else self.failure_message + self.command
        
        # Return statement not necessary, however it makes unit testing much
        # easier.
        return self.module.fail_json(
            msg=message,
        )


    def vcfm_json(self):
        """
        Outputs the required json for vcf-m applications. Follows standards
        outlined by: 
        confluence.pluribusnetworks.com/pages/viewpage.action?pageId=12452428
        """

        #TODO: Implement this function
        pass

