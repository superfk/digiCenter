#!/usr/bin/python
# coding: latin-1
import socket
import sys
#######################################
#
# SimServ protocol example
#
#######################################
#
# Defines
#
# IP address of controller board
addr = '169.254.206.212'
# port of protocol server
port = 2049
# delimiter and carriage return as ascci code
DELIM=b'\xb6'
CR = b'\r'
#
# function: createSimServCmd
#
# create valid simserv command with delimiters
#
def createSimServCmd(cmdID, arglist):
    cmd = cmdID.encode('ascii') # command ID
    cmd = cmd + DELIM + b'1' # Chb Id
    for arg in arglist:
        cmd = cmd + DELIM
        cmd = cmd + arg.encode('ascii')
        cmd = cmd + CR
    return cmd

#
# function: showSimServData
#
# format for output
#
def showSimServData(data):
    list = data.split(DELIM)
    i = 0
    outp = ""
    for l in list:
        i = i +1
        sys.stdout.write(l.decode())
    if i< len(list):
        sys.stdout.write('Â¶')
        
print ("SimServ protocol example")
# create stream socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# connect to protocol server
result = client_socket.connect((addr, port))
sys.stdout.write('\nSetting setpoint to 56.7')
cmd = createSimServCmd('11001', ['1', '56.7'])
sys.stdout.write('\nsending: ')
showSimServData(cmd)
client_socket.send(cmd)
data = client_socket.recv(512)
sys.stdout.write('\nreceived: ')
showSimServData(data)
sys.stdout.write('\nStarting manual mode')
cmd = createSimServCmd('14001', ['1', '1'])
sys.stdout.write('\nsending: ')
showSimServData(cmd)
client_socket.send(cmd)
data = client_socket.recv(512)
sys.stdout.write('\nreceived: ')
showSimServData(data)
sys.stdout.write('\nReading actual value')
cmd = createSimServCmd('11004', ['1'])
sys.stdout.write('\nsending: ')
showSimServData(cmd)
client_socket.send(cmd)
data = client_socket.recv(512)

sys.stdout.write('\nreceived: ')
showSimServData(data)
client_socket.close