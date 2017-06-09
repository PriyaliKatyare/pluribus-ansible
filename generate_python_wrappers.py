"""
cat tmp.txt | sed 's/&nbsp; //g' | sed 's/\<td .*\>//' | sed 's/ border=0//' | sed 's/\<h[123].*//' | sed 's/\<br .*//' | sed 's/\<hr .*//' | sed 's/\[ //' | sed 's/ \]//'
"""

from bs4 import BeautifulSoup
import re

myfile = open('def.txt', 'r')
data = myfile.read()

class Decleration():
    def __init__():
        self.req = []
        self.ops = []

def struct_simple(option):
    return """        if '%s' in kwargs:
            command += \" %s %%s\" %% kwargs['%s']""" % (option.replace('-','_'), option.replace('_',''), option.replace('-','_'))

def struct_single(option):
    return """        if '%s' in kwargs:
            command += \" %s\"""" % (option.replace('-','_'), option)

def struct_array(option, choices):
    return """        if '%s' in kwargs:
            for item in %s:
                if item == kwargs['%s']:
                    command += \" %s %%s\" %% item
                    break""" % (option.replace('-','_'), choices, option.replace('-','_'), option.replace('_', ''))

def struct_choice(choices):
    return """        if '%s' in kwargs:
            if kwargs['%s']:
                command += \" %s\"
            else:
                command += \" %s\"""" % (choices[0].replace('-','_'), choices[0].replace('-','_'), choices[0], choices[1])

simple = re.compile('^[a-z-]+ [a-z-]+$')
single = re.compile('^[a-z-]+$')
array = re.compile('^[a-z-]+ ([a-z-]+\|)+[a-z-]+$')
choice = re.compile('^([a-z-]+\|)+[a-z-]+$')
range = re.compile('^[a-z-]+ [0-9\.]+$')

soup = BeautifulSoup(data, 'html.parser')
tables = soup.find_all('table')

# print """class AGEN_C():
#     def __init__():
#         pass
# """

for table in tables:
    rows = table.find_all('tr')
    print """
    def %s(self, **kwargs):
        command = '%s'""" % (rows[0].td.get_text().replace('-','_'), rows[0].td.get_text())
    
    for row in rows[1:]:
        raw = row.td.get_text()
        text = raw.split(" ")

        # Handle the param 'if', which cant be passed as a kwarg
        if text[0] == 'if':
            text[0] = '_if'
            
        if simple.match(raw):
            print struct_simple(text[0])
            
        elif single.match(raw):
            print struct_single(text[0])
            
        elif array.match(raw):
            option = text[0]
            choices = text[1].split('|')
            print struct_array(option, choices)
        
        elif choice.match(raw):
            options = raw.split('|')
            print struct_choice(options)
        
        elif range.match(raw):
            #print "range: " + text
            pass
        
        else:
            #print "ERROR: " + text
            pass

    print """
        return self.send_command(command)
"""
        
