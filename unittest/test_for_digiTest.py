import serial
import re
import time


def get_resp(resp):

    error_code = None
    para = None
    value = None
    cks = None
    resp_reg = "([a-zA-Z_\d.]*),([a-zA-Z_]*)=?([a-zA-Z_\d. \/]*),([a-zA-Z_\d.]*)"
    x = re.search(resp_reg, resp.decode('utf-8'))

    if x:
        error_code = x.groups()[0]
        para = x.groups()[1]
        value = x.groups()[2]
        cks = x.groups()[3]
    return error_code, para, value, cks


ser = serial.Serial('COM3')
print(ser.name)

# check if any value in buffer
while True:
    b_in = ser.in_waiting
    b_out = ser.out_waiting

    if b_in > 0 or b_out > 0:
        print('Input {}, Output {}'.format(b_in,b_out))
        data = ser.read(b_in)
        print(data)
        break
    else:
        time.sleep(0.1)        

counter = 0
progbar = ''
while True:

    cmd = b'GET(DEV_NAME),DB21'
    ser.write(cmd)
    line = ser.readline()  # b'E0100,MS_PRO=ACTIVE,66F8\r\n'   if not ready to be received cmd
    print(line)
    ret = get_resp(line)
    if ret[2] == 'ACTIVE':
        time.sleep(0.2)
        progbar += '-'
        print( 'Waitng Ready({}) {}>>'.format(counter, progbar))
        counter +=1
    else:
        break

# get device name
cmd = b'GET(DEV_NAME),DB21'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# get device software version
cmd = b'GET(DEV_SV),563B'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# get method
cmd = b'GET(MS_METHOD),2C41'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# get mode
cmd = b'GET(MS_MODE),4937'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# get device measuring duration
cmd = b'GET(MS_DURATION),EC15'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# get device measuring value , now is HDA only
cmd = b'GET(MS_VALUE),FF81'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# set device measuring duration
cmd = b'SET(MS_DURATION=5),3A3D'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

# set device measuring duration
cmd = b'MOV_ABS(START_POS),FD44'
ser.write(cmd)
line = ser.readline()
print(line)
ret = get_resp(line)
print(ret)

ser.close()


'''real reply
COM3
b'E0000,DEV_NAME=DT II,80CB\r\n'
('E0000', 'DEV_NAME', 'DT II', '80CB')
b'E0000,DEV_SV=1.38,E4C2\r\n'
('E0000', 'DEV_SV', '1.38', 'E4C2')
b'E0000,MS_DURATION=5,30AA\r\n'
('E0000', 'MS_DURATION', '5', '30AA')
b'E0007,NO_COMMAND,AF2A\r\n'
('E0007', 'NO_COMMAND', '', 'AF2A')
b'E0000,MS_DURATION=5,30AA\r\n'
('E0000', 'MS_DURATION', '5', '30AA')
b',E5EE\r\n'
(None, None, None, None)

'''



