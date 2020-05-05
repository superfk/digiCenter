import serial
from PyCRC.CRCCCITT import CRCCCITT
import re
import time

class BaInstr(object):
    def __init__(self):
        self.device = None
        self.debug = True
        self.wait_cmd = True
        self.duration = 0
        self.connected = False

    def config(self, debug=False, wait_cmd = True):
        self.debug = debug
        self.wait_cmd = wait_cmd
    
    def make_cmd(self, cmd, para, input_value=None):
        if input_value:
            if type(input_value) == str:
                main_cmd = '{}({}={}),'.format(cmd, para, input_value)
            elif type(input_value) == int or type(input_value) == float or type(input_value) == bool:
                main_cmd = '{}({}={}),'.format(cmd, para, input_value)
            else:
                main_cmd = 'Undefined value type'
        else:
            main_cmd = "{}({}),".format(cmd, para)

        return bytes("{}{}".format(main_cmd, self.get_cksum(main_cmd)).encode('utf-8'))
        
    def get_cksum(self, input):
        cks = hex(CRCCCITT().calculate(input)).upper()[2:]
        cks = cks.rjust(4, '0')
        return cks

    def parse_resp(self, resp):
        resp_str = resp.decode('utf-8')
        resp_reg = '''([a-zA-Z_\d.]*),?\(([a-zA-Z_]*)=?(["'a-zA-Z_\d. \/]*)\),?([a-zA-Z_\d.]*)'''
        match = re.search(resp_reg, resp_str)
        ret = {}        
        if match:
            ret['error_code'] = match.groups()[0]
            ret['para'] = match.groups()[1]
            ret['value'] = match.groups()[2]
            ret['cks'] = match.groups()[3]
        else:
            ret = None
        return ret
    
    def readline_only(self):
        resp = self.device.readline()
        if self.debug:
            print("original resp in readline only: {}".format(resp))
        resp = self.parse_resp(resp)
        if self.debug:
            print("parsing resp in readline only: {}".format(resp))
        if resp:
            return resp['value']
        else:
            return None
    
    def write_and_read(self,cmd, para, value=None):
        max_wait_count = 200
        counter = 0
        while True:
            combined_cmd = self.make_cmd(cmd, para, value)
            if self.debug:
                print("Original cmd: {}".format(combined_cmd))
            self.device.write(combined_cmd)
            resp = self.device.readline()
            if self.debug:
                print("original resp: {}".format(resp))
            resp = self.parse_resp(resp)
            if self.debug:
                print("parsing resp: {}".format(resp))
            if resp:
                if resp['value'] == '"DEVICE BUSY"':
                    time.sleep(0.1)
                    counter += 1
                    if not self.wait_cmd:
                        return None
                elif resp:
                    return resp['value']
                else:
                    return None
            else:
                return None

    
    def open_rs232(self, port=None, baudrate=9600, bytesize=serial.EIGHTBITS, parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE, timeout=10):
        self.device = serial.Serial(port=port, baudrate=baudrate, bytesize=bytesize, parity=parity, stopbits=stopbits, timeout=timeout, write_timeout=3)
        if self.device:
            self.connected = True
        else:
            self.connected = False
        
        return self.connected
    
    def close_rs232(self):
        self.connected = False
        self.device.close()

    def get_dev_name(self):
        return self.write_and_read('GET', 'DEV_NAME')
    
    def get_dev_software_version(self):
        return self.write_and_read('GET', 'DEV_SV')

    def get_ms_duration(self):
        self.duration = float(self.write_and_read('GET', 'MS_DURATION'))
        return self.duration

    def set_ms_duration(self, value):
        self.write_and_read('SET', 'MS_DURATION', value)
        self.duration = float(value)
        return self.duration

    def get_ms_method(self):
        return self.write_and_read('GET', 'MS_METHOD')

    def isReady(self):
        ret = self.write_and_read('GET', 'DEV_NAME')
        if ret:
            if ret[2] == 'ACTIVE':
                return False
            else:
                return True
        else:
            return False


if __name__ == '__main__':
    # ba = BaInstr()
    # input = b'GET(MS_MODE),' # exp_crc = '05F9' 
    # result = ba.get_cksum(input)
    # print(result)

    # resp = 'E0000,MS_DURATION=5,30AA\r\n'
    # par_result = ba.parse_resp(resp)
    # print(par_result)
    # ba.open_rs232("COM3",timeout=1)
    # ret = ba.get_dev_name()
    # print(ret)
    # ret = ba.get_dev_software_version()
    # print(ret)
    # ret = ba.get_ms_duration()
    # print(ret)
    # ret = ba.get_ms_method()
    # print(ret)
    # ret = ba.isReady()
    # print(ret)
    # ret = ba.set_ms_duration(3)
    # print(ret)
    
    # ba.close_rs232()
    ser = serial.Serial('COM3',9600)
    ser.close()
