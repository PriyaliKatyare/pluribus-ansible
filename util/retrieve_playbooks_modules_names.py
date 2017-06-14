# This python script can be used to get modules' and playbooks' name from git repo dynamically.
# The files can be downloaded using the names obtained from the git repo through this python script.
# Usecase: to download pn_autossh.py(name obtained through this script),
#                                               we can simply download using wget as example below:
# eg: wget https://raw.githubusercontent.com/amitsi/pluribus-ansible/master/ansible/library/pn_autossh.py

# ---- REQUIREMENTS ----
# The package named 'bs4' needs to be installed before this python script can be used.
# The package can be installed using the command 'pip install bs4'.

# ---- RETURN ----
# It prints 2 lists:
# playbook_list: The list of names of all the playbooks name.
# module_list: The list of names of all the modules name.

# ---- USAGE ----
# Some ways to use the script:
#    # Use the linux commands in this python script itself to download the files for git repo
#    #               using the names obtained from this python script.
#    # Store the modules' names and playbooks' names in a file through this python script
#    #               and then use the bash commands to download the files through bash scripts.


from bs4 import BeautifulSoup
import urllib

playbook_list = []
module_list = []
playbooks_git_url = 'https://github.com/amitsi/pluribus-ansible/tree/master/ansible/playbooks'
library_git_url = 'https://github.com/amitsi/pluribus-ansible/tree/master/ansible/library'

doc = urllib.urlopen(playbooks_git_url).read()
soup = BeautifulSoup(doc, 'html.parser')

for td_content in soup.find_all("td", {'class': "content"}):
    for span_content in td_content.find_all("span", {'class': "css-truncate"}):
        playbook_name = str(span_content.string)
        if '.yml' in playbook_name:
            playbook_list.append(playbook_name)

doc = urllib.urlopen(library_git_url).read()
soup = BeautifulSoup(doc, 'html.parser')

for td_content in soup.find_all("td", {'class': "content"}):
    for span_content in td_content.find_all("span", {'class': "css-truncate"}):
        module_name = str(span_content.string)
        if '.py' in module_name:
            module_list.append(module_name)

print playbook_list
print module_list
