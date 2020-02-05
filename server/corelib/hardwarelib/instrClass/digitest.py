import threading
import time
import re
import matplotlib.pyplot as plt
import sys
from corelib.hardwarelib.instrClass.baInstr import BaInstr
import random

class Digitest(BaInstr):
    def __init__(self):
        super(Digitest, self).__init__()

    def set_remote(self, enabled=True):
        if enabled:
            ret = self.write_and_read('SET','DEV_REMOTE_CONTROL','TRUE')
        else:
            ret = self.write_and_read('SET','DEV_REMOTE_CONTROL','FALSE')
        return ret

    def get_remote(self):
        return self.write_and_read('GET', 'MS_MODE')
    
    def start_mear(self):
        self.write_and_read('MS_PRO', 'START')
        return True
    
    def stop_mear(self):
        self.write_and_read('MS_PRO', 'STOP')
    
    def set_mode(self, mode):
        self.write_and_read('SET', 'MS_MODE', mode)
        return True
    
    def set_std_mode(self):
        self.set_mode('STANDARD_M')
        return True
    
    def set_std_graph_mode(self):
        self.set_mode('STANDARD_GRAPH_M')
        return True
    
    def set_std_pk_mode(self):
        self.set_mode('STANDARD_PK_M')
    
    def set_hysterese_mode(self):
        self.set_mode('HYSTERESE_M')
    
    def get_mode(self):
        return self.write_and_read('GET', 'MS_MODE')
    
    def get_single_value(self):
        ret = self.write_and_read('GET','MS_VALUE')
        if ret == '"DEVICE BUSY"':
            return None
        elif ret == 'FINISHED':
            time.sleep(0.1)
            # ret = self.write_and_read('GET','MS_VALUE')
            ret = self.readline_only()
            return True, ret, "ok"
        else:
            return False, 0, ret
    
    def get_buffered_value(self, buffer=13):
        while True:
            data = self.device.readline().decode('utf-8').strip()
            if self.debug:
                print("Graph data resp: {}".format(data))
            resp_reg = ''' ?([\d.]*)> ?([\d.]*)'''
            match = re.search(resp_reg, data)
            ret = None
            if match:
                ret = {}
                ret['time'] = float(match.groups()[0])
                ret['value'] = float(match.groups()[1])
                yield True, ret['time'], ret['value'], "ok"
            else:
                ret = self.parse_resp(data.encode('utf-8'))
                if ret:
                    if ret['value'] == 'FINISHED':
                        break
                    else:
                        yield False, 0, 0, ret['value']
                        break
    
    def get_suitable_mode(self):
        ret = self.get_ms_method().lower()
        resp_reg = '''(shore)?(asker)?(type)?'''
        match = re.search(resp_reg, ret)
        if match:
            return ['STANDARD_M','STANDARD_GRAPH_M', 'STANDARD_PK_M']
        
        resp_reg = '''(irhd))?(vlrh)?'''
        match = re.search(resp_reg, ret)
        if match:
            return ['STANDARD_M','STANDARD_GRAPH_M', 'HYSTERESE_M']

    def isConnectRotation(self):
        ret = self.write_and_read('GET','DEV_OPTION')
        if ret == '"ROTATION DC"':
            return True
        else:
            return False

    def get_rotation_info(self):
        if self.isConnectRotation():
            sampleSize = int(self.write_and_read('GET','DEV_OPT_ROT_N'))
            mearCounts = int(self.write_and_read('GET','DEV_OPT_ROT_n'))
            return sampleSize, mearCounts
        else:
            return None,None
    
    def set_rotation_home(self):
        if self.isConnectRotation():
            ret = self.write_and_read('ROT_Nn','{},{}'.format(0,0))
            if ret == '"OUT OF RANGE"':
                return False, ret
            else:
                return True, 'ok'
    
    def set_rotation_pos(self,sample_N, mear_pos_n):
        if self.isConnectRotation():
            ret = self.write_and_read('ROT_Nn','{},{}'.format(sample_N,mear_pos_n))
            if ret == '"OUT OF RANGE"':
                return False, ret
            else:
                return True, 'ok'


class DummyDigitest(Digitest):
    def __init__(self):
        super(DummyDigitest, self).__init__()
        self.dummyCounter = 0
        # self.dummyType = '"ROTATION DC"'
        self.dummyType = '"FIX DC"'
        self.sampleCounts = 4
        self.mearCounts = 3
    
    def readline_only(self):
        resp = 'dummyResp'
        if self.debug:
            print("original resp in readline only: {}".format(resp))
        resp = 'dummyResp'
        if self.debug:
            print("parsing resp in readline only: {}".format(resp))
        if resp:
            return 'dummyResp'
        else:
            return None
    
    def write_and_read(self,cmd, para, value=None):
        max_wait_count = 200
        counter = 0
        return True
    
    def open_rs232(self, port=None, baudrate=9600, bytesize=None, parity=None, stopbits=None, timeout=None):
        self.device = None
        return self.device
    
    def close_rs232(self):
        pass

    def get_dev_name(self):
        return 'DummyDigitest'
    
    def get_dev_software_version(self):
        return 'DummyVersion1.0'

    def get_ms_duration(self):
        self.duration = 3.0
        return self.duration

    def set_ms_duration(self, value):
        self.duration = float(value)
        return self.duration

    def get_ms_method(self):
        return 'ShoreA'

    def isReady(self):
        ret = 'Ready'
        if ret:
            if ret[2] == 'ACTIVE':
                return False
            else:
                return True
        else:
            return False
    
    def set_remote(self, enabled=True):
        if enabled:
            print('SET','DEV_REMOTE_CONTROL','TRUE')
        else:
            print('SET','DEV_REMOTE_CONTROL','FALSE')

    def get_remote(self):
        return 'ShoreA'
    
    def start_mear(self):
        print('MS_PRO', 'START')
    
    def stop_mear(self):
        print('MS_PRO', 'STOP')
    
    def set_mode(self, mode):
        print('SET', 'MS_MODE', mode)
    
    def set_std_mode(self):
        self.set_mode('STANDARD_M')
    
    def set_std_graph_mode(self):
        self.set_mode('STANDARD_GRAPH_M')
    
    def set_std_pk_mode(self):
        self.set_mode('STANDARD_PK_M')
    
    def set_hysterese_mode(self):
        self.set_mode('HYSTERESE_M')
    
    def get_mode(self):
        return 'STANDARD_M'
    
    def get_single_value(self):
        time.sleep(0.1)
        if self.dummyCounter*0.1 < self.duration:
            ret = '"DEVICE BUSY"'
            self.dummyCounter += 1
        else:
            ret = 'FINISHED'
            self.dummyCounter = 0

        if ret == '"DEVICE BUSY"':
            return None
        elif ret == 'FINISHED':
            time.sleep(0.1)
            ret = random.random()*100
            return ret
        else:
            return None
    
    def get_buffered_value(self, buffer=13):
        while True:
            time.sleep(0.1)
            if self.dummyCounter < buffer:
                match = True
                ret = None
                self.dummyCounter += 1
            else:
                match = False
                ret = True
                self.dummyCounter = 0

            if match:
                ret = {}
                ret['time'] = self.dummyCounter * 0.1
                ret['value'] = random.random()*100
                yield True, ret['time'], ret['value'], "ok"
            else:
                if ret:
                    ret = {}
                    ret['value'] = 'FINISHED'
                    if ret['value'] == 'FINISHED':
                        break
                    else:
                        yield False, 0, 0, 'DEVICE BUSY'
                        break
    
    def get_suitable_mode(self):
        ret = 'ShoreA'.lower()
        resp_reg = '''(shore)?(asker)?(type)?'''
        match = re.search(resp_reg, ret)
        if match:
            return ['STANDARD_M','STANDARD_GRAPH_M', 'STANDARD_PK_M']
        
        resp_reg = '''(irhd))?(vlrh)?'''
        match = re.search(resp_reg, ret)
        if match:
            return ['STANDARD_M','STANDARD_GRAPH_M', 'HYSTERESE_M']

    def isConnectRotation(self):
        ret = self.dummyType
        if ret == '"ROTATION DC"':
            return True
        else:
            return False

    def get_rotation_info(self):
        if self.isConnectRotation():
            sampleSize = self.sampleCounts
            mearCounts = self.mearCounts
            return sampleSize, mearCounts
        else:
            return None,None
    
    def set_rotation_home(self):
        if self.isConnectRotation():
            ret = True
            if ret == '"OUT OF RANGE"':
                return False, ret
            else:
                return True, 'ok'
        else:
            return True, 'ok'
    
    def set_rotation_pos(self,sample_N, mear_pos_n):
        if self.isConnectRotation():
            self.sampleCounts = sample_N
            self.mearCounts = mear_pos_n
            ret = True
            if ret == '"OUT OF RANGE"':
                return False, ret
            else:
                return True, 'ok'
        else:
            return True, 'ok'
            
def main():
    ba = DummyDigitest()
    # input = b'GET(MS_MODE),' # exp_crc = '05F9' 
    # result = ba.get_cksum(input)
    # print(result)

    def print_data(data):
        print('I am callback: {}'.format(data))


    # resp = 'E0000,MS_DURATION=5,30AA\r\n'
    # par_result = ba.parse_resp(resp)
    # print(par_result)
    ba.open_rs232("COM3")
    ret = ba.get_dev_name()
    print(ret)
    ret = ba.get_dev_software_version()
    print(ret)
    ret = ba.get_ms_method()
    print(ret)
    ba.config(debug=True)
    ba.set_remote(True)
    ba.set_mode('STANDARD_M')
    duration_s = 1
    ret = ba.set_ms_duration(duration_s)
    print(ret)
    for i in range(3):
        time.sleep(0.1)
        ba.set_remote(True)
        ba.start_mear()
        
        while True:
            ret = ba.get_single_value()
            print('final resp of step {}: {}'.format(i, ret))
            if ret:
                break
            else:
                time.sleep(0.1)
    
    # ret = ba.set_remote(False)

    # ret = ba.set_remote(True)
    
    # ret = ba.set_mode('STANDARD_GRAPH_M')
    # print(ret)
    # duration_s = 10
    # ret = ba.set_ms_duration(duration_s)
    # print(ret)
    # ba.config(debug=True)
    # ret = ba.start_mear()
    # print('I am waiting for result')
    
    # getBuffer = ba.get_buffered_value()
    # for b in getBuffer:
    #     print(b)
    
    
    ba.config(wait_cmd=True)
    ba.set_remote(False)

    ba.close_rs232()

    # plt.plot(x,y)
    # plt.show()

def test_rotation_single_mear():
    ba = DummyDigitest()

    def mear(ba):
        ret = ba.start_mear()
        while True:
            ret = ba.get_single_value()
            if ret:
                return float(ret[1])
            else:
                time.sleep(0.1)

    
    ba.open_rs232("COM3")

    ret = ba.get_ms_method()
    print(ret)
    ba.config(debug=True)
    ba.set_remote(True)
    ba.set_std_mode()
    duration_s = 1
    ret = ba.set_ms_duration(duration_s)
    print(ret)

    ba.config(debug=False)
    ret = ba.isConnectRotation()
    print(ret)
    sample_N, mear_n = ba.get_rotation_info()

    ret = ba.set_rotation_home()
    print(ret)

    for N in range(sample_N):
        for n in range(mear_n):
            ret = ba.set_rotation_pos(N+1,n+1)
            if not ret[0]:
                print(ret[1])
                return
            else:
                print(ret[1])
                ret = mear(ba)
                print('Hardness Result: {}'.format(ret))
                time.sleep(1)
    ba.set_rotation_home()
    ba.close_rs232()

def test_rotation_graph_mear():
    ba = DummyDigitest()
    print(ba.isConnectRotation())
    
    ba.open_rs232("COM3")

    ret = ba.get_ms_method()
    print(ret)
    ba.config(debug=True)
    ba.set_remote(True)
    ba.set_std_graph_mode()
    duration_s = 3
    ret = ba.set_ms_duration(duration_s)
    print(ret)

    ba.config(debug=False)
    ret = ba.isConnectRotation()
    print(ret)
    sample_N, mear_n = ba.get_rotation_info()

    ret = ba.set_rotation_home()
    print(ret)

    for N in range(sample_N):
        for n in range(mear_n):
            ret = ba.set_rotation_pos(N+1,n+1)
            if not ret[0]:
                print(ret[1])
                return
            else:
                print(ret[1])
                ba.start_mear()
                ret = ba.get_buffered_value()
                for r in ret:
                    print('Hardness Result: {}'.format(r))
                time.sleep(1)
    ba.set_rotation_home()
    ba.close_rs232()

if __name__ == '__main__':
    # test_rotation_single_mear()
    test_rotation_graph_mear()
    