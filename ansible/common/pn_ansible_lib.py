"""
PN Ansible Library
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

    mask = [0, 0, 0, 0]
    for i in range(int(cidr)):
        mask[i / 8] += (1 << (7 - i % 8))

    network = []
    for i in range(4):
        network.append(addr[i] & mask[i])

    broadcast = network
    for i in range(32 - int(cidr)):
        broadcast[3 - i / 8] += (1 << (i % 8))

    avaliable_ips = []
    host = int(addr[3]) - ((int(addr[3]) %
                            (supernet_mapping[int(supernet)] + 2)))
    count = 0

    third_oct = network[2]

    while third_oct <= broadcast[2]:
        ip_list = []
        while count < broadcast[3]:
            hostmin = host + 1
            hostmax = host + supernet_mapping[int(supernet)]
            while hostmin <= hostmax:
                ip_list.append(hostmin)
                hostmin += 1
            host = hostmax + 2
            count += host

        ip_address = [broadcast[0], broadcast[1], third_oct]
        for i in enumerate(ip_list):
            avaliable_ips.append('.'.join(str(x) for x in ip_address) +
                                 ".%s/%s" % (ip_list[i], int(supernet)))

        host = count = 0
        third_oct += 1

    return avaliable_ips


class PnCli(object):
    """
    This is class designed to abstract the Pluribus CLI.
    """

    # ==--------------------------------------------------------------------== #
    #
    # Class management methods
    #
    # ==--------------------------------------------------------------------== #

    def __init__(self, module, prefix=''):
        """
        Initializes a PN_cli class. This class is used to interact with the
        command line of the destination switch.
        :param module: The ansible module instance, we need this to run commands
        throuh ssh on the destination host.
        :param prefix: The command prefix. This will be used when you are
        repeatadly issuing commands with the same prefix, it allows less typing
        from the caller. By default the prefix will be '/usr/bin/cli --quiet'
        and '/usr/bin/cli --quiet --user {username}:{password}' if
        pn_cliusername and pn_clipassword are defined in the module parameters.
        :param command:
        """

        self.prefix = prefix

        if not prefix:
            self.prefix = '/usr/bin/cli --quiet'
            if ('pn_cliusername' in module.params) and \
               ('pn_clipassword' in module.params):
                self.prefix += ' --user %s:%s ' % (
                    module.params['pn_cliusername'],
                    module.params['pn_clipassword'])

        self.module = module

    # ==--------------------------------------------------------------------== #
    #
    # CLI interaction methods
    #
    # ==--------------------------------------------------------------------== #

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
        instance's command on the destination host and returns the result. If
        the cli returns an error and does not execute the command Ansible will
        exit with a json error.
        :param command: The command to send to the cli.
        :return: The output sent back by the CLI
        """

        # TODO: Check for error instead of output
        command = shlex.split(self.gen_command(command))
        out, err = self.module.run_command(command)[1:]

        if err:
            self.module.exit_json(
                error='1',
                failed=True,
                stderr=err.strip(),
                msg="Operation Failed: " + ' '.join(map(str, command)),
                changed=False
            )

        return out if out else None

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

    # ==--------------------------------------------------------------------== #
    #
    # Return/Output  methods
    #
    # ==--------------------------------------------------------------------== #

    def send_exit(self, status_int, message, **kwargs):
        """
        Sends a module exit_json to Ansible. Include the following keyword
        arguments to output vcfm-complient JSON
        confluence.pluribusnetworks.com/pages/viewpage.action?pageId=12452428
        :param status_int: The status to be returned. Status 0 if success but no
        changes (idepotency), 1 is success and things were changed. Any other
        status is a general failure.
        :param message: The message to be sent back in the JSON response.
        :param kwargs: Unpacks all key word arguments into the module's exit
        json
        method.
        """

        change = False

        if status_int is 0 or status_int is 1:

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

    # ==--------------------------------------------------------------------== #
    #
    # Utility Methods
    #
    # ==--------------------------------------------------------------------== #

    def auto_accept_eula(self):
        """
        Accepts the EULA when Ansible logs into a new switch. This method is
        referenced from the auto_accept_eula in pn_initial_ztp.py
        :return: The output from the cli command sent to the target.
        """

        if 'pn_clipassword' not in self.module.params:
            self.send_exit(5, "Could not accept EULA, no password supplied")

        return self.send_command("--skip-setup --script-password "
                                 "switch-setup-modify password %s eula-accepted"
                                 " true" % self.module.params['pn_clipassword'])
