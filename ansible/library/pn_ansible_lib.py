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
        self.success_message = "Operation Completed: "
        self.failure_message = "Operation Failure: "


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

    
    def send_command(self, command):
        """
        Send a command to the CLI on the destination host. Runs the current 
        instance's command on the destination host and returns the result. If the
        cli returns an error and does not execute the command Ansible will exit
        with a json error.
        :param command: The command to send to the cli.
        :return: The output sent back by the CLI
        """
        
        command = shlex.split(self.gen_command(command))
        out, err = self.module.run_command(command)[1:]
        
        # TODO: Use module.fail_json?
        return out if out else self.module.exit_json(
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

    
    def send_exit(self, status, message):
        """
        Sends a module exit_json to Ansible.
        :param status: The status to be returned. Status 0 if success but no
        changes (idepotency), 1 is success and things were changed. Any other
        status is a general failure.
        :param ovrmsg: String that overwrites the default message sent back to
        Ansible.
        """

        change = False
        
        if status is 0 or status is 1:
            
            if status is 1:
                change = True

            # Return statement not necessary, however it makes unit testing much
            # easier.
            return self.module.exit_json(
                msg=message,
                changed=change
            )
        
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


    def vrouter(action, **kwargs):
        """
        Handle's vrouter creation, deletion, modification and show commands
        :param action: [ create | delete | show ]
        :return:
        """
        if action is 'create':
            pass
        elif action is 'delete':
            pass
        else:
            #show
            pass


    def cluster(self, action, **kwargs):
        """
        Handles commands related to clusters on the CLI. Does not do idempotency
        logic. Idempotency logic must be implemented in the module itself.
        Issues: Does not support validate | no-validate command line option when
        creating a cluster.
        :param action: The action to preform [ create | delete | exists | show ].
        :param kwargs: Keyword arguments to the function, see the ONVL command
        guide for relevant arguments based on the action. Note that all '-' must
        be converted to a '_' in keyword arguments to follow python syntax rules.
        :return: Depends on action, create and delete return nothing, exists 
        returns a boolean and show returns the output from the cli.

        Examples:

        Create a cluster between two switches:
        ```python
        ...
        import pn_ansible_lib as pn
        ...
        cli = pn.PN_cli(module)

        # Check that the cluster doesn't already exist.
        if not cli.cluster('exists', cluster_name='example'):
            cli.cluster('create', cluster_name='example', 
                        cluster_node_1='switch-1', cluster_node_2='switch-2')

            if cli.cluster('exists', cluster_name='example'):
                # Good to go, it worked!
                ...
            else:
                # Cluster wasn't created :(
                ...

        else:
            # Cluster already exists
            ...

        ...
        ```

        Delete a cluster between two switches:
        ```python
        ...
        import pn_ansible_lib as pn
        ...
        cli = pn.PN_cli(module)

        # Check if the cluster even exists
        if cli.cluster('exists', cluster_name='example'):
            cli.cluster('delete', cluster_name='example'):
        
            if cli.cluster('exists', cluster_name='example'):
                # Cluster wasn't deleted :(
                ...
            else:
                # Cluster was deleted! Yay!
                ...

        else:
            # Cluster didn't exist in the first place
            ...

        ...
        ```
        """

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

        # Returns the names of all clusters
        else:
            command = 'cluster-show' + self.format("name")
            return self.send_command(command)


        

        
