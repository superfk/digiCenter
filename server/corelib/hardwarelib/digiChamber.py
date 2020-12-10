#!/usr/bin/python
# coding: latin-1
import socket
import sys
import time
import matplotlib.pyplot as plt
import random

# delimiter and carriage return as ascci code
DELIM=b'\xb6'
CR = b'\r'

class DigiChamber(object):
    def __init__(self, ip='192.168.0.1', port=2049):
        self.ip = ip
        self.port = port
        self.s = None
        self.connected = False
        self.dummyT = 23
        self.dummyH = 50
    
    def connect(self):
        self.connected=False
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.settimeout(5)
        self.s.connect((self.ip, self.port))
        self.connected=True
        return self.connected
    
    def recovery(self):
        tryCounts = 5
        interval = 1
        for i in range(tryCounts):
            try:
                self.close()
            except:
                pass
            try:
                connected = self.connect()
                if connected:
                    return True
                else:
                    time.sleep(interval)
            except:
                time.sleep(interval)
        return False

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
        if len(data)==1:
            if int(data[0]) in [-8, -6]:
                return int(data[0]), None
            return 0, data[0]
        else:
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
            cmd = self.create_cmd('99997', [argID])
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
        cmd = self.create_cmd('11018', [])
        respid, value = self.send_and_get(cmd)
        value = self.get_number_control_variables()
        ctrl_vars = []
        for d in range(value):
            # parse id of control variable
            cvID = str(d+1)
            var_info = {}
            # variable name
            cmd = self.create_cmd('11026', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['name']=info.decode('utf-8', 'ignore').strip()
            # variable unit
            cmd = self.create_cmd('11023', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['unit']=info.decode('utf-8', 'ignore').strip()
            # variable min input limit
            cmd = self.create_cmd('11007', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['min']=float(info)
            # variable max input limit
            cmd = self.create_cmd('11009', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['max']=float(info)
            # variable wanring min input limit
            cmd = self.create_cmd('11016', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['warn_min']=float(info)
            # variable warning max input limit
            cmd = self.create_cmd('11017', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['warn_max']=float(info)
            # variable alarm min input limit
            cmd = self.create_cmd('11014', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['alarm_min']=float(info)
            # variable alarm max input limit
            cmd = self.create_cmd('11015', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['alarm_max']=float(info)

            ctrl_vars.append(var_info)

        return ctrl_vars

    def get_control_values_info(self):
        # how many variable
        cmd = self.create_cmd('13007', [])
        respid, value = self.send_and_get(cmd)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            # parse id of control variable
            cvID = str(d+1)
            var_info = {}
            # variable name
            cmd = self.create_cmd('13011', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['name']=info.decode('utf-8', 'ignore').strip()
            # variable unit
            cmd = self.create_cmd('13010', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['unit']=info.decode('utf-8', 'ignore').strip()
            # variable min input limit
            cmd = self.create_cmd('13002', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['min']=float(info)
            # variable max input limit
            cmd = self.create_cmd('13004', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['max']=float(info)

            ctrl_vars.append(var_info)

        return ctrl_vars

    def get_mear_values_info(self):
        # how many variable
        cmd = self.create_cmd('12012', [])
        respid, value = self.send_and_get(cmd)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            # parse id of control variable
            cvID = str(d+1)
            var_info = {}
            # variable name
            cmd = self.create_cmd('12019', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['name']=info.decode('utf-8', 'ignore').strip()
            # variable unit
            cmd = self.create_cmd('12016', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['unit']=info.decode('utf-8', 'ignore').strip()
            # variable wanring min input limit
            cmd = self.create_cmd('12010', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['warn_min']=float(info)
            # variable warning max input limit
            cmd = self.create_cmd('12011', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['warn_max']=float(info)
            # variable alarm min input limit
            cmd = self.create_cmd('12008', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['alarm_min']=float(info)
            # variable alarm max input limit
            cmd = self.create_cmd('12009', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['alarm_max']=float(info)

            ctrl_vars.append(var_info)

        return ctrl_vars
    
    def get_do_info(self):
        # how many variable
        cmd = self.create_cmd('14007', [])
        respid, value = self.send_and_get(cmd)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            # parse id of control variable
            cvID = str(d+1)
            var_info = {}
            # variable name
            cmd = self.create_cmd('14010', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['name']=info.decode('utf-8', 'ignore').strip()
            # variable state
            cmd = self.create_cmd('14003', [str(d+1+1)])
            respid, info = self.send_and_get(cmd)
            var_info['state']=info.decode('utf-8', 'ignore').strip()
            ctrl_vars.append(var_info)
            # variable address
            var_info['addr']=int(cvID)

        return ctrl_vars
    
    def get_di_info(self):
        # how many variable
        cmd = self.create_cmd('15004', [])
        respid, value = self.send_and_get(cmd)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            # parse id of control variable
            cvID = str(d+1)
            var_info = {}
            # variable name
            cmd = self.create_cmd('15005', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['name']=info.decode('utf-8', 'ignore').strip()
            # variable state
            cmd = self.create_cmd('15002', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['state']=info.decode('utf-8', 'ignore').strip()
            ctrl_vars.append(var_info)
            # variable address
            var_info['addr']=int(cvID)

        return ctrl_vars
    
    def get_msg_info(self):
        # how many variable
        cmd = self.create_cmd('17002', [])
        respid, value = self.send_and_get(cmd)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            # parse id of control variable
            cvID = str(d+1)
            var_info = {}
            # variable name
            cmd = self.create_cmd('17007', [cvID])
            respid, info = self.send_and_get(cmd)
            var_info['msg']=info.decode('utf-8', 'ignore').strip()

        return ctrl_vars
    
    def get_number_control_variables(self):
        cmd = self.create_cmd('11018', [])
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
    
    def get_real_temperature(self, roundTo=1):
        cmd = self.create_cmd('11004', ['1'])
        respid, value = self.send_and_get(cmd)
        value = round(float(value),roundTo)
        return value
    
    def get_real_humidity(self, roundTo=1):
        cmd = self.create_cmd('11004', ['2'])
        respid, value = self.send_and_get(cmd)
        if respid in [-8,-6]:
            value = 0
        value = round(float(value),roundTo)
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

    def set_tempShift(self, value=0):
        cmd = self.create_cmd('13006', ['2', str(value)])
        self.send_and_get(cmd)

    def set_compAir(self, on=0):
        cmd = self.create_cmd('14001', ['9', str(on)])
        self.send_and_get(cmd)

    def set_dryer(self, on=0):
        cmd = self.create_cmd('14001', ['10', str(on)])
        self.send_and_get(cmd)

    def set_controlSupplyAir(self, on=0):
        cmd = self.create_cmd('14001', ['20', str(on)])
        self.send_and_get(cmd)
    
    def is_test_running(self):
        cmd = self.create_cmd('10012', [])
        respid, value = self.send_and_get(cmd)
        status_code = int(value)
        if status_code in [3, 7, 11]:
            return True
        else:
            return False

    def set_dummy_act_temp(self,value):
        self.dummyT = value
    
    def set_dummy_act_hum(self,value):
        self.dummyH = value

    def close(self):
        self.connected=False
        self.s.close()
        
'''
#################################################################
### Dummy Class
#################################################################
'''


class DummyChamber(DigiChamber):
    def __init__(self, ip='192.168.0.1', port=2049):
        super(DummyChamber, self).__init__(ip,port)
        self.ip = ip
        self.port = port
        self.s = None
        self.connected = False
        self.dummySetPoint = 0
        self.gradientUp = 0
        self.gradientDown = 0
        self.status = 0
    
    def connect(self):
        self.connected=True
        self.status = 1
        return self.connected
    
    def recovery(self):
        return True

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
        time.sleep(delay_sec)
        return None
    
    def parsing_data(self, data):
        global CR, DELIM
        lists = data.split(DELIM)
        i = 0
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
        info['TestSysType'] = 'TestSysType'
        info['YearManuf'] = 'dummy'
        info['SN'] = 'dummy'
        info['OrderN'] = 'dummy'
        info['PLCVer'] = 'dummy'
        info['PLCRTVer'] = 'dummy'
        info['S!MACVer'] = 'dummy'
        return info
    
    def set_manual_mode(self, enabled=False):
        if enabled:
            setManual = '1'
            self.status = 2
        else:
            setManual = '0'
            self.status = 1
        cmd = self.create_cmd('14001', ['1', setManual])
        return enabled
    
    def get_control_variables_info(self):
        # how many variable
        cmd = self.create_cmd('11018', ['1'])
        respid, value = 1,2
        print(value)
        value = int(value)
        ctrl_vars = []
        for d in range(value):
            var_info = {}
            # variable name
            cmd = self.create_cmd('11026', ['1', str(d+1)])
            respid, info = 1,'Temperature'
            var_info['name']=info
            # variable unit
            cmd = self.create_cmd('11023', ['1', str(d+1)])
            respid, info = 1,'°C'
            var_info['unit']=info
            # variable min input limit
            cmd = self.create_cmd('11007', ['1', str(d+1)])
            respid, info = 1,'-45'
            var_info['min']=float(info)
            # variable max input limit
            cmd = self.create_cmd('11009', ['1', str(d+1)])
            respid, info = 1,'180'
            var_info['max']=float(info)
            # variable wanring min input limit
            cmd = self.create_cmd('11016', ['1', str(d+1)])
            respid, info = 1,'-40'
            var_info['warn_min']=float(info)
            # variable warning max input limit
            cmd = self.create_cmd('11017', ['1', str(d+1)])
            respid, info = 1,'170'
            var_info['warn_max']=float(info)
            # variable alarm min input limit
            cmd = self.create_cmd('11014', ['1', str(d+1)])
            respid, info = 1,'-40'
            var_info['alarm_min']=float(info)
            # variable alarm max input limit
            cmd = self.create_cmd('11015', ['1', str(d+1)])
            respid, info = 1,'170'
            var_info['alarm_max']=float(info)

            ctrl_vars.append(var_info)

        return ctrl_vars
    
    def get_number_control_variables(self):
        cmd = self.create_cmd('11018', ['1'])
        respid, value = 1,'2'
        value = int(value)
        return value
    
    def set_setPoint(self, value):
        cmd = self.create_cmd('11001', ['1', str(value)])
        self.send_and_get(cmd)
        self.dummySetPoint = value
        return self.dummySetPoint
    
    def get_setPoint(self):
        return self.dummySetPoint
    
    def get_real_control_variable_value(self):
        cmd = self.create_cmd('11004', ['1'])
        return self.dummySetPoint + random.random()*0.2
    
    def get_real_temperature(self, roundTo=1):
        return round(self.dummyT + random.random()*0.002,roundTo)
    
    def get_real_humidity(self,  roundTo=1):
        return round(self.dummyH + random.random()*0.2,roundTo)
    
    def set_gradient_up(self, value_k_per_min=0):
        cmd = self.create_cmd('11068', ['1', str(value_k_per_min)])
        if value_k_per_min <= 0:
            self.gradientUp=60
        else:
            self.gradientUp=value_k_per_min
        return self.gradientUp
    
    def get_gradient_up(self):
        cmd = self.create_cmd('11066', ['1'])
        return self.gradientUp
    
    def set_gradient_down(self, value_k_per_min=0):
        cmd = self.create_cmd('11072', ['1', str(value_k_per_min)])
        if value_k_per_min <= 0:
            self.gradientDown=60
        else:
            self.gradientDown=value_k_per_min
        return self.gradientDown
    
    def get_gradient_down(self):
        return self.gradientDown

    def set_tempShift(self, value=0):
        cmd = self.create_cmd('13006', ['2', str(value)])
        self.send_and_get(cmd)

    def set_compAir(self, on=0):
        cmd = self.create_cmd('14001', ['9', str(on)])
        self.send_and_get(cmd)

    def set_dryer(self, on=0):
        cmd = self.create_cmd('14001', ['10', str(on)])
        self.send_and_get(cmd)

    def set_controlSupplyAir(self, on=0):
        cmd = self.create_cmd('14001', ['20', str(on)])
        self.send_and_get(cmd)

    def is_test_running(self):
        cmd = self.create_cmd('10012', [])
        self.send_and_get(cmd)
        status_code = self.status
        if status_code in [3, 7, 11]:
            return True
        else:
            return False
            
    def close(self):
        self.connected=False
        self.status = 0

        
if __name__ == '__main__':
    dc = DigiChamber(ip='192.168.0.100')
    dc.connect()
    print('system info')
    print(dc.get_chamber_info())
    print('')
    ret = dc.get_real_humidity()
    print(ret)
    ret = dc.get_control_values_info()
    print(ret)
    ret = dc.get_gradient_up()
    print(ret)
    ret = dc.get_gradient_down()
    print(ret)
    ret = dc.get_mear_values_info()
    print(ret)
    ret = dc.get_real_control_variable_value()
    print(ret)
    ret = dc.get_real_temperature()
    print(ret)
    ret = dc.get_setPoint()
    print(ret)
    # dc.set_manual_mode(True)
    # target = 30
    # dc.set_setPoint(target)
    # print('get setpoint: {}'.format(dc.get_setPoint()))
    # print('')
    # ctrl_var_info = dc.get_control_variables_info()
    # print(ctrl_var_info)
    # print('')
    # data = []
    # while True:
    #     value = dc.get_real_temperature()
    #     print('curretn temp: {}'.format(value))
    #     print('get real setpoint: {}'.format(dc.get_real_control_variable_value()))
    #     print('')
    #     time.sleep(0.5)
    #     data.append(value)
    #     if value >= target:
    #         break
    
    # dc.set_manual_mode(False)
    dc.close()
    # plt.plot(data)
    # plt.show()


