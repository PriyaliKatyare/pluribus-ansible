#!/usr/bin/env bash

cd ../

##
# Function to trap and display error messages.
##
function error() {
  echo -e "\e[0;33mERROR: The ZTP script failed while running the command $BASH_COMMAND at line $BASH_LINENO.\e[0m" >&2
  exit 1
}
trap error ERR

RED='\033[0;31m'
NC='\033[0m'

##
# Function to trap and display error messages.
##
default_conf_file="# If you want to install ansible using GIT then provide GIT keyword in ansible_install_approach variable.Dont use quotes for value.(Default Value - OS-INSTALLER)
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
dhcp_range=10.9.1.1 10.9.1.100"

##
# Sample csv file structure for DHCP.
##
default_csv_file="02:42:b4:c9:6d:1e,10.9.1.1,pikachu,spine
8c:89:a5:f4:28:2f,10.9.1.2,lapras,leaf
8c:89:a5:f4:23:1f,10.9.1.3,,spine
8c:89:a5:f3:28:2e,10.9.1.4,gyarados,,"

##
# Sample csv file structure for ONIE.
##
default_csv_file_onie="02:42:b4:c9:6d:1e,10.9.1.1,pikachu,spine,671232X1646008,10g
8c:89:a5:f4:28:2f,10.9.1.2,lapras,leaf,671232X1645002,40g
8c:89:a5:f4:23:1f,10.9.1.3,,spine,,10g
8c:89:a5:f3:28:2e,10.9.1.4,gyarados,spine,,40g"

##
# The help content displayed when -h/-help is given as input.
##
help="
${RED}NAME${NC}
     ztp — Script to configure DHCP, ONIE etc
                  to check availability of provided hosts

${RED}SYNOPSIS${NC}
     bash ztp.sh [-h/-help] [-dhcp] [-onie] [-conf file.conf] [-csv file.csv] [-reconfigure_dhcp] 
                 [-skip_ansible] [-all_online] [-all_offline]  [-online_onie] [-offline_onie] [-online_license] [-offline_license] [-checkallsystemsgo]

${RED}OPTIONS${NC}

     -h or -help:        Display brief usage message.
   
     -dhcp:              This field will install dhcpserver and ansible. 

     -onie:              This field configures your system to act as a ONIE Server.

     -conf:              Reads conf file as input. This file contains network information required by switches. e.g netmask, domain-name, dns etc

     -csv:               Reads csv file as input. This section contains MAC, IP list, Hostname,TAG field and Inband ip entries which is required to create mac-ip mappings.
                         MAC and IP address fields are compulsory. Please provide comma for optional fields if it does not have any value.
                         Please check below CSV file example.
  
     -reconfigure_dhcp:  Script will create new dhcpd.conf file from the provided conf file. Otherwise it will append contents to present file.

     -skip_ansible:      This field will skip installations of ansible, python and pip modules.

     -all_online:        In this field script will download onie image,activate keys, download keys and copy it to mentioned switches.
      [Not recommended for first run]: In first run we can not copy keys before installing os on switches.

     -all_offline:       In this field user needs to download ONIE image and activation keys manually.

     -online_onie:       This field will download ONIE image automatically. User just need to provide versio of image in conf file.
 
     -offline_onie:      In this field user needs to download ONIE image manually and keep it in web server directory. i.e /var/www/html/images
 
     -online_license:    This field will download activation keys automatically.

     -offline_license:   In this field user needs to download activation keys manually.
 
     -checkallsystemsgo: This field will check availability of all the hosts mentioned in the CSV file.

${RED}EXAMPLES: ${NC}
     bash ztp.sh -dhcp -conf file.conf
     bash ztp.sh -dhcp -conf file.conf -csv file.csv
     bash ztp.sh -dhcp -conf file.conf -csv file.csv -reconfigure_dhcp
     bash ztp.sh -dhcp -conf file.conf -csv file.csv -reconfigure_dhcp -skip_ansible
     bash ztp.sh -onie -conf file.conf -csv file.csv -all_online -skip_ansible
     bash ztp.sh -onie -conf file.conf -csv file.csv -all_offline -skip_ansible
     bash ztp.sh -onie -conf file.conf -csv file.csv -offline_onie -skip_ansible
     bash ztp.sh -onie -conf file.conf -csv file.csv -online_onie -reconfigure_dhcp
     bash ztp.sh -onie -conf file.conf -csv file.csv -offline_license -reconfigure-dhcp
     bash ztp.sh -onie -conf file.conf -csv file.csv -online_license -skip_ansible
     bash ztp.sh -onie -conf file.conf -csv file.csv -offline_license 
     bash ztp.sh -checkallsystemsgo

${RED}=> For DHCP : Contents of file.conf:${NC}
$default_conf_file

${RED}=> For DHCP : Contents of file.csv:${NC}
$default_csv_file

${RED}=> For ONIE : Contents of file.conf ${NC}
$default_conf_file
default-url=http://dhcpserverip/images/onie-installer
username=ansible  #In case of online version
password=test123  #In case of online version
onie_image_version=2.5.1-10309 #In case of online version

${RED}=> For ONIE: Contents of file.csv:${NC}
$default_csv_file_onie

"
##
# Checks operating system type on the basis of *-release file.
##
if [ -f "/etc/redhat-release" ]; then
OS="Centos"
elif [ -f "/etc/lsb-release" ]; then
OS="Ubuntu"
fi

csv_file=""
processCsv=0
device_id=()
device_type=()
ip_arr=()
script_dir=`pwd`

##
# This function validates ipaddress and mac address field from CSV file.
# Checking whether the ip address and mac address are correct.
# Checking whether the number of arguements in csv files are correct.
#     If -dhcp: the least comma count required is 2.
#     If -onie: the least comma count required is 4.
# Arguments : csv file
##
validate_csv()
{
  # CSV File validation
  cd $script_dir
  params=$@
  processCsv=0
  if [[ "$params" == *"-csv"* ]]; then
    csv_file=`echo "${params#*-csv[$IFS]}" | awk '{ print $1 }'`

    if [ ! -e $csv_file  ]; then
    echo -e "\nCSV file is not present or not in readable format\n"
      exit 0
    else
      comma_count=0
      if [[ "$params" == *"-dhcp"* ]]; then
        comma_count=2
      elif [[ "$params" == *"-onie"* ]]; then
        comma_count=4
      fi

      # Checking no of fields in csv file(basically checks for no of commas(min: 3))
      for line in `cat $csv_file` ;
      do
        commas=`echo $line | awk -F "," '{print NF-1}'`
        if [ "$commas" -le "$comma_count" ];then
          printf "\n\nPlease provide correct arguments separated by commas. Use ,, inplace of optional value. Check sample csv file from Help\n\n"
          exit 0
        fi
      done
 
      #Checking whether user has provided correct mac and ip addresses
      for line in `cat $csv_file` ;
      do
        mac_address=`echo $line | cut -d "," -f1`
        ip_address=`echo $line | cut -d "," -f2`

        if [[ "$mac_address" =~ ^([a-fA-F0-9]{2}:){5}[a-fA-F0-9]{2}$ ]]; then
          if [[ $ip_address =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            processCsv=1
          else
            printf "${RED}Check your CSV file. Please provide ip address in correct format${NC}\n"
            exit 0
          fi
        else
          printf "${RED}Check your CSV file. Please provide mac address in correct format${NC}\n"
          exit 0
        fi
      done
    fi
  fi
}

##
# This function installs Ansible using GIT 
##
install_ansible_using_git()
{
  ansible_directory="/etc/ansible"
  if [ -d "$ansible_directory" ]; then
    sudo rm -r $ansible_directory
  fi
  cd /etc/
  sudo git clone git://github.com/ansible/ansible.git --recursive
  cd ./ansible
  sudo -s source ./hacking/env-setup
  sudo easy_install pip
}


##
# This function configures dhcp server
# This function will also install ansible and pip modules, if user has not specified -skip_ansible option. 
# If user has provided -reconfigure_dhcp option then function will reconfigure dhcpd.conf file. Otherwise it will just keep appending to new entries in conf file.
# The function checks for the availabilty of csv file and conf file and validate them.
# It installs ansible, python, pip, dhcp for Ubuntu and Centos according to the operating system.
# It downloads the yml files from the git repo.
# It creates host blocks in dhcpd.conf on the basis of csv file input.
# Arguments: conf file and csv file
##
dhcpserver()
{
  printf "\n>Configuring DHCP server\n"
  params=$@
  conf_file=`echo "${params#*-conf[$IFS]}" | awk '{ print $1 }'`

  #Parsing conf file for different network values
  if [ ! -e "$conf_file"  ]; then
    echo -e "\nConfiguration file is not present or not in readable format.Try providing full path of file.\n"
    exit 0
  else
    interface=`cat "$conf_file" | grep 'dhcp_network_interface' | cut -d = -f2`
    subnet_mask=`cat "$conf_file" | grep 'dhcp_subnet-mask' | cut -d = -f2`
    broadcast_address=`cat "$conf_file" | grep 'dhcp_broadcast-address' | cut -d = -f2`
    routers=`cat "$conf_file" | grep 'dhcp_routers' | cut -d = -f2`
    dns=`cat "$conf_file" | grep 'dhcp_dns' | cut -d = -f2`
    domain_name=`cat "$conf_file" | grep 'dhcp_domain-name' | cut -d = -f2`
    subnet=`cat "$conf_file" | grep 'dhcp_subnet_address' | cut -d = -f2`
    range=`cat "$conf_file" | grep 'dhcp_range' | cut -d = -f2`
  fi

  if [[ "$params" == *"-csv"* ]]; then
    validate_csv "$params"
  fi

  ansible_install_approach=`cat $conf_file | grep 'ansible_install_approach=' | cut -d = -f2`

  #First it checks for OS type and then installs dhcp, ansible, python and pip
  if [ $OS == "Ubuntu" ]; then
      sudo apt-get -qq update -y
      sudo apt-get -qq install isc-dhcp-server -y
      sudo sed -i '/INTERFACES=/c INTERFACES="'$interface'"' /etc/default/isc-dhcp-server
      dhcp_restart_command='sudo service isc-dhcp-server restart'
      if ! [[ "$params" == *"-skip_ansible"* ]]; then
        if [ "$ansible_install_approach" == "GIT" ]; then
          #Installing latest Ansible - Using git
          sudo apt-get -y install git
          install_ansible_using_git
        elif [ "$ansible_install_approach" == "OS-INSTALLER" ]; then
          #Installing latest Ansible - Using apt-get
          sudo apt-get -qq install software-properties-common
          sudo apt-add-repository -y ppa:ansible/ansible
          sudo apt-get -qq update
          sudo apt-get -qq -y install ansible
          sudo apt-get -qq -y install python
          sudo apt-get -qq -y install python-pip
        fi
        sudo pip install paramiko PyYAML Jinja2 httplib2 six > /dev/null
      else
        printf "\n  -Skipping Ansible installations"
      fi
  elif [ $OS == "Centos" ]; then
      sudo yum -y update
      sudo yum -y install dhcp
      count=`cat /etc/sysconfig/dhcpd | grep 'DHCPDARGS=' | wc -l`
      if [ $count == "1" ]; then
        sed -i "/DHCPDARGS=/c DHCPDARGS=$interface" /etc/sysconfig/dhcpd
      else
        echo "DHCPDARGS=$interface" >> /etc/sysconfig/dhcpd
      fi
      dhcp_restart_command='sudo systemctl restart dhcpd'
      if ! [[ "$params" == *"-skip_ansible"* ]]; then
        if [ "$ansible_install_approach" == "GIT" ]; then
          sudo yum -y install git
          install_ansible_using_git
        elif [ "$ansible_install_approach" == "OS-INSTALLER" ]; then
          sudo yum -y -q install epel-release
          sudo yum -y -q update
          sudo yum -y -q install ansible
          sudo yum -y -q install python
          sudo yum -y -q install python-pip
        fi 
      else   
        printf "\n  -Skipping Ansible installations"
      fi
  fi

  #check if user has provided -skip_ansible, if no then download the yml files
  if ! [[ "$params" == *"-skip_ansible"* ]]; then
    ymlfiles=(bgpsetup.yml bgpteardown.yml cli_vault.yml l2setup.yml l2teardown.yml main.yml pn_ebgp.yml pn_fabric.yml pn_fabric_l3_ebgp.yml pn_l2.yml pn_l2_ztp.yml pn_l3.yml pn_l3_ebgp.yml pn_l3_ztp.yml pn_vrrp.yml)
    sudo mkdir -p /etc/ansible
    cd /etc/ansible
    for i in ${ymlfiles[@]}; do
      sudo wget --quiet https://raw.githubusercontent.com/amitsi/pluribus-ansible/master/ansible/playbooks/$i -O $i
    done
  fi

#check if dhcpd.conf file has any configuration
check_conf_exists=`cat /etc/dhcp/dhcpd.conf | grep '#DHCP SERVER CONF FILE' | wc -l`

  #check if user has provided -reconfigure-dhcp, if yes it will recreate dhcpd.conf file
  if [[ $check_conf_exists == 0 ]] || [[ "$params" == *"-reconfigure_dhcp"* ]]; then
sudo sh -c "echo '#DHCP SERVER CONF FILE
# option definitions common to all supported networks...
default-lease-time 600;
max-lease-time 7200;
# If this DHCP server is the official DHCP server for the local
# network, the authoritative directive should be uncommented.
authoritative;
# Use this to send dhcp log messages to a different log file (you also
# have to hack syslog.conf to complete the redirection).
log-facility local7;

subnet $subnet netmask $subnet_mask {  #network
  range $range; # Range
  option domain-name-servers $dns; #Pri DNS , Sec DNS
  option domain-name \"$domain_name\"; #Domain name
  option routers $routers; #Gateway
  option broadcast-address $broadcast_address; #Broadcast
  default-lease-time 600;
  max-lease-time 7200;
}
' > /etc/dhcp/dhcpd.conf"
  fi

  #Following will parse csv file and wil create host blocks in dhcpd.conf file
  if [ $processCsv == 1 ]; then

    #Appending dhcpd.conf file with mac-ipaddress entries
    spinehostnames=()
    leafhostnames=() 
    spineips=()
    leafips=()
  

    for line in `cat $csv_file` ;
    do
      arr=()
      IFS=',' read -a arr <<< "$line"
      mac=${arr[0]}
      ip=${arr[1]}
      ip_arr+=(${arr[1]})
      hostname=${arr[2]}
      tag=${arr[3]}
      device_id+=(${arr[4]})
      device_type+=(${arr[5]})
  
      check_mac_entry_exists=`cat /etc/dhcp/dhcpd.conf | grep "$mac" | wc -l`
      check_ip_entry_exists=`cat /etc/dhcp/dhcpd.conf | grep "$ip" | wc -l`
      if [ -z "$hostname" ]; then
        check_hostname_entry_exists=0
      else
        check_hostname_entry_exists=`cat /etc/dhcp/dhcpd.conf | grep "$hostname" | wc -l`
      fi

      if [ -z $hostname ]; then
      host_block="host $ip {
  hardware ethernet $mac;
  fixed-address $ip;
"
      else
      host_block="host $hostname {
  hardware ethernet $mac;
  fixed-address $ip;
  option host-name \"$hostname\";
"
     fi

      if [[ "$params" == *"-onie"* ]]; then
        url=`cat $conf_file | grep 'default-url=' | cut -d = -f2`
        host_block="$host_block  option default-url=\"$url\";"
      fi
  host_block="$host_block
}"

      if [ $check_mac_entry_exists == 0 ] && [ $check_ip_entry_exists == 0 ] && [ $check_hostname_entry_exists == 0 ]; then
        sudo sh -c "echo '$host_block' >> /etc/dhcp/dhcpd.conf"
      fi

      if ! [ -z "$tag" ]; then
        if [ "$tag" == "spine"  ]; then
          spinehostnames+=($hostname)
          spineips+=($ip)
        else
          leafhostnames+=($hostname)
          leafips+=($ip)
        fi
      else
        printf "\n  -Tag(spine/leaf) is not provided for host:$hostname. This host is not added in /etc/ansible/hosts file"
      fi
    done
    
    #if user has not provided -skip_ansible flag, then only following code will get executed.
    #this code creates host file for ansbile from csv file
    if ! [[ "$params" == *"-skip_ansible"* ]]; then
      echo "[spine]" > /etc/ansible/hosts
      for ((j=1; j<=${#spineips[@]}; j++)); do
        echo "${spinehostnames[j-1]} ansible_host=${spineips[j-1]}" >> /etc/ansible/hosts
      done

      echo -e "\n" >> /etc/ansible/hosts

      echo "[leaf]" >> /etc/ansible/hosts
      for ((j=1; j<=${#leafips[@]}; j++)); do
        echo "${leafhostnames[j-1]} ansible_host=${leafips[j-1]}" >> /etc/ansible/hosts
      done
    fi

  fi #end of processCsv

  #Restart dhcp server
  eval $dhcp_restart_command
}

##
# Following function will copy activation key file to all switches which are mentioned in the csv file.
# The keys are stored in license_10g folder for 10g activation key.
# The keys are stored in license_40g folder for 40g activation key.
##
copy_activations_keys()
{
  sleep 1
  ten_g_keyfile_path="/var/www/html/images/license_10g/onvl-activation-keys"
  fourty_g_keyfile_path="/var/www/html/images/license_40g/onvl-activation-keys"
  
  if [ ! -e "$ten_g_keyfile_path"  ] || [ ! -e "$fourty_g_keyfile_path"  ]; then
    echo -e "\n  -Key files are not present in /var/www/html/images/license_10g, /var/www/html/images/license_40g directories."
    exit 0
  else  
    sudo apt-get -y -qq install expect
    printf "\n  -Copying Activation keys to Switches"
    default_username=""
    default_password=""
    printf "\n  -I need username and password for the switches to copy key files. Shall I use default pluribus user credentials(y/n):"
    read choice
    if [ "$choice" == "y" ] || [ "$choice" == "y" ] || [ "$choice" == "yes" ] || [ "$choice" == "Yes" ]; then
      default_username="pluribus"
      default_password="test123"
    elif [ "$choice" == "n" ] || [ "$choice" == "no" ] || [ "$choice" == "No" ] || [ "$choice" == "N" ]; then
      printf "\n  -Please provide username for the switch:"
      read username
      printf "\n  -Please provide username for the switch:"
      read password
      default_username=$username
      default_password=$password
    else
      printf "\n  -You have provided wrong input:"
      exit 0
    fi

    filename=""
    for ((j=1; j<=${#ip_arr[@]}; j++)); do
      if [ "${device_type[j-1]}" == "10g" ]; then
        filename="/var/www/html/images/license_10g/onvl-activation-keys"
      elif [ "${device_type[j-1]}" == "40g" ]; then
        filename="/var/www/html/images/license_40g/onvl-activation-keys"
      fi
## TODO :  Add Eula accept code , add sftp enable code here###
sudo /usr/bin/expect <<EOD
set timeout 300
spawn /usr/bin/sftp $default_username@${ip_arr[j-1]}
expect "*?assword:"
send "$default_password\n"
expect "sftp>"
send "put $filename /sftp/import\r"
expect "sftp>"
send "bye\r"
sleep 2
interact
EOD
  
    done
  fi
}

##
# This function configures your server to act as a ONIE.
# This function will install apache2 and JQ parser.
# It will configure ONIE OS and License either automatically or manually as per user input flags.
# The function provides all possible options of onie(online as well as offline) provisioning.
# The function provides all possible options of licensing(online as well as offline).
# Arguments: conf file and csv file.
##
onie()
{
  printf "\n>Configuring ONIE\n\n"
  declare params=$@
  conf_file=`echo "${params#*-conf[$IFS]}" | awk '{ print $1 }'`
  validate_csv "$params"
  cd $script_dir
  #install apache2 server
  printf "  -Updating system respositories\n"
  sudo apt-get -y -qq update
  printf "  -Installing apache2\n"
  sudo apt-get -y -qq install apache2
  printf "  -Installed apache2 successfully\n"

  dhcpserver "$params"
  printf "\n\n>Backto : Configuring ONIE\n"
  sleep 1
  cd $script_dir
  username=""
  password=""
  csrftoken=""
  comma_count=4
  cookie_file_name="/tmp/cookie"

  #If command line arguments contains 'online' word , it will configure jq json parser
  if [[ "$params" == *"online"* ]]; then
    printf "\n  -configuring JQ json parser"
    if ! [ -f ./jq ]; then
      sudo wget --quiet http://stedolan.github.io/jq/download/linux64/jq
    fi
    sudo chmod +x ./jq
    sudo cp jq /usr/bin
    username=`cat $conf_file | grep 'username=' | cut -d = -f2`
    password=`cat $conf_file | grep 'password=' | cut -d = -f2`
  fi

  #If user wants to configure both onie and license online
  if [[ "$params" == *"-all_online"* ]];then
    mkdir -p /var/www/html/images
    mkdir -p /var/www/html/images/license_10g
    mkdir -p /var/www/html/images/license_40g
    version=`cat $conf_file | grep 'onie_image_version=' | cut -d = -f2`
    login_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/login -d login_email=$username\&login_password=$password -k -c $cookie_file_name`
    login_result=`echo $login_json | jq '.success'`

    if ! [ "$login_result" == true ]; then
      printf "\n -Login failed: cloud-web.pluribusnetworks.com. Please provide correct credentials in conf file\n"
      exit 0
    else
      csrftoken=`cat $cookie_file_name | grep -Po '(csrftoken\s)\K[^\s]*'`
    fi

    #check if device_id field is empty or not. If empty then setting no_device_id=1
    no_device_id=0
    for ((j=1; j<=${#device_id[@]}; j++)); do
      commas=`echo $line | awk -F "," '{print NF-1}'`
      if [ -z "${device_id[j-1]}" ];then
        no_device_id=1
        break
      fi
    done

    if [ "${#device_id[@]}" == 0 ]; then
      no_device_id=1
    fi

    #Downloading order_detail in the form of json
    order_details_json=`curl -s -X GET https://cloud-web.pluribusnetworks.com/api/orderDetails -b $cookie_file_name -k`
    order_detail_id=`echo $order_details_json | jq '.order_details[0].id'`
    order_detail_id_40g=`echo $order_details_json | jq '.order_details[1].id'` 

    #check if device_ids are provided or not in csv file. if not then script can get it from switches(else part).
    if [ "$no_device_id" == 0 ]; then
      i=0
      for id in "${device_id[@]}"; do
        printf "\n  -Activating key"
        if [ "${device_type[i]}" == "40g" ]; then
          order_detail_id=$order_detail_id_40g
        fi
		
	#Api call for orderActivation
        activation_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/orderActivations -d order_detail_id=$order_detail_id\&device_ids=$id\&csrfmiddlewaretoken=$csrftoken -b $cookie_file_name -k`
        activation_result=`echo $activation_json | jq '.success'`
        if ! [ "$activation_result" == true ]; then
          printf "\n  -Unable to activate key for Device: $id"
        fi
        i=$((i+1))
        order_detail_id=`echo $order_details_json | jq '.order_details[0].id'`
      done
      printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id ..\n"
      curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id -b $cookie_file_name -k > /var/www/html/images/license_10g/onvl-activation-keys
      printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id_40g ..\n"
      curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id_40g -b $cookie_file_name -k > /var/www/html/images/license_40g/onvl-activation-keys
      #copy_activations_keys
    else
      printf "\n  -Device ids are not provided for all switches in CSV file. I can get device ids from the switches.\n   But make sure nvOS is running and DHCP IP is assigned to all switches mentioned in the CSV file.\n   ${RED}Shall I login to switches and get device id Enter (y/n)?:${NC}"
      read device_choice 
      all_device_id=() 
      if [ $device_choice == "y" ]; then
        for ((j=1; j<=${#ip_arr[@]}; j++)); do
          for ((i=1; i<=3; i++)); do
            ####TODO#### Need to change below line
            ID=`ssh -o StrictHostKeyChecking=no root@${ip_arr[j-1]} 'onie-syseeprom' | grep 'Serial Number' | awk '{ print $5 }'`
            if ! [ -z $ID ]; then
              all_device_id+=($ID)           
              break
            fi   
          done 
        done
        i=0
        for id in "${all_device_id[@]}"
        do
          printf "\n  -Activating key"
          if [ "${device_type[i]}" == "40g" ]; then
            order_detail_id=$order_detail_id_40g
          fi
		  
	  #Api call for orderActivation
          activation_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/orderActivations -d order_detail_id=$order_detail_id\&device_ids=$id\&csrfmiddlewaretoken=$csrftoken -b $cookie_file_name -k`
          activation_result=`echo $activation_json | jq '.success'`
          if ! [ "$activation_result" == true ]; then
            printf "\n  -Unable to activate key for Device: $id"
          fi
          i=$((i+1))
          order_detail_id=`echo $order_details_json | jq '.order_details[0].id'`
        done
        printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id ..\n"
        curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id -b $cookie_file_name -k > /var/www/html/images/license_10g/onvl-activation-keys
        printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id_40g ..\n"
        curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id_40g -b $cookie_file_name -k > /var/www/html/images/license_40g/onvl-activation-keys
        #copy_activations_keys

      else
        printf "\n  -Continuing installations without activating keys.\n   If you want to just activate keys after this installations. Execute: ${RED}bash ztp.sh -conf file.conf -csv file.csv -offline_onie -online_license${NC}\n   But make sure before running this command, provide device_ids in csv file." 
     
      fi
    fi

    #Copying the image in /var/www/html/image folder
    cd /var/www/html/images
    printf "\n\n  -Now Downloading image in /var/www/html/images. Make sure you have provided default-url parameter value as http://ip_of_dhcp_server/images/onie-installer. in conf file\n\n"
    sleep 1
    curl -o onie-installer -H 'Accept-Encoding: gzip, deflate, br' -X GET https://cloud-web.pluribusnetworks.com/api/download_image1/onie-installer-$version\?version\=$version -b $cookie_file_name -k
    printf "\n  -Downloaded image in /var/www/html/images."


  #If user wants to configure both onie and license offline
  elif [[ "$params" == *"-all_offline"* ]]; then
    printf "\n  -Configuring ONIE: Offline\n"
    printf "\n  -Please Keep onie image in /var/www/html/images/ and activation keys in /var/www/html/images/license_10g and /var/www/html/images/license_40g directories"
    #copy_activations_keys
  fi

  #Choice: user wants to configure online onie or offline onie
  if [[ "$params" == *"-online_onie"* ]]; then
    mkdir -p /var/www/html/images 
    version=`cat $conf_file | grep 'onie_image_version=' | cut -d = -f2`
	
    #Api call for logging in and storing the cookie in cookie_file
    #It takes login_username and login_password as arguements
    login_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/login -d login_email=$username\&login_password=$password -k -c $cookie_file_name`
    login_result=`echo $login_json | jq '.success'`
    if ! [ "$login_result" == true ]; then
      printf "\n  -Login failed: cloud-web.pluribusnetworks.com. Please provide correct credentials in conf file\n"
      exit 0
    else
      csrftoken=`cat $cookie_file_name | grep -Po '(csrftoken\s)\K[^\s]*'`
    fi
    cd /var/www/html/images
    printf "\n  -Downloading image in /var/www/html/images. Make sure you have provided default-url parameter value as http://ip_of_dhcp_server/images/onie-installer. in conf file"
    #curl -o onie-installer -H 'Accept-Encoding: gzip, deflate, br' -X GET https://cloud-web.pluribusnetworks.com/api/download_image1/onie-installer-$version\?version\=$version -b $cookie_file_name -k
    printf "\n  -Downloaded image in /var/www/html/images.\n"

  elif [[ "$params" == *"-offline_onie"* ]]; then
    printf "\n  -Offline ONIE: Download latest ONIE image and keep it in http server directory. i.e /var/www/html/images." 
  fi
 
  #Choice: user wants to configure online license or offline license
  if [[ "$params" == *"-online_license"* ]]; then
    mkdir -p /var/www/html/images/license_10g
    mkdir -p /var/www/html/images/license_40g

    #Api call for logging in and storing the cookie in cookie_file
    #It takes login_username and login_password as arguements	
    login_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/login -d login_email=$username\&login_password=$password -k -c $cookie_file_name`
    login_result=`echo $login_json | jq '.success'`
	
    #If logging is successful then strip out csfrtoken from the cookie
    if ! [ "$login_result" == true ]; then
      printf "\n  -Login failed: cloud-web.pluribusnetworks.com. Please provide correct credentials in conf file"
      exit 0
    else
      csrftoken=`cat $cookie_file_name | grep -Po '(csrftoken\s)\K[^\s]*'`
    fi

    #Api call for finding orderDetails using the cookie as input
    order_details_json=`curl -s -X GET https://cloud-web.pluribusnetworks.com/api/orderDetails -b $cookie_file_name -k`
    order_detail_id=`echo $order_details_json | jq '.order_details[0].id'`
    order_detail_id_40g=`echo $order_details_json | jq '.order_details[1].id'`

    no_device_id=0
    for ((j=1; j<=${#device_id[@]}; j++)); do
      commas=`echo $line | awk -F "," '{print NF-1}'`
      if [ -z "${device_id[j-1]}" ];then
        no_device_id=1
        break
      fi
    done

    if [ "${#device_id[@]}" == 0 ]; then
      no_device_id=1
    fi

    if [ "$no_device_id" == 0 ]; then
      i=0
      for id in "${device_id[@]}"; do
        printf "\n  -Activating key"
        if [ "${device_type[i]}" == "40g" ]; then
          order_detail_id=$order_detail_id_40g
        fi
		
        #OrderActivation using csrftoken, cookie, device_id and order_detail_id
        activation_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/orderActivations -d order_detail_id=$order_detail_id\&device_ids=$id\&csrfmiddlewaretoken=$csrftoken -b $cookie_file_name -k`
        activation_result=`echo $activation_json | jq '.success'`
        if ! [ "$activation_result" == true ]; then
          printf "\n  -Unable to activate key for Device: $id . May be key is already activated."
        fi
        i=$((i+1))
        order_detail_id=`echo $order_details_json | jq '.order_details[0].id'`
      done
      printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id ..\n"
      curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id -b $cookie_file_name -k > /var/www/html/images/license_10g/onvl-activation-keys
      printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id_40g ..\n"
      curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id_40g -b $cookie_file_name -k > /var/www/html/images/license_40g/onvl-activation-keys
      #copy_activations_keys

    else
      printf "\n  -Device ids are not provided for all switches in CSV file. I can get device ids from the switches.\n   But make sure nvOS is running and DHCP IP is assigned to all switches mentioned in the CSV file.\n   ${RED}Shall I login to switches and get device id Enter (y/n)?:${NC}"
      read device_choice
      all_device_id=()
      if [ $device_choice == "y" ]; then 
        for ((j=1; j<=${#ip_arr[@]}; j++)); do
          for ((i=1; i<=3; i++)); do
            ID=`ssh -o StrictHostKeyChecking=no root@${ip_arr[j-1]} 'onie-syseeprom' | grep 'Serial Number' | awk '{ print $5 }'`
            if ! [ -z $ID ]; then
              all_device_id+=($ID)
              break
            fi
          done
        done
        i=0
        for id in "${all_device_id[@]}"
        do
          printf "\n  -Activating key"
          if [ "${device_type[i]}" == "40g" ]; then
            order_detail_id=$order_detail_id_40g
          fi
		  
	  #OrderActivation using csrftoken, cookie, device_id and order_detail_id
          activation_json=`curl -s -X POST https://cloud-web.pluribusnetworks.com/api/orderActivations -d order_detail_id=$order_detail_id\&device_ids=$id\&csrfmiddlewaretoken=$csrftoken -b $cookie_file_name -k`
          activation_result=`echo $activation_json | jq '.success'`
          if ! [ "$activation_result" == true ]; then
            printf "\n  -Unable to activate key for Device: $id . May be key is already activated."
          fi
          i=$((i+1))
          order_detail_id=`echo $order_details_json | jq '.order_details[0].id'`
        done
		
	#Downloading the keys to onvl_activation-keys_10g if it is 10g else to onvl_activation-keys_40g if it is 40g
        printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id ..\n"
        curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id -b $cookie_file_name -k > /etc/pluribuslicense/onvl-activation-keys_10g
        printf "\n\n  -Activation of keys finished. Now downloading Activation key for OrderID:$order_detail_id_40g ..\n"
        curl -s -X GET https://cloud-web.pluribusnetworks.com/api/offline_bundle/$order_detail_id_40g -b $cookie_file_name -k > /etc/pluribuslicense/onvl-activation-keys_40g
        #copy_activations_keys

      else
        printf "\n  -Continuing installations without activating keys.\n   If you want to just activate keys after this installations. Execute: ${RED}bash ztp.sh -conf file.conf -csv file.csv -offline_onie -online_license${NC}\n   But make sure before running this command, provide device_ids in csv file."
      fi
    fi
  elif [[ "$params" == *"-offline_license"* ]] ; then
    printf "\n  -Configuring Onie License: Offline\n"
    printf "\n  -Please Keep onie image in /var/www/html/images/ and activation keys in /var/www/html/images/license_10g and /var/www/html/images/license_40g directories"
    #copy_activations_keys
  fi

  cd $script_dir
  ##Reload apache service
  printf "\n  -Restarting apache service\n"
  sudo service apache2 restart

}
 
##
# This function checks availability of hosts provided in csv file.
# It uses ping to check the availability. 
# Arguments: csv file
##
checkallsystemsgo()
{
   params=$@
   if ! [[ "$params" == *"-csv"* ]]; then
      printf "\nScript requires .csv file as argument to read host ips. Please provide csv file as an argument : ${RED}bash ${0##*/} -checkallsystemsgo -csv filename.csv${NC}\n\n"
      exit 0
   else
     csv_file=`echo "${params#*-csv[$IFS]}" | awk '{ print $1 }'`
     if [ ! -e $csv_file  ]; then
       echo -e "\nCSV file is not present or not in readable format\n"
       exit 0
     else
       if [[ "$params" == *"-csv"* ]]; then
         validate_csv "$params"
       fi

       if [ $processCsv == 1 ]; then
         for line in `cat $csv_file` ;
         do
           arr=()
           IFS=',' read -a arr <<< "$line"
           count=`ping -c 1 ${arr[1]} | grep '1 received' | wc -l`
           if [ "$count" == 1 ];then
             printf "\n\nHost is UP and running with IP: ${arr[1]}\n\n"
           else
             printf "\n\nHost is down or IP is not yet assigned: ${arr[1]}\n\n"  
           fi
         done 
       fi
     fi
   fi
}

##
# This is the main function which parses the arguments and depending on that it calls different functions.
# It configures ONIE OR DHCP OR BOTH according to the user input.
##
main()
{
  declare params="$@"
  if [[ "$params" = *"-h"* ]] || [[ "$params" = *"-help"* ]] || [[ "$params" = *"--h"* ]] || [[ "$params" = *"--help"* ]] || [[ "$#" == 0 ]] ; then
    printf "\n\e[0;31m[ZTP] \e[0m"
    printf "$help"
    exit 0
  fi

  #####DHCP#######
  #If user provides the input '-dhcp'
  if  [[ "$params" == *"-dhcp"* ]]; then
    choice="n"
    choice1="n"
    if ! [[ "$params" == *"-conf"* ]]; then
      printf "\nScript requires .conf file as argument. Please provide configuration file as an argument : ${RED}bash ${0##*/} -dhcp -conf filename.conf${NC}\n\n"
      printf "Shall I generate sample conf file in /tmp/file.conf. ${RED}(y/n):${NC}"
      read choice
      if [ $choice == "y" ]; then
        echo "$default_conf_file" > /tmp/file.conf
        printf "\n#####Sample Conf file is created in /tmp/file.conf with following contents######\n"
        printf "\n${RED}$default_conf_file${NC}\n\n"
      fi
      exit 0
    fi
    dhcpserver "$params"
    exit 0

  ########ONIE##############
  #If user provides the input '-onie'
  elif [[ "$params" == *"-onie"* ]]; then
    if ! [[ "$params" == *"-conf"* ]] && ! [[ "$params" == *"-csv"* ]]; then
      printf "\nScript requires conf and csv file as an argument. These files will be passed as an argument to dhcpserver function. \nExample: ${RED}bash ${0##*/} -onie -conf filename.conf -csv filename.csv ${NC}\n\n"
      printf "Shall I generate sample conf and csv file in /tmp/file.conf and /tmp/file.csv respectively. ${RED}(y/n):${NC}"
      read choice1
      if [ $choice1 == "y" ]; then
        default_conf_file="$default_conf_file
default-url=http://ip_of_dhcp_server/images/onie-installer
username=ansible #In case of online version
password=test123 #In case of online version
onie_image_version=2.5.1-10309 #In case of online version"

        echo "$default_conf_file" > /tmp/file.conf
        printf "\n#####Sample Conf file is created in /tmp/file.conf with following contents######\n"
        printf "\n${RED}$default_conf_file${NC}\n\n"
        printf "\n#####Sample CSV file is created in /tmp/file.csv with following contents######\n"
        printf "\n${RED}$default_csv_file${NC}\n\n"
      fi
      exit 0
    fi

    #Taking the conf file name and storing in conf_file
    conf_file=`echo "${params#*-conf[$IFS]}" | awk '{ print $1 }'`
    if [[ `cat $conf_file | grep 'default-url='` ]]; then
      url=`cat $conf_file | grep 'default-url=' | cut -d = -f2`
    else
      printf "\nScript requires default-url parameter for http server purpose. Please provide default-url parameter in conf file. \nExample: ${RED}default-url=http://ip_of_dhcp_server/images/onie-installer${NC}\n\n"
      exit 0
    fi

    #Exiting if the user has not provided provisioning method for licensing and configuring onie
    if ! [[ "$params" == *"-all_offline"* ]] && ! [[ "$params" == *"-all_online"* ]] && ! [[ "$params" == *"-offline_onie"* ]] && ! [[ "$params" == *"-online_onie"* ]] && ! [[ "$params" == *"-offline_license"* ]] && ! [[ "$params" == *"-online_license"* ]]; then
      printf "\nPlease provide one of these parameters \n1. -all_online \n2. -all_offline \n3. -online_onie \n4. -offline_onie \n5. -online_license \n6. -offline_license\n"
      exit 0
    fi

    #Input user-credentials from conf file incase of online onie and online licensing
    if [[ "$params" == *"-online_license"* ]] || [[ "$params" == *"-online_onie"* ]] ; then
      if ! [ `cat $conf_file | grep 'username='` ]; then
        printf "\nPlease provide username value in conf file.\n\n"
        exit 0
      fi

      if ! [[ `cat $conf_file | grep 'password='` ]]; then
        printf "\nPlease provide password value in conf file.\n\n"
        exit 0
      fi

      if ! [[ `cat $conf_file | grep 'onie_image_version='` ]]; then
        printf "\nPlease provide image version value in conf file.\n\n"
        exit 0
      fi
    fi
    onie "$params"
    exit 0
  elif [[ "$params" == *"-checkallsystemsgo"* ]]; then
    checkallsystemsgo "$params"
  else
    printf "\nCurrently ZTP Script provides 3 functions. i.e DHCP, ONIE and check systems availability. So please provide any of the following options as parameter\n"
    printf "\n1. -dhcp"
    printf "\n2. -onie\n"
    printf "\n3. -checkallsystemsgo"
    printf "\nor run command bash ztp.sh -help\n\n"
  fi

}

main "$@"
