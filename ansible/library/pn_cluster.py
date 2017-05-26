#!/usr/bin/python
""" PN CLI cluster-create/cluster-delete """

# Copyright 2016 Pluribus Networks
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess
import shlex
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: pn_cluster
author: "Pluribus Networks"
version: 1.0
short_description: CLI command to create/delete a cluster.
description:
  - Execute cluster-create or cluster-delete command.
  - A cluster allows two switches to cooperate in high-availability (HA)
    deployments. The nodes that form the cluster must be members of the same
    fabric. Clusters are typically used in conjunction with a virtual link
    aggregation group (VLAG) that allows links physically connected to two
    separate switches appear as a single trunk to a third device. The third
    device can be a switch,server, or any Ethernet device.
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
  pn_cliswitch:
    description:
      - Target switch to run the cli on.
    required: False
    type: str
  pn_command:
    description:
      - The C(pn_command) takes the cluster-create/cluster-delete command
        as value.
    required: true
    choices: ['cluster-create', 'cluster-delete']
    type: str
  pn_name:
    description:
      - Specify the name of the cluster.
    required: true
    type: str
  pn_cluster_node1:
    description:
      - Specify the name of the first switch in the cluster.
      - Required for 'cluster-create'.
    type: str
  pn_cluster_node2:
    description:
      - Specify the name of the second switch in the cluster.
      - Required for 'cluster-create'.
    type: str
  pn_validate:
    description:
      - Validate the inter-switch links and state of switches in the cluster.
    choices: ['validate', 'no-validate']
    type: str
"""

EXAMPLES = """
- name: create spine cluster
  pn_cluster:
    pn_command: 'cluster-create'
    pn_name: 'spine-cluster'
    pn_cluster_node1: 'spine01'
    pn_cluster_node2: 'spine02'
    pn_validate: validate
    pn_quiet: True

- name: delete spine cluster
  pn_cluster:
    pn_command: 'cluster-delete'
    pn_name: 'spine-cluster'
    pn_quiet: True
"""

RETURN = """
command:
  description: the CLI command run on the target node(s).
stdout:
  description: the set of responses from the cluster command.
  returned: always
  type: list
stderr:
  description: the set of error responses from the cluster command.
  returned: on error
  type: list
changed:
  description: Indicates whether the CLI caused changes on the target.
  returned: always
  type: bool
"""

NAME_EXISTS = None
NODE1_EXISTS = None
NODE2_EXISTS = None

def pn_cli(module):
    """
    This method is to generate the cli portion to launch the Netvisor cli.
    It parses the username, password, switch parameters from module.
    :param module: The Ansible module to fetch username, password and switch
    :return: returns the cli string for further processing
    """
    username = module.params['pn_cliusername']
    password = module.params['pn_clipassword']
    cliswitch = module.params['pn_cliswitch']

    if username and password:
        cli = '/usr/bin/cli --quiet --user %s:%s ' % (username, password)
    else:
        cli = '/usr/bin/cli --quiet '

    cli += ' switch-local ' if cliswitch == 'local' else ' switch ' + cliswitch
    return cli


def check_cli(module, cli):
    """
    This method checks for idempotency using the cluster-show command.
    If a cluster with given name exists, return NAME_EXISTS as True else False.
    If the given cluster-node-1 is already a part of another cluster, return
    NODE1_EXISTS as True else False.
    If the given cluster-node-2 is already a part of another cluster, return
    NODE2_EXISTS as True else False.
    :param module: The Ansible module to fetch input parameters
    :param cli: The CLI string
    :return Global Booleans: NAME_EXISTS, NODE1_EXISTS, NODE2_EXISTS
    """
    name = module.params['pn_name']
    node1 = module.params['pn_cluster_node1']
    node2 = module.params['pn_cluster_node2']

    show = cli + ' cluster-show  format name,cluster-node-1,cluster-node-2 '
    show = shlex.split(show)
    out = module.run_command(show)[1]

    out = out.split()
    # Global flags
    global NAME_EXISTS, NODE1_EXISTS, NODE2_EXISTS

    NAME_EXISTS = True if name in out else False
    NODE1_EXISTS = True if node1 in out else False
    NODE2_EXISTS = True if node2 in out else False


def run_cli(module, cli):
    """
    This method executes the cli command on the target node(s) and returns the
    output. The module then exits based on the output.
    :param cli: the complete cli string to be executed on the target node(s).
    :param module: The Ansible module to fetch command
    """
    cliswitch = module.params['pn_cliswitch']
    command = module.params['pn_command']
    cmd = shlex.split(cli)
    response = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                                stdout=subprocess.PIPE, universal_newlines=True)
    # 'out' contains the output
    # 'err' contains the error messages
    out, err = response.communicate()

    print_cli = cli.split(cliswitch)[1]

    # Response in JSON format
    if err:
        module.exit_json(
            command=print_cli,
            stderr=err.strip(),
            msg="%s operation failed" % command,
            changed=False
        )

    if out:
        module.exit_json(
            command=print_cli,
            stdout=out.strip(),
            msg="%s operation completed" % command,
            changed=True
        )

    else:
        module.exit_json(
            command=print_cli,
            msg="%s operation completed" % command,
            changed=True
        )


def main():
    """ This section is for arguments parsing """
    module = AnsibleModule(
        argument_spec=dict(
            pn_cliusername=dict(required=False, type='str'),
            pn_clipassword=dict(required=False, type='str'),
            pn_cliswitch=dict(required=False, type='str', default='local'),
            pn_command=dict(required=True, type='str',
                            choices=['cluster-create', 'cluster-delete']),
            pn_name=dict(required=True, type='str'),
            pn_cluster_node1=dict(type='str'),
            pn_cluster_node2=dict(type='str'),
            pn_validate=dict(type='bool')
        ),
        required_if=(
            ["pn_command", "cluster-create",
             ["pn_name", "pn_cluster_node1", "pn_cluster_node2"]],
            ["pn_command", "cluster-delete", ["pn_name"]]
        )
    )

    # Accessing the parameters
    command = module.params['pn_command']
    name = module.params['pn_name']
    cluster_node1 = module.params['pn_cluster_node1']
    cluster_node2 = module.params['pn_cluster_node2']
    validate = module.params['pn_validate']

    # Building the CLI command string
    cli = pn_cli(module)

    if command == 'cluster-create':

        check_cli(module, cli)

        if NAME_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Cluster with name %s already exists' % name
            )
        if NODE1_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Node %s already part of a cluster' % cluster_node1
            )
        if NODE2_EXISTS is True:
            module.exit_json(
                skipped=True,
                msg='Node %s already part of a cluster' % cluster_node2
            )

        cli += ' %s name %s ' % (command, name)
        cli += 'cluster-node-1 %s cluster-node-2 %s ' % (cluster_node1,
                                                         cluster_node2)
        if validate is True:
            cli += ' validate '
        if validate is False:
            cli += ' no-validate '

    if command == 'cluster-delete':

        check_cli(module, cli)

        if NAME_EXISTS is False:
            module.exit_json(
                skipped=True,
                msg='Cluster with name %s does not exist' % name
            )
        cli += ' %s name %s ' % (command, name)

    run_cli(module, cli)

# AnsibleModule boilerplate

if __name__ == '__main__':
    main()
