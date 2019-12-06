#!/usr/bin/python
# coding: latin-1
import socket
import sys
import time
import matplotlib.pyplot as plt 

# delimiter and carriage return as ascci code
DELIM=b'\xb6'
CR = b'\r'

class DigiChamber(object):
    def __init__(self, ip='192.168.0.1', port=2049):
        self.ip = ip
        self.port = port
        self.s = None
        self.connected = False
    
    def connect(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(3)
        result = self.s.connect((self.ip, self.port))
        if result:
            self.connected=True
        return self.connected

    def create_cmd(self, cmdID, arglist):
        global CR, DELIM
        cmd = cmdID.encode('ascii') # command ID
        cmd = cmd + DELIM + b'1' # Chb Id
        for arg in arglist:
            cmd = cmd + DELIM
            cmd = cmd + arg.encode('ascii')
            cmd = cmd + CR
        return cmd
    
    def send_and_get(self, cmd, buffer=512, delay_sec=0):
        global DELIM
        self.s.send(cmd)
        time.sleep(delay_sec)
        data = self.s.recv(buffer)
        data = data.split(DELIM)
        return data
    
    def parsing_data(self, data):
        global CR, DELIM
        lists = data.split(DELIM)
        i = 0
        outp = ""
        for l in lists:
            i = i +1
            sys.stdout.write(l.decode())
        if i< len(lists):
            sys.stdout.write('Â¶')
    
    def get_chamber_info(self):
        '''
        1 Test system type
        2 Year manufactured
        3 Serial number
        4 Order number
        5 PLC Lib version
        6 PLC runtime system version
        7 PLC version
        8 S!MPAC® program version
        '''
        total = 8
        info = {}
        info_head = ['TestSysType', 'YearManuf', 'SN', 'OrderN', 'PLCVer', 'PLCRTVer', 'S!MACVer']
        for i, h in enumerate(info_head):
            argID = str(i+1)
            cmd = self.create_cmd('99997', ['1', argID])
            respid, data = self.send_and_get(cmd)
            info[h] = data.decode()
        return info
    
    def set_manual_mode(self, enabled=False):
        if enabled:
            setManual = '1'
        else:
            setManual = '0'
        cmd = self.create_cmd('14001', ['1', setManual])
        return self.send_and_get(cmd)
    
    def get_control_variables_info(self):
        # how many variable
        cmd = self.create_cmd('11018', ['1'])
        respid, value = self.send_and_get(cmd)
        print(value)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            var_info = {}
            # variable name
            cmd = self.create_cmd('11026', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['name']=info.decode('utf-8', 'ignore').strip()
            # variable unit
            cmd = self.create_cmd('11023', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['unit']=info.decode('utf-8', 'ignore').strip()
            # variable min input limit
            cmd = self.create_cmd('11007', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['min']=float(info)
            # variable max input limit
            cmd = self.create_cmd('11009', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['max']=float(info)
            # variable wanring min input limit
            cmd = self.create_cmd('11016', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['warn_min']=float(info)
            # variable warning max input limit
            cmd = self.create_cmd('11017', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['warn_max']=float(info)
            # variable alarm min input limit
            cmd = self.create_cmd('11014', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['alarm_min']=float(info)
            # variable alarm max input limit
            cmd = self.create_cmd('11015', ['1', str(d+1)])
            respid, info = self.send_and_get(cmd)
            var_info['alarm_max']=float(info)

            ctrl_vars.append(var_info)

        return ctrl_vars
    
    def get_name_control_variables(self):
        cmd = self.create_cmd('11018', ['1'])
        respid, value = self.send_and_get(cmd)
        value = int(value)
        return value
    
    def set_setPoint(self, value):
        cmd = self.create_cmd('11001', ['1', str(value)])
        self.send_and_get(cmd)
        rep = self.get_setPoint()
        return rep
    
    def get_setPoint(self):
        cmd = self.create_cmd('11002', ['1'])
        respid, value = self.send_and_get(cmd)
        value = float(value)
        return value
    
    def get_real_control_variable_value(self):
        cmd = self.create_cmd('11004', ['1'])
        respid, value = self.send_and_get(cmd)
        value = float(value)
        return value
    
    def get_real_temperature(self):
        cmd = self.create_cmd('12002', ['1'])
        respid, value = self.send_and_get(cmd)
        value = float(value)
        print(value)
        return value
    
    def set_gradient_up(self, value_k_per_min=0):
        cmd = self.create_cmd('11068', ['1', str(value_k_per_min)])
        self.send_and_get(cmd)
        return self.get_gradient_up()
    
    def get_gradient_up(self):
        cmd = self.create_cmd('11066', ['1'])
        respid, value = self.send_and_get(cmd)
        return value
    
    def set_gradient_down(self, value_k_per_min=0):
        cmd = self.create_cmd('11072', ['1', str(value_k_per_min)])
        self.send_and_get(cmd)
        return self.get_gradient_down()
    
    def get_gradient_down(self):
        cmd = self.create_cmd('11070', ['1'])
        respid, value = self.send_and_get(cmd)
        return value
    
    def close(self):
        self.s.close()
        self.connected=False
        

if __name__ == '__main__':
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    print(dc.get_chamber_info())
    dc.set_manual_mode(False)
    dc.set_setPoint(45)
    print('get setpoint: {}'.format(dc.get_setPoint()))
    ctrl_var_info = dc.get_control_variables_info()
    print(ctrl_var_info)
    # data = []
    # for i in range(3):
    #     value = dc.get_real_temperature()
    #     time.sleep(0.2)
    #     data.append(value)
    
    # plt.plot(data)
    # plt.show()


