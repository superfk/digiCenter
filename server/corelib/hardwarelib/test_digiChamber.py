#!/usr/bin/python
# coding: latin-1
import socket
import sys
import time
import matplotlib.pyplot as plt
import random
from digiChamber import DigiChamber
import numpy as np
from scipy.stats import linregress

def get_slope(x,y,last=None):
    if last:
        try:
            x = x[-1*last:]
            y = y[-1*last:]
        except:
            pass
    return linregress(x, y)[0]

def plotAll(timeset,temp,setpoint,slope):
    fig, ax1 = plt.subplots()
    color = 'tab:red'
    ax1.set_xlabel('Time (minutes)')
    ax1.set_ylabel('Temperature', color=color)
    ax1.plot(timeset, temp, color=color, label='temp')
    ax1.plot(timeset, setpoint, color='tab:green',label='setpoint')
    ax1.legend()
    ax1.tick_params(axis='y', labelcolor=color)

    ax2 = ax1.twinx()  # instantiate a second axes that shares the same x-axis

    color = 'tab:blue'
    ax2.set_ylabel('Slope(K/min)', color=color)  # we already handled the x-label with ax1
    ax2.plot(timeset, slope, color=color,label='slope')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.legend()
    fig.tight_layout()  # otherwise the right y-label is slightly clipped
    plt.show()

def get_control_vars():
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    ret = dc.get_control_variables_info()
    dc.close()
    return ret

def sw_control_ramp_test(target = 40, tol = 5):
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    print('system info')
    print(dc.get_chamber_info())
    print('')
    # reset gredient to zero for deactivating gradient mode
    dc.set_gradient_up(0)
    dc.set_gradient_down(0)
    dc.set_setPoint(target)
    print('get setpoint: {}'.format(dc.get_setPoint()))
    print('')
    ctrl_var_info = dc.get_control_variables_info()
    print(ctrl_var_info)
    print('')
    data = []
    setpoints = []
    timeset = []
    slopes = []
    UL = target * (1+tol/100)
    LL = target * (1-tol/100)
    dc.set_manual_mode(True)
    init = time.time()
    while True:
        curt = (time.time() - init)/60
        value = dc.get_real_temperature()
        setp = dc.get_real_control_variable_value()
        timeset.append(curt)
        data.append(value)
        setpoints.append(setp)
        
        try:
            slope = get_slope(timeset,data,last=20)
        except IndexError:
            slope=0
        slopes.append(slope)
        print('target: {}'.format(target))
        print('current time: {} mins'.format(curt))
        print('current temp: {}'.format(value))
        print('get real setpoint: {}'.format(setp))
        print('slope: {}'.format(slope))
        print('')
        time.sleep(1)
        if value >= LL and value <= UL:
            print('reached target')
            break
    
    dc.set_manual_mode(False)
    dc.close()
    plotAll(timeset, data, setpoints, slopes)
    

def hw_control_ramp_test(target = 40, tol = 5, slope = 2):
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    print('system info')
    print(dc.get_chamber_info())
    print('')
    curt = dc.get_real_temperature()
    dc.set_setPoint(curt)
    if curt >= target:
        dc.set_gradient_down(slope)
    else:
        dc.set_gradient_up(slope)
    dc.set_setPoint(target)
    print('get setpoint: {}'.format(dc.get_setPoint()))
    print('')
    ctrl_var_info = dc.get_control_variables_info()
    print(ctrl_var_info)
    print('')
    data = []
    setpoints = []
    timeset = []
    slopes = []
    UL = target * (1+tol/100)
    LL = target * (1-tol/100)
    dc.set_manual_mode(True)
    init = time.time()
    while True:
        curt = (time.time() - init)/60
        value = dc.get_real_temperature()
        setp = dc.get_real_control_variable_value()
        timeset.append(curt)
        data.append(value)
        setpoints.append(setp)
        
        try:
            slope = get_slope(timeset,data,last=20)
        except IndexError:
            slope=0
        slopes.append(slope)
        print('target: {}'.format(target))
        print('current time: {} mins'.format(curt))
        print('current temp: {}'.format(value))
        print('get real setpoint: {}'.format(setp))
        print('slope: {}'.format(slope))
        print('')
        time.sleep(1)
        if value >= LL and value <= UL:
            print('reached target')
            break
    
    dc.set_manual_mode(False)
    dc.close()
    plotAll(timeset, data, setpoints, slopes)

def stable_test(min=5):
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    print('system info')
    print(dc.get_chamber_info())
    print('')
    target = dc.get_real_temperature()
    dc.set_gradient_up(0)
    dc.set_gradient_down(0)
    dc.set_setPoint(target)
    print('get setpoint: {}'.format(dc.get_setPoint()))
    print('')
    ctrl_var_info = dc.get_control_variables_info()
    print(ctrl_var_info)
    print('')
    data = []
    setpoints = []
    timeset = []
    slopes = []
    dc.set_manual_mode(True)
    init = time.time()
    while True:
        curt = (time.time() - init)/60
        value = dc.get_real_temperature()
        setp = dc.get_real_control_variable_value()
        timeset.append(curt)
        data.append(value)
        setpoints.append(setp)
        
        try:
            slope = get_slope(timeset,data,last=20)
        except IndexError:
            slope=0
        slopes.append(slope)
        print('target: {}'.format(target))
        print('current time: {} mins'.format(curt))
        print('current temp: {}'.format(value))
        print('get real setpoint: {}'.format(setp))
        print('slope: {}'.format(slope))
        print('')
        time.sleep(1)
        if curt >= min:
            print('time up')
            break
    
    dc.set_manual_mode(False)
    dc.close()
    plotAll(timeset, data, setpoints, slopes)

def stable_test_mode_off(min=5):
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    print('system info')
    print(dc.get_chamber_info())
    print('')
    target = dc.get_real_temperature()
    dc.set_gradient_up(0)
    dc.set_gradient_down(0)
    dc.set_setPoint(target)
    print('get setpoint: {}'.format(dc.get_setPoint()))
    print('')
    ctrl_var_info = dc.get_control_variables_info()
    print(ctrl_var_info)
    print('')
    data = []
    setpoints = []
    timeset = []
    slopes = []
    dc.set_manual_mode(False)
    init = time.time()
    while True:
        curt = (time.time() - init)/60
        value = dc.get_real_temperature()
        setp = dc.get_real_control_variable_value()
        timeset.append(curt)
        data.append(value)
        setpoints.append(setp)
        
        try:
            slope = get_slope(timeset,data,last=20)
        except IndexError:
            slope=0
        slopes.append(slope)
        print('target: {}'.format(target))
        print('current time: {} mins'.format(curt))
        print('current temp: {}'.format(value))
        print('get real setpoint: {}'.format(setp))
        print('slope: {}'.format(slope))
        print('')
        time.sleep(1)
        if curt >= min:
            print('time up')
            break
    
    dc.set_manual_mode(False)
    dc.close()
    plotAll(timeset, data, setpoints, slopes)

def get_temp():
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    ret = dc.get_real_temperature()
    dc.close()
    return ret

def get_hum():
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    ret = dc.get_real_humidity()
    dc.close()
    return ret

def queryInfo():
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    print('####### Control Variables ##########')
    ret = setCmd(dc, '11018', [])
    n = ret[1].decode('utf-8', 'ignore').strip()
    print('Number of control variables: {}'.format(n))
    ret = dc.get_control_variables_info()
    print('Content of control variables: {}'.format(ret))
    print('')
    print('####### Control Values ##########')
    ret = setCmd(dc, '13007', [])
    n = ret[1].decode('utf-8', 'ignore').strip()
    print('Number of control values: {}'.format(n))
    ret = dc.get_control_values_info()
    print('Content of control values: {}'.format(ret))
    print('')
    print('####### Measrued Values ##########')
    ret = setCmd(dc, '12012', [])
    n = ret[1].decode('utf-8', 'ignore').strip()
    print('Number of measured values: {}'.format(n))
    ret = dc.get_mear_values_info()
    print('Content of measured values: {}'.format(ret))
    print('')
    print('####### Digital output ##########')
    ret = setCmd(dc, '14007', [])
    n = ret[1].decode('utf-8', 'ignore').strip()
    print('Number of digital output: {}'.format(n))
    ret = dc.get_do_info()
    print('Content of digital output: {}'.format(ret))
    print('')
    print('####### Digital input ##########')
    ret = setCmd(dc, '15004', [])
    n = ret[1].decode('utf-8', 'ignore').strip()
    print('Number of digital input: {}'.format(n))
    ret = dc.get_di_info()
    print('Content of digital input: {}'.format(ret))
    print('')
    print('####### Messages ##########')
    ret = setCmd(dc, '17002', [])
    n = ret[1].decode('utf-8', 'ignore').strip()
    print('Number of message: {}'.format(n))
    ret = dc.get_msg_info()
    print('Content of message: {}'.format(ret))
    print('')
    
    dc.close()
    return ret

def setCmd(dc, cmdid, args):
    cmd = dc.create_cmd(cmdid, args)
    ret = dc.send_and_get(cmd)
    return ret

def cmd_test(cmdid, args):
    dc = DigiChamber(ip='169.254.206.212')
    dc.connect()
    ret = setCmd(dc, cmdid, args)
    dc.close()
    return ret

if __name__ == '__main__':
    # sw_control_ramp_test(target = 40, tol=1)
    # hw_control_ramp_test(target = 60, tol=1, slope=5)
    # stable_test(min=5)
    # stable_test_mode_off(min=5)
    ret = queryInfo()
    ret = get_temp()
    print(ret)
    ret = get_hum()
    print(ret)
    ret = cmd_test('12002',['2'])
    print(ret)