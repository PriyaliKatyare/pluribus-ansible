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


