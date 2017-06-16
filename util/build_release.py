"""
build_release.py
This tool builds a release style file out of a python module file.

Currently prepends hand written library, then the auto-generated wrappers that
the module uses and finally fixes library calls. Stores generated file in
pushable_ansible/ which can be run by pointing run.sh at the pushable_ansible/
directory as the Ansible library.

TODO:
Prepend the LICENSE
Prepend disclaimer to look for source code on GitHub
Generate Documentation
"""

import argparse
import re
import os
from bs4 import BeautifulSoup

# ==------------------------------------------------------------------------== #
#
# Handle Argument parsing, build directory structure
#
# ==------------------------------------------------------------------------== #

PARSER = argparse.ArgumentParser(description='Create a release style file for'
                                 ' release and testing. Concatenates the '
                                 'library file, converts library calls, and '
                                 'appends all of the relevant CLI python '
                                 'wrappers.')
PARSER.add_argument('file', metavar='FILENAME', nargs='+')

ARGS = PARSER.parse_args()

FILENAMES = ARGS.file

# Release directory to be used when generating release files
REL_DIR = '../ansible_pushable/'

if not os.path.exists(REL_DIR):
    os.makedirs(REL_DIR)

# ==------------------------------------------------------------------------== #
#
# Python code templates for the various CLI commands
#
# ==------------------------------------------------------------------------== #


def struct_simple(_option):
    """
    Generate a wrapper for a simple argument, see util/README.md
    """

    return """        if '%s' in kwargs:
            command += \" %s %%s\" %% kwargs['%s']
""" % (_option.replace('-', '_'),
       _option.replace('_', ''),
       _option.replace('-', '_'))


def struct_single(_option):
    """
    Generate a wrapper for a single argument, see util/README.md
    """

    return """        if '%s' in kwargs:
            command += \" %s\"
""" % (_option.replace('-', '_'), _option)


def struct_array(_option, _choices):
    """
    Generate a wrapper for a array argument, see util/README.md
    """

    return """        if '%s' in kwargs:
            for item in %s:
                if item == kwargs['%s']:
                    command += \" %s %%s\" %% item
                    break
""" % (_option.replace('-', '_'), _choices,
       _option.replace('-', '_'),
       _option.replace('_', ''))


def struct_choice(_choices):
    """
    Generate a wrapper for a choice argument, see util/README.md
    """

    return """        if '%s' in kwargs:
            if kwargs['%s']:
                command += \" %s\"
            else:
                command += \" %s\"
""" % (_choices[0].replace('-', '_'),
       _choices[0].replace('-', '_'),
       _choices[0], _choices[1])

# Regular expression matchers for the various templates
SIMPLE = re.compile(r'^[a-z-]+ [a-z-]+$')
SINGLE = re.compile(r'^[a-z-]+$')
ARRAY = re.compile(r'^[a-z-]+ ([a-z-]+\|)+[a-z-]+$')
CHOICE = re.compile(r'^([a-z-]+\|)+[a-z-]+$')
RANGE = re.compile(r'^[a-z-]+ [0-9\.]+$')

# If there is more than one file, generate a dictionary, otherwise walk the file

LIB_DATA = ''
DEF_DATA = ''
with open('../ansible/common/pn_ansible_lib.py', 'r') as FILE:
    LIB_DATA = FILE.read()

with open('def.txt', 'r') as FILE:
    DEF_DATA = FILE.read()

# ==------------------------------------------------------------------------== #
#
# Build dictionary of all of the CLI wrappers avaliable
#
# ==------------------------------------------------------------------------== #

METHOD_DICT = {}
TABLES = BeautifulSoup(DEF_DATA, 'html.parser').find_all('table')

for table in TABLES:
    rows = table.find_all('tr')
    prepend_string = """    def %s(self, **kwargs):
        command = '%s'
""" % (rows[0].td.get_text().replace('-', '_'),
       rows[0].td.get_text())

    # Match each argument with its type and generate the appropriate python code
    for row in rows[1:]:
        raw = row.td.get_text()
        text = raw.split(" ")

        if text[0] == 'if':
            text[0] = '_if'

        if SIMPLE.match(raw):
            prepend_string += struct_simple(text[0])

        elif SINGLE.match(raw):
            prepend_string += struct_single(text[0])

        elif ARRAY.match(raw):
            option = text[0]
            choices = text[1].split('|')
            prepend_string += struct_array(option, choices)

        elif CHOICE.match(raw):
            options = raw.split('|')
            raw.split('|')
            prepend_string += struct_choice(options)

        elif RANGE.match(raw):
            # print "range: " + text
            pass

        else:
            # print "ERROR: " + text
            pass

        prepend_string += """        return self.send_command(command)
"""
        METHOD_DICT[rows[0].td.get_text().replace('-', '_')] = prepend_string

for filename in FILENAMES:
    file_data = ''
    lib_call = re.compile(r'.*cli\.([a-zA-Z_]+)\(.*\).*')
    with open(filename, 'r') as FILE:
        for line in FILE:
            line = re.sub(r'pn\.', '', line)
            line = re.sub(r'.*import pn_ansible_lib as pn.*', '', line)
            file_data += line

    source_index = []

    with open(filename) as FILE:
        for line in FILE:
            if lib_call.match(line):
                source_index.append(lib_call.match(line).group(1))

    source_index = list(set(source_index))

    prepend_string = ''

    with open(REL_DIR + filename.split('/')[-1], 'w') as FILE:
        FILE.write('')

    with open(REL_DIR + filename.split('/')[-1], 'a') as FILE:
        FILE.write(LIB_DATA)
        for call in source_index:
            if call not in METHOD_DICT:
                # Do nothing, other library functions or illegal functions
                pass
            else:
                FILE.write(METHOD_DICT[call])

        FILE.write(file_data)

    with open(FILENAMES[0]) as FILE:
        for line in FILE:
            pass
