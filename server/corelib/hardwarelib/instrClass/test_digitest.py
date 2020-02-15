import threading
import time
import re
import matplotlib.pyplot as plt
import sys
from digitest import Digitest
import random

def main():
    ba = Digitest()
    # input = b'GET(MS_MODE),' # exp_crc = '05F9' 
    # result = ba.get_cksum(input)
    # print(result)

    def print_data(data):
        print('I am callback: {}'.format(data))


    # resp = 'E0000,MS_DURATION=5,30AA\r\n'
    # par_result = ba.parse_resp(resp)
    # print(par_result)
    ba.open_rs232("COM4")
    ret = ba.get_dev_name()
    print(ret)
    ret = ba.get_dev_software_version()
    print(ret)
    ret = ba.get_ms_method()
    print(ret)
    ba.config(debug=False)
    ba.set_remote(True)
    ba.set_mode('STANDARD_M')
    duration_s = 3
    ret = ba.set_ms_duration(duration_s)
    print(ret)
    ret = ba.isConnectRotation()
    print('rotation mode: {}'.format(ret))
    for i in range(2):
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
        
    
    ba.config(wait_cmd=True)
    ba.set_remote(False)

    ba.close_rs232()

def test_rotation_single_mear():
    ba = Digitest()

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
    ba = Digitest()
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
    main()