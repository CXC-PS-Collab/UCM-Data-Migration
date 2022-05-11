#!/usr/bin/python
# PSFL license

import paramiko
from paramiko_expect import SSHClientInteraction
# import threading
import re
import time

connection = [["10.105.60.210", "osvadmin", "C1sc0@123!"],
              ["10.105.60.211", "admin", "C1sc0@123!"]
              ]
commandList = ["show status", "show network cluster","utils service list","utils dbreplication status","utils dbreplication runtimestate"]
## Reference-- https://voicexplained.blog/2017/02/25/cucm-python-scripting/
## Created by ashimis3
def session(ip, username, password):
    print("Starting tunnel for",ip)
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(ip, username=username, password=password)
    interact = SSHClientInteraction(ssh, timeout=60, display=True)

    interact.expect('admin:')   # program will wait till session is established and CUCM returns admin prompt
    output = interact.current_output_clean  # program saves output of the command to the "output" variable
    output = output + "\n\n" + ("="*80) + "\n\n"


    for cmd in commandList:

        interact.send(cmd)    # program runs the command
        output += ":::Command::: "+cmd+"\n\n"
        if cmd == "utils dbreplication runtimestate":
            result1 = 0
            result2 = 1
            while not result1 == result2:
                interact.send(cmd)
                interact.expect('admin:') # program waits for the command to finish (this happen when CUCM returns admin prompt)
                output += interact.current_output_clean
                regex = re.search('COMPLETED ([0-9]+) tables checked out of ([0-9]+)', output)
                if regex != None:
                    result1 = regex.group(1)
                    result2 = regex.group(2)
                    time.sleep(30)
                else:
                    # interact.expect('admin:')   
                    output += interact.current_output_clean  # program saves output of the command to the "output" variable
                    break
        else:
            interact.expect('admin:')   # program waits for the command to finish (this happen when CUCM returns admin prompt)
            output += interact.current_output_clean  # program saves output of the command to the "output" variable
        output = output + "\n\n" + ("="*80) + "\n\n"

    ssh.close()
    # print(output)
    # interact.send('utils dbreplication status')
    # interact.expect('admin:')

    # while not result1 == result2:
    #     interact.send('utils dbreplication runtimestate')
    #     interact.expect('admin:')
    #     output = interact.current_output_clean
    #     regex = re.search('COMPLETED ([0-9]+) tables checked out of ([0-9]+)', output)
    #     if regex != None:
    #         result1 = regex.group(1)
    #         result2 = regex.group(2)
    #     else:
    #         break
    #     time.sleep(30)
        

    ip_file_name = ip.replace('.', '_')
    output_file = '{}.txt'.format(ip_file_name)
    print(output_file)

    with open(output_file, 'w') as out:
        out.write(output)

print("Starting Connections...")
for i in connection:
    session(i[0], i[1], i[2])
    # t = threading.Thread(target = session, args = (i[0], i[1], i[2]))
    # t.daemon = True
    # t.start()