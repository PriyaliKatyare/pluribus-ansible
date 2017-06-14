# Make the import statements and remove lib file
# Add appropriate copyright headers on every file
# Add disclamer to look at source code on github
# Generate Customer Facing Docs
# Create a new folder to keep all of this in
# Optionally Scrub all other files for release

##-----------------------------------------------------------------------------##
# build_release.py:
# This tool builds a release ready version of an ansible playbook for either
# release or for testing. This
##-----------------------------------------------------------------------------##

from bs4 import BeautifulSoup
import argparse
import re
import os

##-----------------------------------------------------------------------------##
# Handle Argument parsing, build directory structure
##-----------------------------------------------------------------------------##

parser = argparse.ArgumentParser(description='Create a release style file for'
                                 ' release and testing. Concatenates the '
                                 'library file, converts library calls, and '
                                 'appends all of the relevant CLI python '
                                 'wrappers.')
parser.add_argument('file', metavar='FILENAME', nargs='+')
# Change lib call from cli\..*
# Specify target directory for files
args = parser.parse_args()

FILENAMES = args.file

print args.file

if not os.path.exists('xyz/'):
    os.makedirs('xyz') 

##-----------------------------------------------------------------------------##
# Python code templates for the various CLI commands
##-----------------------------------------------------------------------------##

def struct_simple(option):
    return """        if '%s' in kwargs:
            command += \" %s %%s\" %% kwargs['%s']
""" % (option.replace('-','_'),
                                                         option.replace('_',''),
                                                         option.replace('-','_'))

def struct_single(option):
    return """        if '%s' in kwargs:
            command += \" %s\"
""" % (option.replace('-','_'), option)

def struct_array(option, choices):
    return """        if '%s' in kwargs:
            for item in %s:
                if item == kwargs['%s']:
                    command += \" %s %%s\" %% item
                    break
""" % (option.replace('-','_'), choices,
                                option.replace('-','_'), option.replace('_', ''))

def struct_choice(choices):
    return """        if '%s' in kwargs:
            if kwargs['%s']:
                command += \" %s\"
            else:
                command += \" %s\"
""" % (choices[0].replace('-','_'),
                                         choices[0].replace('-','_'),
                                         choices[0], choices[1])

# Regular expression matchers for the various templates
simple = re.compile('^[a-z-]+ [a-z-]+$')
single = re.compile('^[a-z-]+$')
array = re.compile('^[a-z-]+ ([a-z-]+\|)+[a-z-]+$')
choice = re.compile('^([a-z-]+\|)+[a-z-]+$')
range = re.compile('^[a-z-]+ [0-9\.]+$')

# If there is more than one file, generate a dictionary, otherwise walk the file

lib_data = ''
def_data = ''
with open('ansible/library/pn_ansible_lib.py', 'r') as FILE:
    lib_data = FILE.read()

with open('def.txt', 'r') as FILE:
    def_data = FILE.read()

##-----------------------------------------------------------------------------##
# Build dictionary of all of the CLI wrappers avaliable
##-----------------------------------------------------------------------------##

method_dict = {}
soup = BeautifulSoup(def_data, 'html.parser')
tables = soup.find_all('table')
        
for table in tables:
    rows = table.find_all('tr')
    prepend_string = """    def %s(self, **kwargs):
    command = '%s'
""" % (rows[0].td.get_text().replace('-','_'),
       rows[0].td.get_text())

    for row in rows[1:]:
        raw = row.td.get_text()
        text = raw.split(" ")

        if text[0] == 'if':
            text[0] = '_if'
            
        if simple.match(raw):
            prepend_string += struct_simple(text[0])
                        
        elif single.match(raw):
            prepend_string += struct_single(text[0])
                        
        elif array.match(raw):
            option = text[0]
            choices = text[1].split('|')
            prepend_string += struct_array(option, choices)
                    
        elif choice.match(raw):
            options = raw.split('|')
            raw.split('|')
            prepend_string += struct_choice(options)
                    
        elif range.match(raw):
            #print "range: " + text
            pass
                    
        else:
            #print "ERROR: " + text
            pass
                
        prepend_string += """        return self.send_command(command)
"""
        method_dict[rows[0].td.get_text().replace('-','_')] = prepend_string

for filename in FILENAMES:
    file_data = ''
    lib_call = re.compile('.*pn\.([a-zA-Z_]+)\(.*\).*')
    with open(filename, 'r') as FILE:
        for line in FILE:
            line = re.sub('pn.', '', line)
            file_data += line
        
    source_index = []
    
    with open(filename) as FILE:
        for line in FILE:
            if lib_call.match(line):
                source_index.append(lib_call.match(line).group(1))

    source_index = list(set(source_index))
                
    prepend_string = ''
    
    with open('xyz/' + filename.split('/')[-1], 'w') as FILE:
        FILE.write('')
    
    with open('xyz/' + filename.split('/')[-1], 'a') as FILE:
        FILE.write(lib_data)
        for call in source_index:
            if not call in method_dict:
                # Do nothing, other library functions or illegal functions
                pass
            else:
                FILE.write(method_dict[call])

        FILE.write(file_data)

    with open(FILENAMES[0]) as FILE:
        for line in FILE:
            pass

