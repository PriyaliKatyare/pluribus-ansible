# Pluribus Networks - Ansible
 
# Index
  + [Ansible](#ansible)
  + [Getting Started](#getting-started)
    - [Installation](#installation)
    - [Control Machine Requirements](#control-machine-requirements)
    - [Managed Node Requirements](#managed-node-requirements)
  + [Inventory](#inventory)
  + [Configuration File](#configuration-file)
  + [Modules](#modules)
  + [Playbooks](#playbooks)
  + [Security](#security)
  + [Setup Key Based Authentication](#setup-key-based-authentication)
  + [Running Playbooks](#running-playbooks)
  + [Repository](#repository)
  + [Troubleshooting Utilities!](#troubleshooting-utilities)
  + [README_JSON.md](#readme_json)
  + [HowTo.md](#howto)
  + [Setup.md](#setup)
  
# Ansible
 Ansible is an open source IT automation tool for configuration management, provisioning and application deployment. Ansible is agentless and does not require a software agent to be installed on the target nodes. It uses SSH for secured communication with the target nodes. The Pluribus Networks Ansible library provides support for using Ansible to deploy, configure and manage devices running Netvisor OS. This repository contains modules developed for Netvisor OS CLI to perform specific tasks on devices running Netvisor OS. These modules run CLI commands for installing Netvisor OS, configuring, retrieving information/device statistics, modifying configuration settings on the target nodes. 

# Getting Started

## Installation
 Ansible by default manages machines over the SSH protocol. Ansible is installed on a control machine that manages one or more nodes. Managed nodes do not require any agent software. 

## Control Machine Requirements 
 The host you want to use as the control machine requires Python 2.6 or later. This control machine can be a desktop/laptop/workstation running a Linux based OS or any version of BSD. 
 The Ansible control machine requires the following software:
 
 * SSH
 * Python 2.6 or later
 * Ansible 1.8 or later release
   
 The steps for installing Ansible on Debian/Ubuntu is outlined here. 
 To get the latest version of Ansible:
 
```
  $ sudo apt-add-repository ppa:ansible/ansible -y                     
  $ sudo apt-get update && sudo apt-get install ansible -y
```

 To install Ansible on other platforms, please refer: [Ansible-Installation](https://docs.ansible.com/ansible/intro_installation.html)

## Managed Node Requirements
 Communication with managed nodes is over SSH. By default it uses sftp, but you can switch to scp in ansible.cfg
 As with the control machine, the managed nodes require Python 2.6 or later. (For nodes running Python 2.5 or lesser version, you may need python-simplejson)
 

# Inventory
 Ansible can work against multiple nodes in the infrastructure simultaneously. This is done by selecting a group of nodes in the Ansible's inventory file which is by default saved at /etc/ansible/hosts on the control machine. This file (see the default [hosts](hosts.sample) file)is configurable.
 
```
aquarius.pluribusnetworks.com
 
[spine]
gui-spine1 ansible_host=10.9.21.60 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-spine2 ansible_host=10.9.21.61 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"

[leaf]
gui-leaf1 ansible_host=10.9.21.62 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-leaf2 ansible_host=10.9.21.63 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-leaf3 ansible_host=10.9.21.64 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"
gui-leaf4 ansible_host=10.9.21.65 ansible_user="{{ SSH_USER }}" ansible_ssh_pass="{{ SSH_PASS }}" ansible_become_pass="{{ SSH_PASS }}"

[cisco-spine]
nexus9k-spine.pluribusnetworks.com

[arista-spine]
aristaeOs-spine.pluribusnetworks.com

[juniper-spine]
junos-spine.pluribusnetworks.com

[wan]
pn_wan

``` 

 Group names are enclosed in brackets and are used to classify systems based on purpose. 
 A node can be a part of multiple groups or none.
 Ansible allows us to specify corresponding host-dependent parameters in the hosts file itself. These variables can be used in the playbooks by enclsing them with flower brackets`{{ variable_name }}`. Some of these include:
 - **ansible_host** : Specify the name or IP address of the host to connect to.
 - **ansible_port** : Specify the non-standard SSH port if you're not using the default port 22.
 - **ansible_user** : Specify the SSH username to use.
 - **ansible_ssh_pass** : \*Specify the SSH password to use.
 - **ansible_become_pass** : \*Specify the privilage escalation password(sudo/su).
 - **ansible_ssh_private_key_file** : \*Specify the private key file used for password less SSH.
 
 \*Please note that these varaibles should not be stored as plain-text! You can store them in an AES encrypted vault file and access them as shown above. Lookup [Security](#security) for more on this.
 
 Please refer: [Ansible-Inventory](https://docs.ansible.com/ansible/intro_inventory.html) for more information on how to configure the hosts file.


# Configuration File
  Custom changes to the ansible workflow and how it behaves are made through the configuration file. If you installed ansible from a package manager, the `ansible.cfg` will be present in `/etc/ansible` directory. If it is not present, you can create one to override default settings. Although the default settings should be sufficient for most of the purposes, you may need to change some of the settings based on your requirements.
  The default configuration file can be found here: [ansible.cfg](ansible.cfg.sample)

**Checklist**:
  1. Make sure you set the library path to point to your library directory in the `ansible.cfg` file.
  2. Disable host key checking in `ansible.cfg` file. If required, establish SSH keys(Use [pn_autossh](/ansible/library/pn_autossh.py) module to easily setup SSH keys!).
  3. Make other configuration changes as required.

 Snapshot of example config file:

```
*** snippet ***
#inventory      = /etc/ansible/hosts
library        = /etc/ansible/pluribus-ansible/ansible/library/
#remote_tmp     = $HOME/.ansible/tmp
...
...
# uncomment this to disable SSH key host checking
host_key_checking = False
...
...
# if set, always use this private key file for authentication, same as
# if passing --private-key to ansible or ansible-playbook
#private_key_file = /path/to/file

# If set, configures the path to the Vault password file as an alternative to
# specifying --vault-password-file on the command line.
#vault_password_file = /path/to/vault_password_file
...
...
# You can set these parameters for individual plays in playbooks as well(preferred).
[privilege_escalation] 
#become=True
#become_method=sudo
#become_user=root
#become_ask_pass=False
*** snippet ***
```

# Modules
 Ansible modules reusable, standalone scripts that do the actual work. Modules get called and executed in playbook tasks.
 Modules return information to ansible in JSON format. Modules can be placed in different places where ansible looks for modules. As a convenience, we place them under library folder in our ansible project directory.
 
 **Pluribus Ansible Modules**
   Pluribus-Ansible modules support following configurations. These modules are idempotent. More information about these modules, options and their usage can be found in [Module Docs](/docs/module_docs). 
 
 - [pn_initial_ztp](ansible/library/pn_initial_ztp.py): To create/join fabric during zero touch provisioning.
 - [pn_l2_ztp](ansible/library/pn_l2_ztp.py): To auto configure vlags for layer2 fabric.
 - [pn_l3_ztp](ansible/library/pn_l3_ztp.py): To auto configure link IPs for layer3 fabric.
 - [pn_ztp_vrrp_l2](ansible/library/pn_ztp_vrrp_l2_csv.py): To configure VRRP (Virtual Router Redundancy Protocol) for layer2 fabric.
 - [pn_ztp_vrrp_l3](ansible/library/pn_ztp_vrrp_l3.py): To configure VRRP (Virtual Router Redundancy Protocol) for layer3 fabric.
 - [pn_ebgp_ospf](ansible/library/pn_ebgp_ospf.py): To configure eBGP/OSPF.
 - [pn_vflow](ansible/library/pn_flow.py): To create/delete/modify vFlows.
 - [pn_vxlan](ansible/library/pn_vxlan.py): To configure vxlan.
 - [pn_l1_mode](ansible/library/pn_l1_mode.py): To create link association between two switches which are not connected to each other.
 - [pn_switch_config_reset](ansible/library/pn_switch_config_reset.py): To reset the switch configuration to factory default.
 - [pn_show](ansible/library/pn_show.py): To execute CLI show commands.
 - [pn_vlan](ansible/library/pn_vlan.py): To create/delete/modify VLANs.
 - [pn_vlag](ansible/library/pn_vlag.py): To create/delete/modify VLAGs.
 - [pn_cluster](ansible/library/pn_cluster.py): To create/delete Clusters.
 - [pn_trunk](ansible/library/pn_trunk.py): To create/delete/modify Trunks(LAGs).
 - [pn_vrouter](ansible/library/pn_vrouter.py): To create/delete/modify vRouters.
 - [pn_vrouterif](ansible/library/pn_vrouterif.py): To add/remove vRouter interfaces(including VRRP).
 - [pn_vrouterlbif](ansible/library/pn_vrouterlbif.py): To add/remove vRouter Loopback interfaces.
 - [pn_vrouterbgp](ansible/library/pn_vrouterbgp.py): To add/remove vRouter BGP configurations.
 - [pn_ospf](ansible/library/pn_ospf.py): To add/remove vRouter OSPF configurations.

 
 Some of these Pluribus modules are included in the Ansible core modules library([Netvisor](http://docs.ansible.com/ansible/list_of_network_modules.html#netvisor)). You will have to clone this repository in your local machine to use other Pluribus modules. 
 To use pluribus-ansible modules or develop modules for pluribus-ansible, clone this repository in the path where you installed ansible. You can have it in a different project directory but make sure you modify the ansible.cfg file with relevant paths. 

```
~$ mkdir <directory-name>
~$ cd <directory-name>
~:<directory-name>$ git clone <url>
~:<directory-name>$ cd pluribus-ansible
~:<directory-name>/pluribus-ansible$ git checkout -b <your branch>
```

Now you can begin working on your branch.

# Playbooks
 Playbooks are Ansible's configuration, deployment and orchestration language. Playbooks are expressed in [YAML](https://docs.ansible.com/ansible/YAMLSyntax.html) format and have a minimum of syntax. Each playbook is composed of one or more plays. The goal of a play is to map a group of hosts to some well defined tasks. A task is basically a call to an Ansible Module. 
 
 **Pluribus Ansible Playbooks**
   Pluribus-Ansible also includes playbooks that use Pluribus modules to apply network configurations. These playbooks can be used to apply configurations with little modifications. These playbooks can also be used as reference/template to create your own playbooks. These playbooks are well organised and documented, describing the modules and parameters with description, and include debug messages, error handling as well as formatted output(pretty printed in JSON format) that describe each and every configuration that is being applied.
   The playbooks are organised in a directory structure, main playbooks in one folder(playbooks) and the playbook variables in vars folder(playbookvariables). The following is an example playbook for initial ZTP setup along with the associated vars file:

```
#Fabric creation
---


# This task is to configure initial ZTP setup on all switches.
# It uses pn_initial_ztp.py module from library/ directory.
# pn_cliusername and pn_clipassword comes from vars file - cli_vault.yml
# If the tasks fails then it will retry as specified by retries count.
- name: Zero Touch Provisioning - Initial setup
  hosts: all
  serial: 1
  become: true
  become_method: su
  become_user: root

  vars_files:
  - ../playbookvariables/cli_vault.yml
  - ../playbookvariables/vars_fabric_creation.yml

  tasks:
    - name: Auto accept EULA, Disable STP, enable ports and create/join fabric
      pn_initial_ztp:
        pn_cliusername: "{{ USERNAME }}"                              # Cli username (value comes from cli_vault.yml).
        pn_clipassword: "{{ PASSWORD }}"                              # Cli password (value comes from cli_vault.yml).
        pn_fabric_name: "{{ pn_fabric_name }}"                        # Name of the fabric to create/join.
        pn_current_switch: "{{ inventory_hostname }}"                 # Name of the switch on which this task is currently getting executed.
        pn_spine_list: "{{ groups['spine'] }}"                        # List of all spine switches mentioned under [spine] grp in hosts file.
        pn_leaf_list: "{{ groups['leaf'] }}"                          # List of all leaf switches mentioned under [leaf] grp in hosts file.
        pn_toggle_40g: "{{ pn_toggle_40g }}"                          # Flag to indicate if 40g ports should be converted to 10g ports or not.
        pn_inband_ip: "{{ pn_inband_ip }}"                            # Inband ips to be assigned to switches starting with this value. Default: 172.16.0.0/24.
        pn_fabric_network: "{{ pn_fabric_network }}"                  # Choices: in-band or mgmt.  Default: mgmt
        pn_fabric_control_network: "{{ pn_fabric_control_network }}"  # Choices: in-band or mgmt.  Default: mgmt
        pn_static_setup: "{{ pn_static_setup }}"                      # Flag to indicate if static values should be assign to following switch setup params. Default: True.
        pn_mgmt_ip: "{{ ansible_host }}"                              # Specify MGMT-IP value to be assign if pn_static_setup is True.
        pn_mgmt_ip_subnet: "{{ pn_mgmt_ip_subnet }}"                  # Specify subnet mask for MGMT-IP value to be assign if pn_static_setup is True.
        pn_gateway_ip: "{{ pn_gateway_ip }}"                          # Specify GATEWAY-IP value to be assign if pn_static_setup is True.
        pn_dns_ip: "{{ pn_dns_ip }}"                                  # Specify DNS-IP value to be assign if pn_static_setup is True.
        pn_dns_secondary_ip: "{{ pn_dns_secondary_ip }}"              # Specify DNS-SECONDARY-IP value to be assign if pn_static_setup is True.
        pn_domain_name: "{{ pn_domain_name }}"                        # Specify DOMAIN-NAME value to be assign if pn_static_setup is True.
        pn_ntp_server: "{{ pn_ntp_server }}"                          # Specify NTP-SERVER value to be assign if pn_static_setup is True.
        pn_web_api: "{{ pn_web_api }}"                                # Flag to enable web api. Default: True
        pn_stp: "{{ pn_stp }}"                                        # Specify True if you want to enable STP at the end. Default: False.

      register: ztp_out              # Variable to hold/register output of the above tasks.
      until: ztp_out.failed != true  # If the above code fails it will retry the code
      retries: 3                     # This is the retries count
      delay: 3
      ignore_errors: yes             # Flag to indicate if we should ignore errors if any.

    - debug:
        var: ztp_out.stdout_lines    # Print stdout_lines of register variable.

    - pause:
        seconds: 2                   # Pause playbook execution for specified amount of time.
```

  **and the associated variables file:**
 
```
---
#Fabric creation

pn_fabric_name: 'gui-fabric'                      # mandatory, , Name of the fabric to create/join, Fabric Name, text
pn_toggle_40g: True                               # optional, True:False, Flag to toggle/convert 40g ports to 10g ports, Toggle 40g, boolean
pn_inband_ip: '172.16.1.0/24'                     # optional, 172.16.0.0/24, Inband ips to be assigned to switches starting with this value, Inband IP, text
pn_fabric_network: 'mgmt'                         # optional, in-band:mgmt, Select fabric network type, Fabric Network, text
pn_fabric_control_network: 'mgmt'                 # optional, in-band:mgmt, Select fabric control network, Fabric Control Network, text
pn_static_setup: False                            # optional, True:False, Flag to indicate if static values should be assigned to following switch setup parameters, Static Setup, boolean
pn_mgmt_ip_subnet: '16'                           # optional, , Specify subnet mask for mgmt-ip to be assigned to switches, Mgmt IP Subnet, text
pn_gateway_ip: '10.9.9.0'                         # optional, , Specify gateway-ip to be assigned to switches, Gateway IP, text
pn_dns_ip: '10.20.41.1'                           # optional, , Specify dns-ip to be assigned to switches, DNS IP, text
pn_dns_secondary_ip: '10.20.4.1'                  # optional, , Specify dns-secondary-ip to be assigned to switches, DNS Secondary IP, text
pn_domain_name: 'pluribusnetworks.com'            # optional, , Specify domain-name to be assigned to switches, Domain Name, text
pn_ntp_server: '0.us.pool.ntp.org'                # optional, , Specify ntp-server value to be assigned to switches, NTP Server, text
pn_web_api: True                                  # optional, True:False, Flag to enable web api, Web API, boolean
pn_stp: False                                     # optional, True:False, Flag to enable STP at the end of configuration, STP, boolean 
```
 **Key Points** 
 - The variables file is included under the `vars_files` section by specifying its path relative to the playbook. 
 - The vault file is also included under the `vars_files` section by specifying its path relative to the playbook.(Vault file contains sensitive information like passwords.)
 - Parameters from vault file are accessed as `"{{ USERNAME }}"` and `"{{ PASSWORD }}"`.
 - The variables file is also written in YAML format.
 - Parameters from variables file are accessed as `"{{ pn_fabric_name }}"`.
 - Inventory or host parameters can be passed as `"{{ inventory_hostname }}"` and `"{{ ansible_host }}"`.
 - Hostnames from the inventory/hosts file can also be accessed using filters as `"{{ groups['spine'] }}"` and `"{{ groups['leaf'] }}"`. 
 - Certain modules take a comma separated file(csv file) as a parameter. You can use ansible provided lookup plugin to parse the csv file.
 
 ```
   ...
   ...
  vars_files:
  - ../playbookvariables/cli_vault.yml
  - ../playbookvariables/vars_l3_ztp.yml
  ...
  ...
  ...
       pn_spine_list: "{{ groups['spine'] }}"  # List of all spine switches mentioned under [spine] grp in hosts file.
       pn_leaf_list: "{{ groups['leaf'] }}"    # List of all leaf switches mentioned under [leaf] grp in hosts file.
       pn_csv_data: "{{ lookup('file', '{{ csv_file }}') }}"
  ...
  ...
  
 ```
 
 Following is the list of Pluribus playbooks available to the users:
 
 - [pn_initial_ztp.yml](ansible/playbooks/pn_initial_ztp.yml): This playbook allows Zero Touch Provisioning of switches automatically.  
 - [pn_l2_ztp.yml](ansible/playbooks/pn_l2_ztp.yml): This playbook allows users to provision their switches in L2 or Layer2 setup.
 - [pn_l3_ztp.yml](ansible/playbooks/pn_l3_ztp.yml): This playbook allows users to provision their switches in L3 or Layer3 setup. 
 - [pn_vrrp_l2_with_csv.yml](ansible/playbooks/pn_vrrp_l2_with_csv.yml): This playbook allows users to configue Layer2 VRRP at the Spine layer.
 - [pn_l3_vrrp_ebgp.yml](ansible/playbooks/pn_l3_vrrp_ebgp.yml): This playbook allows users to configure Layer3 VRRP at the Leaf layer along with eBGP configuration.
 - [pn_l3_vrrp_ospf.yml](ansible/playbooks/pn_l3_vrrp_ospf.yml): This playbook allows users to configure Layer3 VRRP at the Leaf layer along with OSPF configuration.
 - [pn_switch_reset.yml](ansible/playbooks/pn_switch_reset.yml): This playbook allows users to perform a switch config reset on the switches.
 - [pn_vlanshow.yml](ansible/roles/examples/pn_vlanshow.yml): This playbook allows users to run a vlan-show command on the network.
 - [pn_vlancreate.yml](ansible/roles/examples/pn_vlancreate.yml): This playbook allows users to create vlans.
 - [pn_vlagcreate.yml](ansible/roles/examples/pn_vlagcreate.yml): This playbook allows users to create vlags.
 - [pn_clustercreate.yml](ansible/roles/examples/pn_clustecreate.yml): This playbook allows users to create cluster configuration between two switches.

**Tip**:[YAML Lint](http://www.yamllint.com/) (online) helps you debug YAML syntax.
 
 
# Security
 Netvisor CLI has a one stage authentication process requiring login credentials to use CLI on devices running ONVL/nvOS. These credentials have to be passed to the Pluribus Ansible modules through playbooks via the parameters `pn_cliusername` and `pn_clipassword`. However it is not a best practice to provide plain-text login credentials for security reasons. These login credentials are not required if root login is enabled on target nodes but this is not recommended unless you have a good reason.
 Ansible Vault to the rescue!
   Ansible vault is a feature of ansible that allows keeping sensitive data such as passwords or keys in encrypted files rather than as plain-text in your playbooks or roles. 
   To enable this feature, a command line tool, `ansible-vault` is used to edit files and a command line flag `--ask-vault-pass` is used. If you have different credentials for different devices, you can encrypt them in `group_vars/` or `host_vars/` inventory variables,  variables loaded by `include_vars` or `vars_files`. 
   Please refer: [Ansible-Vault](http://docs.ansible.com/ansible/playbooks_vault.html) for more on this.
   
 **Creating Encrypted Files**
   To create a new encrypted data file, run the following command:
   
```
ansible-vault create foo.yml
```

  First you will be prompted for a password.
  After providing a password, the tool will launch an editor(defaults to vi). Here you can enter the sensitive data.

```
USERNAME: admin
PASSWORD: admin
```

  Once you have created the file, it will be saved as encrypted data. The default cipher is AES.
  
  The playbook will look like:
  
```
---
- name: vlan show using Vault encrypted file
  hosts: spine[0]
  user: pluribus
  
  vars_files:
  - foo.yml
  
  tasks:
  - name: Run vlan-show command
    pn_show: 
      pn_cliusername:{{ USERNAME }} 
      pn_clipassword={{ PASSWORD }} 
      pn_command=vlan-show
    register: show_output

  - debug: var=show_output
```

# Setup Key Based Authentication
  Ansible is SSH based. It will SSH into the hosts and apply the configurations as specified in the playbook. You will need to specify the remote user flag `-u` as well as `ask-pass or -k` for password everytime you run a playbook. Instead, you can setup SSH keys between your control machine and the target hosts for a more secured connection and avoid the hassle of providing the user and password everytime you run a playbook. You can use the Pluribus module to achieve auto-setup of SSH keys. Use this module+playbook the first time to setup key based authentication.

```
---
# This playbook is to setup SSH keys between localhost and remote switches.
# It uses the pn_autossh module.
# The list of switch IP addresses is passed as a csv file.
# The variables are located in vars_sshkeys.yml file.

- name: Auto SSH setup
  hosts: localhost

  vars_files:
    - ../playbookvariables/cli_vault.yml
    - ../playbookvariables/vars_sshkeys.yml

  tasks:
    - name: Generate SSH keys and push them onto switches
      pn_autossh:
        pn_user: "{{ remote_user }}"                               # Specify the remote user name(SSH user).
        pn_ssh_password: "{{ PASSWORD }}"                          # Specify the SSH password.
        pn_hosts_csv:  "{{ lookup('file', '{{ csv_file }}') }}"    # CSV file that contains (hostname, IP address).
        pn_overwrite: False                                        # Flag that specifies either to overwrite or append the authorization keys file in target hosts.
        pn_filepath: "{{ lookup('env','HOME') + '/.ssh/id_rsa' }}" # Specify the local path to save the generated rsa keys.
      register: output
      
    - debug: var=output.stdout_lines
```
 To setup SSH keys, run the following command:
 
```
$ ansible-playbook pn_autossh.yml --ask-vault-pass
```

# Running Playbooks
   Congratulations, You are now ready to run Pluribus-Ansible playbooks! Just kidding, not yet.
Playbooks can be run using the command `ansible-playbook playbook.yml [options][flags]`. But what are these options and flags?
Let's see the command with the various options/flags:
```
 $ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass -vvv 
```
**Options**:
 - **`ansible-playbook`** : The command to run ansible playbook.
 - **`playbook.yml`** : Name of the playbook that you want to run.
 
 **General Options**:
 - **`-i`** : inventory(host) file. 
   - The `-i` flag is followed by the hosts file.
   - Specify the hosts file name  if it is in the same directory as the playbook.
   - Specify the complete path of the hosts file if it is in a different directory.
   - If the `-i` flag is not specified, ansible will consider the hosts file located at `/etc/ansible/hosts`.
 - **`ask-vault-pass`** : ask for vault password when using vault file.
 - **`-v`** : verbose mode(-vv recommended, -vvv for more, -vvvv to enable cnnection debugging).
 
 **Connection Options**:
 - **`-k or --ask-pass`** : (lowercase 'k') ask for connection password.
   - SSH password.
   - Can be provided in the hosts file with vault protection.
   - We recommend setting up SSH key based authentication to avoid using username/password for a more secured connection.  
 - **`-u`** : remote user(generally SSH user, defaults to root!).
   - The `-u` flag is followed by the username.
   - You can specify the username in the hosts file in which case you dont have to provide this flag.
   - You can also set this in the ansible.cfg file(not recommended).
   - We recommend setting up SSH key based authentication to avoid using username/password for a more secured connection. 
   
 **Privilege Escalation Options**:
 - **`-b or --become`** : run operations with become. 
   - We recommend specifying this in the playbook.
 - **`--become-method=BECOME_METHOD`**: privilege escalation method to use.
   - Defaults to sudo. Valid choices: **sudo**, **su**, pbrun, pfexec, doas, dzdo, ksu.
 - **`--become-user=BECOME_USER`** : run operations as this user, defaults to root.
   - We recommend specifying this in the playbook.
 - **`-K or --ask-become-pass`** : (uppercase 'K') ask for privilege escalation password.
   - We recommend specifying this in the hosts file, with vault encryption.
   
Use the flags/options based on your requirements to run the playbooks. 

# Repository
  The modules, playbooks, module documentation and other related components are organised in various folders. This section provides a brief description of the directories and/or folders in this repository:
  - [`./docs`](./docs) : This folder cantains module documentation.
  - [`./ZTP`](./ZTP) : This folder contains ZTP bash script for installing DHCP, installing ONIE etc for configuring the system.
  - [`./ansible`](./ansible) : This folder contains sub-folders for Pluribus ansible module library and Pluribus ansible playbooks.
  - [`./ansible/library`](./ansible/library) : This folder contains the Pluribus Ansible modules. Make sure to include this as your library path in the ansible config file.
  - [`./ansible/playbooks`](./ansible/playbooks) : This folder contains all the playbooks for ZTP configurations. 
  - [`./ansible/roles`](./ansible/roles) : This folder contains all the playbooks for standalone modules.
  - [`./ansible/playbooks/tests`](./ansible/playbooks/tests) : This folder contains playbooks for testing the ZTP configurations. 
  - [`./ansible/playbooks/advance`](./ansible/playbooks/advance) : This folder contains playbooks specific to the VCF-Manager(GUI) based integration.
  - [`./ansible/playbooks/advance/playbooks`](./ansible/playbooks/advance/playbooks) : This folder contains the GUI specific playbooks.
  - [`./ansible/playbooks/advance/playbookvariables`](./ansible/playbooks/advance/playbookvariables) : This folder contains vars files for GUI specific playbooks.


# Troubleshooting Utilities
  In this section, we describe certain linux utilities that can come in handy while troubleshooting for issues.
  
  **Playbook Logs**
  
  The only way to check the output of the ansible playbook is to use `register` and `debug` modules in playbooks to capture output from the modules. This is because ansible requires module output in JSON format and does not support print statements in module. It is therefore recommended to have some level of verbosity flags while running the playbooks. 
  You can also log the output of the playbook in a log file for later inspection. There are many ways to capture output into log files. Two of them are discussed here:

   - **`I/O redirection`** : Most command line programs that display their results do so by sending their results to standard output. By default, standard output directs its contents to the display. To redirect standard output to a file(overwrite), the `>` character is used.
  
```
  $ ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass > playbookoutput.log
```
  or you can use `>>` to append to a file:

```
  $ ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass >> playbookoutput.log
```

   - **`tee`** : The I/O redirection only redirects the output to a file, it does not display the output on the screen. Tee command is used to save and view (both at the same time) the output of any command. Tee command writes to the STDOUT, and to a file at a time(`-a` for append):
  
```
  $ ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass | tee -a playbookoutput.log  
```
  
  **Execution Time**
  
  You can also time the execution of the playbook by using the linux `time` utility.

```
  $ time ansible-playbook -i hosts playbook.yml -u pluribus -K --ask-pass --ask-vault-pass | tee -a playbookoutput.log
```
 
 This will give the time it took for the playbook to run. 
 
 ```
  real	47m17.075s
  user	6m33.070s
  sys	0m57.437s
 ```
 
 # README_JSON

# Index
  + [Synopsis](#synopsis)
  + [Structure](#structure)
  + [Code example](#code-example)
  + [Configuration](#configuration)
  + [Algorithm behind the working](#algorithm-behind-the-working)

---
# Synopsis:

To have Ansible playbooks' results in json format with standard output payload  

---
## Structure:

**The high-level skeleton for json object is:**  
```  
__________ANSIBLE_TASK_BOUNDARY_STARTS__________
{  
    "plays": [  
        {  
            "play": {  
                "id":   
                "name":  
            },  
            "tasks": [  
                {  
                    "status": {},  
                    "hosts": {},  
                    "task": {  
                        "id":   
                        "name":   
                    }  
                }  
            ]  
        }  
    ]  
}  
__________ANSIBLE_TASK_BOUNDARY_ENDS__________
```

Every json object is wrapped with 2 messages:  
 * `__________ANSIBLE_TASK_BOUNDARY_STARTS__________` notifying the start of the json object  
 * `__________ANSIBLE_TASK_BOUNDARY_ENDS__________` notifying the end of the json object  

The standard json object starts with a `plays` field. `plays` field is the highest level field in the json object.  
 
 * `plays` field contains **play** and **tasks** which are next level of field.
   * `play` tells about the description of a play. It contains **name** and **id**  
      * `name` - It gives the name of the `play`  
      * `id` - It gives id of the `play`  
   * `tasks` tells about description of the task in the play. The `tasks` field contains **status**, **hosts** and **task**  
      * `status` tells about the success or failure of the task. It can contain 3 values:  
          * _0_ - for success  
          * _1_ - for failure  
          * _Cannot determine_ - if there is a weird behaviour  
      * `task` field contains task name and task id of the task which is running.  
      * `hosts` field contains the host name where the task execution is happening and host name contains the various attributes for a task which tells about the details on execution of a task in that host.  

### There are 6 fixed attributes inside the hosts field which are:  

`task` - name of task  
`summary` - the json output command by command with the switch name in which it is executing  
`msg` - short message related to the task  
`failed` - true/false depending upon the execution of the task  
`exception` - in case of any exception while running the modules  
`unreachable` - in case of connection issues or some entity is unreachable  

---
## Code example:

**One of the example for the json object is:**
```
__________ANSIBLE_TASK_BOUNDARY_STARTS__________
{
    "plays": [
        {
            "play": {
                "id": "d00eb3af-a4d3-4887-9cdb-2eb26d11ee69",
                "name": "Zero Touch Provisioning - Initial setup"
            },
            "tasks": [
                {
                    "hosts": {
                        "ansible-spine1": {
                            "_ansible_no_log": false,
                            "_ansible_parsed": true,
                            "attempts": 1,
                            "changed": true,
                            "exception": "",
                            "failed": false,
                            "invocation": {
                                "module_args": {
                                    "pn_clipassword": "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER",
                                    "pn_cliusername": "network-admin",
                                    "pn_current_switch": "ansible-spine1",
                                    "pn_dns_ip": null,
                                    "pn_dns_secondary_ip": null,
                                    "pn_domain_name": null,
                                    "pn_fabric_control_network": "mgmt",
                                    "pn_fabric_name": "ztp-fabric",
                                    "pn_fabric_network": "mgmt",
                                    "pn_gateway_ip": null,
                                    "pn_inband_ip": "172.16.0.0/24",
                                    "pn_mgmt_ip": null,
                                    "pn_mgmt_ip_subnet": null,
                                    "pn_ntp_server": null,
                                    "pn_static_setup": false,
                                    "pn_stp": false,
                                    "pn_toggle_40g": true,
                                    "pn_web_api": true
                                },
                                "module_name": "pn_initial_ztp_json"
                            },
                            "msg": "Initial ZTP configuration executed successfully",
                            "summary": [
                                {
                                    "output": "Eula has already been accepted",
                                    "switch": "ansible-spine1"
                                },
                                {
                                    "output": "Already a part of fabric ztp-fabric",
                                    "switch": "ansible-spine1"
                                },
                                {
                                    "output": "Fabric is already in mgmt control network",
                                    "switch": "ansible-spine1"
                                },
                                {
                                    "output": "STP is already disabled",
                                    "switch": "ansible-spine1"
                                },
                                {
                                    "output": "Ports enabled",
                                    "switch": "ansible-spine1"
                                },
                                {
                                    "output": "In-band ip has already been assigned",
                                    "switch": "ansible-spine1"
                                },
                                {
                                    "output": "In-band ip has already been assigned",
                                    "switch": "ansible-spine1"
                                }
                            ],
                            "task": "Auto accept EULA, Disable STP, enable ports and create/join fabric",
                            "unreachable": false
                        }
                    },
                    "status": "0",
                    "task": {
                        "id": "02f08ed7-b84c-4dcb-9b6e-58564636c423",
                        "name": "Auto accept EULA, Disable STP, enable ports and create/join fabric"
                    }
                }
            ]
        }
    ]
}
__________ANSIBLE_TASK_BOUNDARY_ENDS__________
```

---
## Configuration:

A **json callback plugin** needs to be used to get the desired results in json.  

The name of json plugin is `pn_json.py` which can be found in the locations below:  
1. https://github.com/amitsi/pluribus-ansible/tree/release-2.2.0/ansible  
2. https://github.com/amitsi/pluribus-ansible/tree/master/ansible

Then the `pn_json plugin` needs to be put in the following location:  
1. **/usr/lib/python2.7/dist-packages/ansible/plugins/callback**  

> Note: The plugin needs to be kept in the server machine from where the ansible execution is taking place.  

Then the following changes have to be added in `/etc/ansible/ansible.cfg` configuration file:  
a) gathering = explicit  
b) stdout\_callback = pn\_json  

---
## Algorithm behind the working:  

* Get the **task name** from `task` field  
*  Then the `status` field has to be checked  
  * if `status` field is '1':  
     * Then take the **short error message** from the `msg` field. And **detailed error message** from either `exception/summary/stderr/stdout` field  
  * elif `status` field is '0':  
     * Then take the **short success message** from `msg` field. And the get the **detailed output** from the `summary` field.  
  * else (`status` field is '-1'):  
     * It is some weird behaviour. Pluribus team needs to be notified.  
---

# HowTo
## Setup Ansible Config

Update the following in /etc/ansible/ansible.cfg to appropriate location:

```
library        = /etc/ansible/pluribus-ansible/ansible/library
```

And also uncomment the following:

```
host_key_checking = False
```

## Run playbooks

### Switch-Config-Reset Playbook

Playbook command:

```
# ansible-playbook -i hosts pn_switch_reset.yml -u pluribus --ask-pass --ask-vault-pass -K
```

Output snippet:

```
--snip--
PLAY [Switch Config Reset] *****************************************************

TASK [setup] *******************************************************************
ok: [ansible-leaf2]
ok: [ansible-leaf3]
ok: [ansible-leaf1]
ok: [ansible-spine2]
ok: [ansible-spine1]
ok: [ansible-leaf4]

TASK [Reset all switches] ******************************************************
ok: [ansible-leaf3]
ok: [ansible-leaf2]
ok: [ansible-leaf1]
ok: [ansible-spine1]
ok: [ansible-spine2]
ok: [ansible-leaf4]
.
.
PLAY RECAP *********************************************************************
ansible-leaf1              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf2              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf3              : ok=3    changed=0    unreachable=0    failed=0
ansible-leaf4              : ok=3    changed=0    unreachable=0    failed=0
ansible-spine1             : ok=4    changed=0    unreachable=0    failed=0
ansible-spine2             : ok=3    changed=0    unreachable=0    failed=0
--snip--
```

### Fabric Playbook

Playbook command:

```
# ansible-playbook -i hosts pn_fabric.yml -u pluribus --ask-pass --ask-vault-pass -K
```

Output snippet:

```
--snip--
PLAY [Zero Touch Provisioning - Initial setup] *********************************

TASK [setup] *******************************************************************
ok: [ansible-spine1]

TASK [Auto accept EULA, Disable STP, enable ports and create/join fabric] ******
changed: [ansible-spine1]

TASK [debug] *******************************************************************
ok: [ansible-spine1] => {
    "ztp_out.stdout_lines": [
        "  EULA has been accepted already!  ansible-spine1 is already in fabric vcf-ansible-fab!  Fabric is already in mgmt control network  STP is already disabled!  Ports enabled on ansible-spine1! "
    ]
}
.
.
PLAY RECAP *********************************************************************
ansible-leaf1              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf2              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf3              : ok=4    changed=1    unreachable=0    failed=0
ansible-leaf4              : ok=4    changed=1    unreachable=0    failed=0
ansible-spine1             : ok=4    changed=1    unreachable=0    failed=0
ansible-spine2             : ok=4    changed=1    unreachable=0    failed=0
--snip--
```

### Fabric Playbook - L2 with VRRP

Create a CSV file. Sample CSV file:
```
# cat pn_vrrp_l2.csv
101.108.100.0/24, 100, test-spine1
101.108.101.0/24, 101, test-spine1
101.108.102.0/24, 102, test-spine2
101.108.103.0/24, 103, test-spine2
```

Modify CSV file path in YML file:

```
  vars:
  - csv_file: /pluribus-ansible/ansible/pn_vrrp_l2.csv  # CSV file path.
```

Playbook command:

```
# ansible-playbook -i hosts pn_vrrp_l2_with_csv.yml -u pluribus --ask-pass --ask-vault-pass -K
```

### Fabric Playbook - L3

Playbook command:

```
# ansible-playbook -i hosts pn_ztp_l3.yml -u pluribus --ask-pass --ask-vault-pass -K
```

Output snippet:

```
PLAY [Zero Touch Provisioning - Initial setup] *********************************

TASK [setup] *******************************************************************
ok: [gui-spine1]

TASK [Auto accept EULA, Disable STP, enable ports and create/join fabric] ******
changed: [gui-spine1]

TASK [debug] *******************************************************************
ok: [gui-spine1] => {
    "ztp_out.stdout_lines": [
        "  EULA accepted on gui-spine1!  gui-spine1 has joined fabric vz-fab!  Configured fabric control network to mgmt on gui-spine1!  STP disabled on gui-spine1!  Ports enabled on gui-spine1!  Toggled 40G ports to 10G on gui-spine1! "
    ]
}
.
.
TASK [debug] *******************************************************************
ok: [gui-spine1] => {
    "ztp_l3_out.stdout_lines": [
        "  Created vrouter gui-spine2-vrouter on switch gui-spine2   Created vrouter gui-spine1-vrouter on switch gui-spine1   Created vrouter gui-leaf4-vrouter on switch gui-leaf4   Created vrouter gui-leaf3-vrouter on switch gui-leaf3
 Created vrouter gui-leaf2-vrouter on switch gui-leaf2   Created vrouter gui-leaf1-vrouter on switch gui-leaf1   Added vrouter interface with ip 172.168.1.1/30 on gui-leaf1!  Added BFD config to gui-leaf1-vrouter  Added vrouter interface
with ip 172.168.1.2/30 on gui-spine1!  Added BFD config to gui-spine1-vrouter  Added vrouter interface with ip 172.168.1.5/30 on gui-leaf2!  Added BFD config to gui-leaf2-vrouter  Added vrouter interface with ip 172.168.1.6/30 on gui-spin
e1!  Added BFD config to gui-spine1-vrouter  Added vrouter interface with ip 172.168.1.9/30 on gui-leaf3!  Added BFD config to gui-leaf3-vrouter  Added vrouter interface with ip 172.168.1.10/30 on gui-spine1!  Added BFD config to gui-spin
e1-vrouter  Added vrouter interface with ip 172.168.1.13/30 on gui-leaf4!  Added BFD config to gui-leaf4-vrouter  Added vrouter interface with ip 172.168.1.14/30 on gui-spine1!  Added BFD config to gui-spine1-vrouter  Added vrouter interf
ace with ip 172.168.1.17/30 on gui-leaf1!  Added BFD config to gui-leaf1-vrouter  Added vrouter interface with ip 172.168.1.18/30 on gui-spine2!  Added BFD config to gui-spine2-vrouter  Added vrouter interface with ip 172.168.1.21/30 on g
ui-leaf2!  Added BFD config to gui-leaf2-vrouter  Added vrouter interface with ip 172.168.1.22/30 on gui-spine2!  Added BFD config to gui-spine2-vrouter  Added vrouter interface with ip 172.168.1.25/30 on gui-leaf3!  Added BFD config to g
ui-leaf3-vrouter  Added vrouter interface with ip 172.168.1.26/30 on gui-spine2!  Added BFD config to gui-spine2-vrouter  Added vrouter interface with ip 172.168.1.29/30 on gui-leaf4!  Added BFD config to gui-leaf4-vrouter  Added vrouter
interface with ip 172.168.1.30/30 on gui-spine2!  Added BFD config to gui-spine2-vrouter   Added loopback ip for vrouter gui-spine2-vrouter!  Added loopback ip for vrouter gui-spine1-vrouter!  Added loopback ip for vrouter gui-leaf4-vrout
er!  Added loopback ip for vrouter gui-leaf3-vrouter!  Added loopback ip for vrouter gui-leaf2-vrouter!  Added loopback ip for vrouter gui-leaf1-vrouter! "
    ]
}

TASK [pause] *******************************************************************
Pausing for 2 seconds
(ctrl+C then 'C' = continue early, ctrl+C then 'A' = abort)
ok: [gui-spine1]

PLAY RECAP *********************************************************************
gui-leaf1                  : ok=4    changed=1    unreachable=0    failed=0
gui-leaf2                  : ok=4    changed=1    unreachable=0    failed=0
gui-leaf3                  : ok=4    changed=1    unreachable=0    failed=0
gui-leaf4                  : ok=4    changed=1    unreachable=0    failed=0
gui-spine1                 : ok=8    changed=2    unreachable=0    failed=0
gui-spine2                 : ok=4    changed=1    unreachable=0    failed=0
```

### Fabric Playbook - L3 with VRRP

Create a CSV file. Sample CSV file:

```
# cat pn_vrrp_l3.csv
100, 172.168.100.0/24, test-leaf1, test-leaf2, 19, test-leaf1
101, 172.168.101.0/24, test-leaf3
102, 172.168.102.0/24, test-leaf4
104, 172.168.104.0/24, test-leaf1, test-leaf2, 19, test-leaf1
```

Modify CSV file path in YML file:

```
  vars:
  - csv_file: /etc/ansible/pluribus-ansible/ansible/pn_vrrp_l3.csv  # CSV file path.
```

Playbook command:

```
# ansible-playbook -i hosts pn_vrrp_l2_with_csv.yml -u pluribus --ask-pass --ask-vault-pass -K
```

# Setup.md
This document aims to help you get started with Pluribus Ansible and provides some tips to make the most of your ansible experience.
Ansible also has a comprehensive official documentation which is [amazing](#http://docs.ansible.com/ansible/index.html)!. You can refer it for more information. 

## Setup

```
  $ sudo apt-add-repository ppa:ansible/ansible -y                     
  $ sudo apt-get update && sudo apt-get install ansible -y
```
This will install ansible on your machine. To begin using pluribus-ansible modules or develop modules for pluribus-ansible, clone this repository in your ansible directory.

```
~$ cd /etc/ansible
~:/etc/ansible$ git clone <url>
~:/etc/ansible$ cd pluribus-ansible
~:/etc/ansible/pluribus-ansible$ git checkout -b <your branch>
```

Now you can begin working on your branch.

#NOTE: 
Checklist:
  1. Make sure you set the library path to point to your library directory in the `ansible.cfg` file.
  2. Disable host key checking in `ansible.cfg` file. If required, establish SSH keys.
  3. Make any required configuration changes.
 
## Index
+ [Directory Layout](#directory-layout)
+ [Configuration File](#configuration-file)
+ [Inventory File](#inventory-file)
+ [Group and Host variables](#group-and-host-variables)
+ [Playbooks](#playbooks)
+ [Module Development](#modules)

# Directory Layout
  This section tries to explains a typical directory structure for organizing contents of your project.
  The top level of the directory would contain files and directories like:
```
  /path/to/ansible/
  |-main.yml
  |-hosts
  |-library/
   '--pn_show.py
  |-group_vars/
  |-host_vars/
  |-roles/
```
  `group_vars`, `host_vars`, `roles` provide scalability, reusability and better code organization.

# Configuration File
  Custom changes to the ansible workflow and how it behaves are made through the configuration file. If you installed ansible from a package manager, the `ansible.cfg` will be present in `/etc/ansible` directory. If it is not present, you can create one to override default settings. Although the default settings should be sufficient for most of the purposes, you may need to change some of the settings based on your requirements.
  The default configuration file can be found here: [ansible.cfg](../ansible.cfg)

  Changes in relation to configuration are processed and picked up in the the following order:
```
  1. * ANSIBLE_CONFIG (an environment variable)
  2. * ansible.cfg (in the current directory)
  3. * .ansible.cfg (in the home directory)
  4. * .ansible.cfg (in /etc/ansible/ansible.cfg)
```
  An example directive from the config file:
```
  #inventory = /etc/ansible/hosts
```
  This line is to assign a different directory for a custom hosts file location. Remember to remove the `#` symbol to uncomment.

# Inventory File
  Inventory is a list of hosts, assembled into groups, on which you will run your ansible playbooks. Ansible works against multiple hosts in your infrastructure simultaneously. It does this by selecting a group of hosts listed in Ansible’s inventory file. Ansible has a default inventory file used to define which hosts it will be managing. After installation, there's an example one you can reference at `/etc/ansible/hosts`.
  Copy and move the default [hosts]() file for reference:
```
  $ sudo mv /etc/ansible/hosts /etc/ansible/hosts.orig
  $ sudo vim /etc/ansible/hosts
```
  Note: You can place the `hosts` file in your current working directory and change the inventory path in the `ansible.cfg` file.

  Here is an example of inventory file located in the ansible working directory ~/ansible/hosts
```
  mail.example.com

  [webservers]
  foo.example.com
  bar.example.com

  [dbservers]
  serverone.example.com
  servertwo.example.com
  serverthree.example.com
```
  Ansible automatically puts all the hosts in a group called **`all`**.
  Group names are enclosed in brackets `[]` and are used to classify hosts based on purpose.
  A host can be a part of multiple groups or none. There can be multiple inventory files and they can also be dynamic.
  Please refer: [Ansible-Inventory](https://docs.ansible.com/ansible/intro_inventory.html) for more on this.

# Group and Host variables
  Ansible allows you to have different inventory files for different environments. These inventory files contain various host classified into different groups based on environment, geographic location, scope etc. These groups and hosts can be associated with variables relative to the inventory file. Please refer: [Ansible-vars] (http://docs.ansible.com/ansible/playbooks_best_practices.html#how-to-differentiate-staging-vs-production) for more on this.

# Roles
  Roles are a way to automatically load certain vars_files, tasks and handlers based on the file structure. Roles are good for organizing multiple, related Tasks and encapsulating data needed to accomplish those Tasks. A role contains various optional directories besides `tasks` and each sub-directory contains an entrypoint `main.yml`. The other directories can be handlers, defaults, templates and files.

  - `tasks`: You can include a list of tasks that you would implement across different plays and playbooks in `tasks/main.yml` and include them in your main playbook using `include` directive.
  - `handlers`: A handler is exactly similar to Task, but it will run only when called by another task(similar to an event system). This is useful to run secondary tasks that might be required after running a task. Ths is achieved using the `notify` directive in the parent task.
  - `defaults`: This contains defaults for variables used in the roles.
  - `files`:
  - `templates`:

# Modules
  Ansible modules are reusable piece of code that can be invoked using the ansible API or through the Ansible playbook. Although Ansible modules can be written in any language, Python is the preferred choice. The Ansible module should be capable of handling different arguments, return statuses, errors and failures. This can be achieved by the **AnsibleModule** boilerplate which provides an efficient way to handle arguments and return statuses.

## AnsibleModule boilerplate
  All you need to do is import `ansible.module_utils.basic`
  Put the import function at the end of your file and include your actual module body inside the conventional `main` function.
```
from ansible.module_utils.basic import AnsibleModule
if __name__ == '__main__':
    main()
```

  Module class can be instantiated as follows:
```
def main():
    module = AnsibleModule(
        argument_spec = dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            something = dict(aliases=['whatever'])
        )
    )
```
  As you can see, the **AnsibleModule** boilerplate allows you to specify if the arguments are optional or required, set default values. It also handles different data types.

##  Interaction between parameters:
   The **AnsibleModule** boilerplate also offers interaction between the arguments. It allows you to specify if certain arguments are mutually exclusive or required together. An argument can be `required` or `optional`. You can set `default` values to optional arguments. Also, the possible inputs to a particular argument can be restricted using `choice` keyword.
```
    module = AnsibleModule(
        argument_spec=dict(
            state     = dict(default='present', choices=['present', 'absent']),
            name      = dict(required=True),
            enabled   = dict(required=True, type='bool'),
            something = dict(aliases=['whatever']),
            argument1 = dict(type='str'),
            argument2 = dict(type='str')
        ),
        mutually_exclusive=[
            [ "argument1", "argument2"]
        ],
        required_together=[
            [ "name", "state"]
        ],
        required_one_of=dict=[
            ["state", "something"]
        ],
        required_if=[
            ["state", "present", ["enabled", "argument1", "something"],
            ["state", "absent", ["enabled", "argument2"]
        ]
    )
```
  `mutually_exclusive` - takes a list of lists and ech embedded list consists of parameters which cannot appear together.
  `required_together` - all the specified parameters are required together
  `required_one_of` - at least one of the specified parameters is required
  `required_if` - it checks the value of one parameter and if that value matches, it requires the specified parameters to be present as well.

##  Accessing the arguments:
   Ansible provides an easy way to access arguments from the module instance.
```
    state = module.params['state']
    name = module.params['name']
    enabled = module.params['enable']
    something = module.params['something']
    argument1 = module.params['argument1']
    argument2 = module.params['argument2']
```

  Modules must output valid JSON. **AnsibleModule** boilerplate has a common function, `module.exit_json` for JSON format output. Successful returns are made using:
```
    module.exit_jason(
        changed = True,
        stdout = response
    )

    or

    module.exit_json(
        changed = False,
        stdout = response
    )
```
  Failures are handled in a similar way:
```
    module.fail_json(
        changed = False,
        msg="Something Failed!"
     )
```

##  Documentation:
   All modules must be documented. The modules must include a `DOCUMENTATION` string. This string must be a valid **YAML** document.
```
    #!/usr/bin/python
    # Copyright/License header

    DOCUMENTATION = '''
    ---
    module: modulename
    short_description: A sentence describing the module
    # ... snip...
    '''
```

  The description field supports formatting functions such as `U()`, `M()`, `I()` and `C()` for URL, module, italics and constant width respectively. It is suggested to use `C()` for file and option names, `I()` when referencing parameters, and `M()` for module names.

##  Examples:
   Example section must be written in plain text in an `EXAMPLES` string within the module.

```
    EXAMPLES = '''
    - action: modulename opt1=arg1 opt2=arg2
```

##  Return:
   The `RETURN` section documents what the module returns. For each returned value, provide a `description`, in what circumstances the value is `returned`, the `type` of the value and a `sample`.
```
    RETURN = '''
    - return_value:
        description: short description for the returned value
        returned:
        type:
        sample:
    '''
```

# Playbooks
   The real strength of Ansible lies in Playbooks. A playbook is like a recipe or instruction manual which tells ansible what to do when it connects to each machine. Playbooks are expressed in YAML format and have a minimum of syntax. Each playbook is composed of one or more plays. The goal of a play is to map a group of hosts to some well defined tasks. A task is basically a call to ansible module. The good thing about playbooks is that there is no defined format, you can write a playbook in different ways. You can organize plays, tasks in different ways. You can also add modularity with the help of `roles`. 
     
  Here is an example of a playbook to run `vlan-show`:
```
    ---
    - name: "This Playbook is to view Vlan configurations."
      hosts: spine
      user: network-admin
      
      tasks:
      - pn_show: username=network-admin password=admin pn_showcommand=vlan-show pn_showformat=switch,id,desc pn_quiet=True
      register: vlan_show_output
      - debug: var:vlan_show_output
```

   A few things to note:

   - Nearly every YAML file starts with a list. Each item in the list is a list of key/value pairs, commonly called a “hash” or a “dictionary”.
   - All YAML files can optionally begin with `---` and end with `...`. This is part of the YAML format and indicates the start and end of a document.
   - It is possible to leave off the ‘name’ for a given task, though it is recommended to provide a description about why something is being done instead. This name is shown when the playbook is run.
   - Generous use of whitespace to break things up, and use of comments (which start with ‘#’), is encouraged.
   - All members of a list are lines beginning at the same indentation level starting with a `- ` (a dash and a space).
   - [YAML Lint](#http://www.yamllint.com/) can help you debug YAML syntax.
  
## The Following Modules are supported with Software release 2.4.1:
   - LAG
   - vLAG
   - VLAN
   - Port Configuration
   - vRouters
   - VRRP
   - BGP
   - OSPF
   - Pluribus CLI as a parameter (allows to configure any new feature)

   
   The official [Ansible doc](#http://docs.ansible.com/ansible/playbooks.html) provides more information on Playbooks and YAML. 





 