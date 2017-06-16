ZTP Bash script provides different functions like installing DHCP, configuring ONIE etc.
You need to provide correct arguments to ztp script which then configure your system accordingly.

Currently ZTP provides two main functions.
1.DHCP
2.ONIE

         ############## DHCP ############ 

Dhcpserver function will install dhcpserver,latest ansible and Pip Modules
DhcpServer function takes conf and csv files as arugment.

USAGE: 
       bash ztp.sh -dhcp [-conf] [-csv] [-reinstall]

EXAMPLE: 
       bash ztp.sh -dhcp -conf file.conf
       bash ztp.sh -dhcp -conf file.conf -csv file.csv
       bash ztp.sh -dhcp -conf file.conf -csv file.csv -reinstall_dhcp

Options:
   -h or -help:
       Display brief usage message.
   -conf:
       Reads conf file as input. This file contains network information required by switches.
       e.g netmask, domain-name etc

   -csv: [optional]
       Reads csv file as input. This section contains MAC, IP list, Hostname,TAG field and Inband ip entries which is required to create mac-ip mappings.
       MAC and IP address fields are compulsory. Please provide comma for optional fields if it does not have any value.
       Please check below Csv file example.

   -reinstall dhcp: [optional]
       Script will create new dhcpd.conf file from the contents of provided conf file. Otherwise it will append contents to present file.

=> Contents of file.conf:
# If you want to install ansible using GIT then provide GIT keyword in ansible_install_approach variable.Dont use quotes for value.(Default Value - OS-INSTALLER)
ansible_install_approach=OS-INSTALLER
# On what interfaces should the DHCP server (dhcpd) serve DHCP requests
dhcp_network_interface=eno16777984
# Netmask of DHCP server host
dhcp_subnet-mask=255.255.0.0
# Broadcast address of DHCP server host
dhcp_broadcast-address=10.9.255.255
# Routers for DHCP server host
dhcp_routers=10.9.9.1
dhcp_dns=10.9.10.1, 8.8.8.8
dhcp_domain-name=pluribusnetworks.com
dhcp_subnet_address=10.9.0.0
dhcp_range=10.9.1.1 10.9.1.100


=> Contents file.csv:
02:42:b4:c9:6d:1e,10.9.1.1,pikachu,spine
8c:89:a5:f4:28:2f,10.9.1.2,lapras,leaf
8c:89:a5:f4:23:1f,10.9.1.3,,spine
8c:89:a5:f3:28:2e,10.9.1.4,gyarados,,

       ################ ONIE ###########

ONIE function configures operating system on provided switch.
 - First It will install apache2
 - It will configure dhcpserver to lease ip address and url for operating system image.
 - In the end it will download image from given url and installs it on provided switch.

USAGE: 
       bash ztp.sh -onie -conf file.conf -csv file.csv [-online/offline] [-reinstall_dhcp]

EXAMPLE:  
       bash ztp.sh -onie -conf file.conf -csv file.csv -online
       bash ztp.sh -onie -conf file.conf -csv file.csv -offline
       bash ztp.sh -onie -conf file.conf -csv file.csv -online -reinstall_dhcp 
       bash ztp.sh -onie -conf file.conf -csv file.csv -offline -reinstall_dhcp

Options: 

   -h or -help:
       Display brief usage message.
   -conf:
       Reads conf file as input. This file is needed by dhcpserver script. This file contains network information required by switches.
       e.g netmask, domain-name etc

   -csv:
       Reads csv file as input. This file is needed by dhcpserver script. This section contains MAC, IP list, Hostname,TAG field and Inband ip entries which is required to create mac-ip mappings.
    
   -reinstall dhcp: [optional]
       Script will create new dhcpd.conf file from the contents of provided conf file. Otherwise it will append contents to present file.

=> Contents of file.conf:
# If you want to install ansible using GIT then provide GIT keyword in ansible_install_approach variable.Dont use quotes for value.(Default Value - OS-INSTALLER)
ansible_install_approach=OS-INSTALLER
# On what interfaces should the DHCP server (dhcpd) serve DHCP requests
dhcp_network_interface=eno16777984
# Netmask of DHCP server host
dhcp_subnet-mask=255.255.0.0
# Broadcast address of DHCP server host
dhcp_broadcast-address=10.9.255.255
# Routers for DHCP server host
dhcp_routers=10.9.9.1
dhcp_dns=10.9.10.1, 8.8.8.8
dhcp_domain-name=pluribusnetworks.com
dhcp_subnet_address=10.9.0.0
dhcp_range=10.9.1.1 10.9.1.100
default-url=http://dhcpserverip/images/onie-installer
username=ansible  #In case of online version
password=test123  #In case of online version
onie image version=2.5.1-10309 #In case of online version

=> Contents file.csv:
02:42:b4:c9:6d:1e,10.9.1.1,pikachu,spine
8c:89:a5:f4:28:2f,10.9.1.2,lapras,leaf
8c:89:a5:f4:23:1f,10.9.1.3,,spine
8c:89:a5:f3:28:2e,10.9.1.4,gyarados,,

# Pluribus Ansible Library Development Guide

The Pluribus Ansible Library, `pn_ansible_lib.py`, (library) is a useful tool for developing Pluribus Ansible modules. In combination with auto-generated python CLI wrappers, the library allows for pure scripting of the CLI. Using the library allows for the developer to not worry about interfacing with the CLI, and only worry about the logic required to script the various modules.

+ [Getting Started](#getting-started)
+ [Contributing to the Library](contributing-to-the-library)
+ [Advanced](advanced)
+ [Method Listing](method-listing)

## Getting Started

At the core of the library is a class called `PnCli` which sits on top of the CLI and handles input from the developer and returns data from the CLI. This class, when compiled, contains methods for interacting with the CLI as if it were attached directly to Python.

The library has two parts. The first part is a handwritten section of code that contains some useful tools for working with the CLI. The second part of the library is a set of auto-generated methods that wrap the CLI commands in Python code. These wrappers are the core functionality of the library, and are what we use to script the CLI.

While the full library of methods isn't documented here, they are easy to understand. The methods follow the same conventions as the CLI commands themselves. We use key word arguments and follow a rigid set of rules to use the methods in a concise and consistent way. All commands whose names contain `-` and all arguments whose name contains a `-` are converted to `_` in Python calls.

There are some CLI commands which take a parameter `if`, when using these commands in Python, the keyword for this parameter is `_if` to avoid conflict with the `if` keyword in Python.

There are 4 basic types of CLI parameters which are supported by the auto-generation engine. Their forms and usage are outlined below.

**Simple:** Simple commands take the form of `command argument value` where there is an argument that takes a single value. These end up as `cli.command(argument='value')` in the equivalent Python command.
**Single:** Single commands have arguments of the form `command argument` where there is a single argument with no associated value. As long as these are defined the command will generate correctly. As a convention we define these arguments as `True` in Python. `cli.command(argument=True)`.
**Array:** Array commands have multiple values that can be assigned to them. They take the form `command argument [ A | B | C ]`, where `A`, `B`, and `C` are the possible values for the argument. This turns into the equivalent code in Python: `cli.command(argument='A')` or `cli.command(argument='B')` or  `cli.command(argument='C')`.
**Choice:** Choice commands take the form `command [ choice-a, choice-b ]`. A common example would be the `show-headers` argument, which can be the binary choice `show-headers` or `no-show-headers`. The implementation in Python looks like: `cli.command(choice_a=True)` or `cli.command(choice_a=False)`. For a specific example, disabling headers in CLI responses would look as follows: `cli.command(show_headers=False)`.

### Examples
The following queries the CLI for the switch name of the current switch with `cli.switch_setup_show` and if the name is not present (The switch is named wrong) then we call `cli.switch_setup_modify` to rename the switch.
```Python
...
cli = PnCli(module)
if module.params['pn_current_switch'] not in \
       cli.switch_setup_show(format='switch-name', show_headers=False):
        cli.switch_setup_modify(switch_name=module.params['pn_current_switch'])
...
```
This example follows the CLI logic outlined below:
```
CLI > switch-setup-show format switch-name no-show-headers
ansible-leaf-1
CLI > switch-setup-modify switch-name ansible-leaf-2
```

The second example enables the web api on the switch.

```python
...
cli = PnCli(module)
if module.params['pn_web_api']:
    cli.admin_service_modify(web=True, _if='mgmt')
...
```
Which emulates the following on the CLI
```
CLI > admin-service-modify web if mgmt
```

## Contributing to the Library
Contributing to the shared library is easy! If you find a task or function that is repeated more than once in any playbook, that is a sign that the task or function should be moved to the library file instead of existing in multiple modules. Simply parameterize the function and replace calls in the calling file with calls to the library method.

Next, create test cases for your new method in the `pn_ansible_lib_tests.py` file. In writing tests take care to explore every single branch of logic in the method and any edge cases that you can think of. If you need to "fake" output from the CLI. Use the included `Module` class to add functionality to the psuedo-CLI. 

Before pushing any library changes, make sure that running `pylint` and `pep8 --max-line-length=80` both return no errors. We like to keep our codebase clean :) Also make sure that **ALL** affected modules are tested, in addition to running the library unit tests against the changes.

## Method Listing

+ [calc_link_ip_addr](#calc_link_ip_addr)
+ [\_\_init\_\_](#__init__)
+ [gen_command](#gen_command)
+ [send_command](#send_command)
+ [check_command](#check_command)
+ [check_command_string](#check_command_string)
+ [send_exit](#send_exit)
+ [auto_accept_eula](#auto_accept_eula)

### `calc_link_ip_addr`
This function is not part of the `PnCli` class. This function calculates all of the available link IP addresses for a given ip address, and returns an array of valid ips.
`calc_link_ip_addr(addr, cidr, supernet)`
**param addr:** The base ip address to use when calculating the link addresses.
**param cidr:** The CIDR notation for the set of link addresses you wish to create.
**param supernet:** The supernet for the addresses being created, this can be either 27, 28, 29, or 30.
**return:** Returns a list (array) of all available (assignable) link ip address with the given criteria.

### `__init__`
Initializes a PN_cli class. This class is used to interact with the Pluribus Command Line Interface of the destination switch.
`__init__(self, module, prefix='')`
**param module:** The `AnsibleModule` instance that the current module is using to send commands to the destination. For testing we can use any object, as long as it has the appropriate parameters that the called methods will look for. We use this for testing by creating a `Module` instance (see `pn_ansible_lib_test.py`) which mimics the commands typically returned by the CLI.
**param prefix:** The prefix that will be prepended to commands sent to the CLI by the `PN_cli` instance.

### `gen_command`
This is one of the core methods of the `PnCli` class. `gen_command` concatenates the instance's prefix with a command string, and takes an optional argument to prepend another string prior to the prefix. This is useful for creating commands that require `switch switch-name` in front of their actual command. The string `switch switch-name` can be set as the instance level prefix, and will be prepended to all of the commands sent to the CLI.
`gen_command(self, command, prepend='')`
**param command:** The command around which a generated command should be created.
**param prepend:** An optional argument which will add a string before the instance level prefix.
**return:** The generated command, which can be sent to the CLI or otherwise manipulated.

### `send_command`
This is another core method of the `PnCli` class. `send_command` does the heavy lifting of the class, and is responsible for actually sending the user-generated commands to the CLI. This method is also where errors will be caught and sent to the instance's AnsibleModule object.
`send_command(self, command)`
**param command:** The command that will be sent to the CLI. The command is sent as is, with no manipulation done by this method.
**return:** This method returns the output from the CLI, as a string, as is, upon successful completion of the command. If the command returns an error, this method will exit and print the error code to a AnsibleModule `exit_json` call. If the CLI command did not return an error or any output, this method returns `None` rather than a blank string.

### `check_command`
This method checks the output of a CLI command against a given string. This method can be thought of as a wrapper for `strcmp` implemented in Python.
`check_command(self, command, string)`
**param command:** The command being checked. The first string to compare.
**param string:** The string to check for in the command. The second string to compare.
**return:** `True` if the string is in the command, `False` otherwise.

### `check_command_string`
This is a legacy version of the `check_command` method. There are instances in the codebase where it is preferable to return a string documenting the status of the comparison rather than simply returning `True` or `False`, however, it is preferable to use `check_command` where possible instead of `check_command_string`.
`check_command_string(self, command, string, message)`
**param command:** The command being checked. The first string to compare.
**param string:** The string to check for in the command. The second string to compare.
**param message:** The message to be returned, typically the command being passed to the method.
**return:** Returns {message}: [Failed | Successful] based on whether or not the string was found in the command.

### `send_exit`
This is another core method in the `PnCli` class. This method sends an exit to the instance's `AnsibleModule` object. This is useful for cleanly closing out a module, without having to call the `exit_json` and `fail_json` methods yourself. This method is also used for sending VCFM data back to Ansible, and is accomplished by sending the relevant key word arguments to the `send_exit` command. These additional arguments are summary, task, and status, as outlined [here](        confluence.pluribusnetworks.com/pages/viewpage.action?pageId=12452428
). This status for VCFM is different from the `status_int` parameter.
`send_exit(self, status_int, message, **kwargs)`
**param status_int:** The status for the exit, 0 means no changes and the module was executed successfully, 1 means there were changes and the module executed successfully. Any other number means that the command failed and sends `fail_json` to the `AnsibleModule`.
**param message:**  The message to send the the `AnsibleModule`, this is the `msg` kwarg in `exit_json` and `fail_json`.
**param kwargs:** These are optional parameters for the Ansible output, any keyword arguments supplied here will be passed to the `AnsibleModule` and be output onto the console when the command finishes.
**return:** This method does not return anything. Any code after a call to this method will not be executed.

### `auto_accept_eula`
This method accepts the EULA when Ansible logs into a new switch. This method is actually a specific wrapper for the `send_command` method.
`auto_accept_eula(self)`
**return:** The output from the CLI command `--skip-setup --script-password switch-setup-modify password {password} eula-accepted true`.




