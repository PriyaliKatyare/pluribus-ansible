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

