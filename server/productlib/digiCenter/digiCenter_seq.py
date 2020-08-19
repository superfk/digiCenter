
import asyncio
from datetime import datetime
from queue import Empty
import time
import random
import numpy as np
import traceback

from numpy.core.shape_base import block

dummy_delay = 0.1


class DigiCenterStep(object):
    def __init__(self):
        self.category = ''
        self.itemname = ''
        self.stepid = None
        self.contained_steps = []
        self.paras = []
        self.result = {}
        self.enabled = True
        self.startTime = None
        self.endTime = None
        self.insideLoop = False
        self.resultCallback = None
        self.commCallback = None
        self.hwDigichamber = None
        self.hwDigitest = None
        self.initTime = None
        self.loopIter = 0
        self.batchinfo = None
        self.batchInfoForSamples = None
        self.stopMsgQueue = None
        self.pauseQueue = None
        self.lg = None
        self.force_manual_mode = False
        self.sysConfig = None
        self.errorOccurred = False
        self.errorDetail = ''
        

    def initResult(self):
        self.result = {'stepid':0,
        'name':None, 
        'value': None,
        'unit':None, 
        'status': 'FAIL',
        'startT':None,
        'endT':None,
        'exeT':0, 
        'relTime':0,
        'actTemp':0,
        'actHum': 0,
        'prograss':0,
        'hardness_dataset':None,
        'project': None,
        'batch': None,
        'sampleIndex':0,
        'sampleId':0,
        'seq_name':None}
        

    def set_paras(self,step):
        self.stepid = step['id']
        self.category = step['cat']
        self.itemname = step['subitem']['item']
        self.paras = step['subitem']['paras']
        self.enabled = step['subitem']['enabled']
    
    @staticmethod
    def deco(func):
        def wrapper(self,*args ):
            print('start of do process')
            self.initResult()
            self.set_startTime()
            self.result['startT']=self.startTime
            if self.enabled:
                self.result = func(self,*args)
                self.incre_one_loopiter()
            else:
                self.set_result('','SKIP',unit='')
            self.set_endTime()
            self.result['endT']=self.endTime
            self.result['exeT']=self.endTime-self.startTime
            self.resultCallback(self.result)
            print('end of do process')
            return self.result 
        return wrapper
    
    def set_digiChamber_hw_control(self, digiChamberController):
        self.hwDigichamber = digiChamberController
    
    def set_digitest_hw_control(self, digitest):
        self.hwDigitest = digitest

    def set_digitest_force_manual_mode(self, forceManualMode):
        self.force_manual_mode = forceManualMode
        
    def do(self):
        return self.result

    def get_result(self):
        return self.result
    
    def set_startTime(self):
        self.startTime = time.time()
    
    def set_endTime(self):
        self.endTime = time.time()
    
    def get_test_interval(self):
        t = self.endTime - self.startTime
        # print('single test interval: {}'.format(t))
        return t
    
    def set_sysConfig(self,config):
        self.sysConfig = config
    
    def set_result(self, value, status, unit=None, eventName=None, hardness_dataset=None, progs=0, batchInfo=None):
        if batchInfo:
            self.result['project'] = batchInfo['batchInfo']['project']
            self.result['batch'] = batchInfo['batchInfo']['batch']
            self.result['sampleIndex'] = batchInfo['id']
            self.result['sampleId'] = batchInfo['batchInfo']['sampleId']
            self.result['seq_name'] = batchInfo['batchInfo']['seq_name']
        else:
            self.result['project'] = ''
            self.result['batch'] = ''
            self.result['sampleId'] = ''
            self.result['seq_name'] = ''
        self.result['stepid'] = self.stepid
        self.result['name'] = self.itemname
        self.result['value'] = value
        self.result['unit'] = unit
        self.result['status'] = status
        self.result['eventName'] = eventName
        self.result['relTime'] = time.time() - self.initTime
        self.result['prograss'] = progs
        self.result['hardness_dataset'] = hardness_dataset
        self.result['category'] = self.category
        try:
            self.result['actTemp'] = self.hwDigichamber.get_real_temperature()
            self.result['actHum'] = self.hwDigichamber.get_real_humidity()
        except:
            self.result['actTemp'] = None
            self.result['actHum'] = None
        return self.result
    
    def set_result_callback(self,resultCallback):
        self.resultCallback = resultCallback
    
    def set_communicate_callback(self,commCallback):
        self.commCallback = commCallback

    def set_initTime(self,initTime):
        self.initTime = initTime
    
    def incre_one_loopiter(self):
        self.loopIter += 1
    
    def reset_loopiter(self):
        self.loopIter = 0
    
    def set_batchinfo(self,batchinfo):
        self.batchinfo = batchinfo

    def set_batchInfoForSamples(self, batchInfoForSamples):
        self.batchInfoForSamples = batchInfoForSamples

    def isInterrupted(self):
        return self.stopMsgQueue.qsize()>0

    def wait_for_continue(self):
        retStatus = self.pauseQueue.get()
        return retStatus

    def set_error_occurred(self, error=False, detail=''):
        self.errorOccurred = error
        self.errorDetail = detail

class SetupStep(DigiCenterStep):
    def __init__(self):
        super(SetupStep,self).__init__()
    
    def set_paras(self,step):
        super().set_paras(step)
    
    @DigiCenterStep.deco
    def do(self):
        self.hwDigitest.config(debug=False, wait_cmd = True)
        if self.hwDigitest.isConnectRotation():
            if not self.force_manual_mode:
                # self.hwDigitest.set_rotation_home()
                pass
        self.set_result('PASS','PASS')
        return self.result


class TeardownStep(DigiCenterStep):
    def __init__(self):
        super(TeardownStep,self).__init__()

    def set_paras(self,step):
        super().set_paras(step)
        self.safeTemp = float(list(filter(lambda name: name['name'] == 'safe temperature', self.paras))[0]['value'])
        self.waitMinute = float(list(filter(lambda name: name['name'] == 'waiting time', self.paras))[0]['value'])

    @DigiCenterStep.deco
    def do(self):
        retStatus = 'normal'
        if self.errorOccurred: 
            # ask if need to go teardown
            self.commCallback('show_go_teardown_dialog', self.errorDetail )
            self.lg.debug('wait for user chose if needs to run teardown step')
            retStatus = self.wait_for_continue()
        if retStatus == 'run_teardown' or retStatus == 'normal':
            # to set the temperature to safe range
            self.hwDigichamber.set_gradient_up(0)
            self.hwDigichamber.set_gradient_down(0)
            target = self.safeTemp
            tol = 5 # degree
            UL = target + tol
            LL = target - tol
            self.hwDigichamber.set_setPoint(target)
            self.commCallback('update_gauge_ref',target)
            self.hwDigichamber.set_manual_mode(True)
            curT = self.hwDigichamber.get_real_temperature()
            initT = curT
            initTime = time.time()
            startWait = False
            while True:
                if self.isInterrupted():
                    # stop process immediately
                    break
                ## START ##########only for simulation of chamber###########
                if (target-curT)<0:
                    signSlope = -1*60
                else:
                    signSlope = 60
                curT = curT + signSlope/60*1 + random.random()*0.002
                self.hwDigichamber.set_dummy_act_temp(curT)
                ## END   ###################################################
                curT = self.hwDigichamber.get_real_temperature()
                # prog = round( (abs(curT - initT) / abs(target-initT)) * 100, 0)
                # self.set_result(curT,'WAITING',unit='&#8451', progs=prog)
                # self.resultCallback(self.result)
                if (curT<=UL and curT>=LL) or startWait:
                    startWait = True
                    countTime = time.time() - initTime
                    if countTime >= self.waitMinute*60:
                        break
                    prog = round( countTime / (self.waitMinute*60) * 100 * 0.5, 0) + 50
                    self.set_result(countTime,'WAITING',unit='s', progs=prog)
                    self.resultCallback(self.result)
                else:
                    prog = round( (abs(curT - initT) / abs(target-initT)) * 100 * 0.5, 0)
                    self.set_result(curT,'WAITING',unit='&#8451', progs=prog)
                    self.resultCallback(self.result)
                    initTime = time.time()
                time.sleep(1)
        try:
            self.hwDigichamber.set_manual_mode(False)
            self.commCallback('update_machine_status',{'dt':None,'temp':{'status':1, 'value':None}, 'hum':{'status':1, 'value':None}})
        except:
            self.lg.debug('set manual mode for digiChamber failed')
        try:
            self.hwDigitest.stop_mear()
            self.hwDigitest.set_remote(False)
            self.commCallback('update_machine_status',{'dt':{'status':1, 'value':None},'temp':None, 'hum':None})
        except:
            self.lg.debug('set manual mode for digiTest failed')
        finally:
            self.set_result('PASS','PASS',progs=100)
        return self.result

class TemperatureStep(DigiCenterStep):
    def __init__(self):
        super(TemperatureStep,self).__init__()
        self.targetTemp = 0.0
        self.tol = 0
        self.slope = 0.0 #K/min -> 1/60 K/s
        self.incre = 0.0
        self.actTarget = 0.0

    def set_paras(self,step):
        super().set_paras(step)
        self.targetTemp = float(list(filter(lambda name: name['name'] == 'target temperature', self.paras))[0]['value'])
        self.tol = float(list(filter(lambda name: name['name'] == 'tolerance', self.paras))[0]['value']) # degree
        self.slope = float(list(filter(lambda name: name['name'] == 'slope', self.paras))[0]['value'])
        self.incre = float(list(filter(lambda name: name['name'] == 'increment', self.paras))[0]['value'])
        self.actTarget = self.targetTemp
    
    def set_gradient_process(self, target, slope):
        curT = self.hwDigichamber.get_real_temperature()
        self.hwDigichamber.set_setPoint(curT)
        if curT >= target:
            self.hwDigichamber.set_gradient_down(slope)
        else:
            self.hwDigichamber.set_gradient_up(slope)
        self.hwDigichamber.set_setPoint(target)
    
    def set_temperature_imporve_options(self):
        try:
            self.hwDigichamber.set_tempShift(self.sysConfig['system']['temp_shift_K'])
        except:
            self.hwDigichamber.set_tempShift(2)
        self.hwDigichamber.set_dryer(1)
        self.hwDigichamber.set_compAir(1)
        self.hwDigichamber.set_controlSupplyAir(1)

    @DigiCenterStep.deco
    def do(self):
        # set start temperature
        curT = self.hwDigichamber.get_real_temperature()
        initT = curT
        self.update_actTarget()
        self.set_gradient_process(self.actTarget,self.slope)

        # set manual mode on
        self.hwDigichamber.set_manual_mode(True)
        self.commCallback('update_machine_status',{'dt':None,'temp':{'status':2, 'value':None}, 'hum':{'status':2, 'value':None}})

        # set options
        self.set_temperature_imporve_options()

        # update new target ref to client
        self.commCallback('update_gauge_ref',self.actTarget)

        UL = self.actTarget + self.tol
        LL = self.actTarget - self.tol
        counter = 0
        loopInterval = 0.5 #second
        sendInterval = 10 #second
        while curT>UL or curT<LL:
            if self.stopMsgQueue.qsize()>0:
                # stop process immediately
                self.set_result(curT,'FAIL',unit='&#8451', progs=100)
                break
            # time.sleep(loopInterval)
            time.sleep(loopInterval)
            prog = round( (abs(curT - initT) / abs(self.actTarget-initT)) * 100, 0)
            if counter*loopInterval >= sendInterval:
                self.set_result(curT,'WAITING',unit='&#8451', progs=prog)
                self.resultCallback(self.result)
                counter = 0
            else:
                self.set_result(curT,'UPDATE_PROGRESS_ONLY',unit='&#8451', progs=prog)
                self.resultCallback(self.result)
                counter += 1
            # yield self.result
            if (self.actTarget-curT)<0:
                signSlope = -self.slope
            else:
                signSlope = self.slope
            ## START ##########only for simulation of chamber###########
            
            curT = curT + signSlope/60*1 + random.random()*0.002
            
            self.hwDigichamber.set_dummy_act_temp(curT)
            ## END   ###################################################
            curT = self.hwDigichamber.get_real_temperature()
            
            if curT<=UL and curT>=LL:
                break
        self.set_result(curT,'PASS',unit='&#8451', progs=100)
        # self.hwDigichamber.set_manual_mode(False)
        return self.result

    def update_actTarget(self):
        incre = self.loopIter*self.incre
        self.actTarget = self.targetTemp + incre

class HardnessStep(DigiCenterStep):
    def __init__(self):
        super(HardnessStep,self).__init__()
        self.port = None
        self.method = None
        self.mode = None
        self.mearTime = None # sec
        self.numTests = 3
        self.system_numTests = 3
        self.numericMethod = 'mean'
        self.curSampleId = 0
        self.curMearCounts = 0
        self.singleResult = {'dataset':[], 'result':0, 'std':0.0, 'done':False,
         'method':self.numericMethod, 'totalCounts':0, 'sampleid':self.curSampleId}
        self.retry = False
        self.overall_result = []
        self.isRotation_model = False

    def set_paras(self,step):
        super().set_paras(step)
        self.mearTime = float(list(filter(lambda name: name['name'] == 'measuring time', self.paras))[0]['value'])
        self.numTests = int(list(filter(lambda name: name['name'] == 'number of measurement', self.paras))[0]['value'])
        self.numericMethod = list(filter(lambda name: name['name'] == 'numerical method', self.paras))[0]['value']
    
    def config_digitest(self):
        self.hwDigitest.set_remote(True)
        self.hwDigitest.set_std_mode()
        self.hwDigitest.set_ms_duration(self.mearTime)
        try:
            sampleSize, self.system_numTests = self.hwDigitest.get_rotation_info()
            self.isRotation_model = self.hwDigitest.isConnectRotation()
        except:
            pass
    
    def mear_process(self,currentSample):
        h_data = None
        curT = 0.0
        startTime = time.time()
        self.hwDigitest.start_mear_direct()
        while True:
            # get value
            try:
                # only for demo mode
                curT = self.hwDigichamber.get_real_temperature()           
            except:
                pass
            statusCode, h_data = self.hwDigitest.get_single_value(curT)
            endTime = time.time()
            countdownTime = endTime - startTime
            prog = round( countdownTime / (self.mearTime+20) * 100, 0)
            if statusCode == 1 or statusCode < 0:
                if statusCode < 0:
                    self.lg.debug('Error: DISTANCE_TOO_BIG when measuring')
                    h_data = 0.0
                    return 'ERROR_STOP', h_data
                output_data = round(h_data,1)
                self.commCallback('only_update_hardness_indicator',output_data)
                self.commCallback('update_machine_status',{'dt':{'status':1, 'value':output_data},'temp':None, 'hum':None})
                self.set_result(None,'WAITING',hardness_dataset=self.singleResult, progs=100, batchInfo=currentSample)
                self.resultCallback(self.result)
                return 'OK', output_data
            else:
                self.commCallback('update_machine_status',{'dt':{'status':2, 'value':None},'temp':None, 'hum':None})
                self.set_result(None,'WAITING',hardness_dataset=self.singleResult, progs=prog, batchInfo=currentSample)
                self.resultCallback(self.result)
                # time.sleep(0.5)
                time.sleep(0.5)

    def go_next_measurment_process(self,currentSample,currentPosition):
        sampleIndex = currentSample['id']
        sampleIndexInBatch = currentSample['batchInfo']['sampleId']
        self.lg.debug('[sampleIndex] {}'.format(sampleIndex))
        self.lg.debug('[sampleIndexInBatch] {}'.format(sampleIndexInBatch))
        # handle process between different model of digiChamber
        if self.force_manual_mode:
            self.lg.debug('force manual mode enabled')
        if not self.isRotation_model or self.force_manual_mode:
            # self.set_result(self.singleResult['result'],'PAUSE',hardness_dataset=self.singleResult, progs=100) 
            # self.resultCallback(self.result)
            curResult = self.singleResult
            curResult['curSampleIdx'] = sampleIndex + 1
            curResult['curSampleIdInBatch'] = sampleIndexInBatch + 1 
            self.commCallback('show_move_sample_dialog',curResult)
            self.lg.debug('wait for user move sample')
            retStatus = self.wait_for_continue()
            self.lg.debug('user moved sample completely')
            
            if retStatus == 'retry':
                self.retry = False
                self.singleResult['done'] = False
                if len(self.singleResult['dataset'])>0:
                    self.singleResult['dataset'].pop()
            return None
        else:
            # rotate on next position sample
            N = sampleIndex + 1
            n = currentPosition 
            self.lg.debug('rotate to next position of {}'.format(n))
            time.sleep(0)
            move_completed, response = self.hwDigitest.set_rotation_pos(N,n)
            if move_completed:
                return None
            else:
                return 'move_fail'

    @DigiCenterStep.deco
    def do(self):            
        # config
        self.config_digitest()
        # rotate on next position sample
        # self.lg.debug('rotate to first sample with position')
        # move_completed, response = self.hwDigitest.set_rotation_pos(1,1)
        # mear
        for smp in self.batchInfoForSamples:
            self.lg.debug('####### current sample ######')
            # {'id': 0, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 0}, 'color': 'red'}
            # {'id': 1, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 1}, 'color': 'red'}
            # {'id': 2, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 2}, 'color': 'red'}
            # {'id': 3, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 3}, 'color': 'red'}
            self.lg.debug('{}'.format(smp))
            self.lg.debug('####### current sample ######')
            self.reset_result()
            n = 1
            while True:
                if self.isInterrupted():
                    self.set_result(round(0.0,1),'FAIL',hardness_dataset=self.singleResult, progs=100)
                    return self.result

                sampleIndex = smp['id']
                sampleIndexInBatch = smp['batchInfo']['sampleId']
                
                # move
                status = self.go_next_measurment_process(smp, n)
                if status == 'move_fail':
                    self.set_result(round(0.0,1),'ERROR_STOP', eventName='move_fail',hardness_dataset=self.singleResult, progs=100)
                    return self.result
                # update current sample highlight
                self.set_result(None,'UPDATE_CURRENT_SAMPLEINDEX',hardness_dataset=self.singleResult, progs=0, batchInfo=smp)
                currentResult = self.result.copy()
                self.resultCallback(self.result)

                # mearsure
                self.hwDigitest.config(debug=False, wait_cmd = False)
                statusMsg, output_data = self.mear_process(smp)
                self.hwDigitest.config(debug=False, wait_cmd = True)
                self.lg.debug('[statusMsg, output_data] {}, {}'.format(statusMsg, output_data))
                if statusMsg == 'ERROR_STOP':
                    self.lg.debug('[output_data] {}'.format(output_data))
                    self.set_result(None,'ERROR_STOP',eventName='distance_too_big', hardness_dataset=self.singleResult, progs=100, batchInfo=smp)
                    return self.result

                # record data
                if output_data is not None:
                    self.add_data(output_data,sampleIndexInBatch)
                    self.lg.debug('[self.singleResult] {}'.format(self.singleResult))
                    n += 1
                
                # check mearsure done or not
                if self.singleResult['done']:
                    
                    self.lg.debug('self.singleResult is done? {}'.format(self.singleResult['done']))
                    # all points in current sample done
                    if sampleIndex >= len(self.batchInfoForSamples)-1:
                        self.lg.debug('sampleIndex >= len(self.batchInfoForSamples)-1: {}'.format(sampleIndex >= len(self.batchInfoForSamples)-1))
                        # finishd all samples
                        self.set_result(self.singleResult['result'],'PASS', 
                                        eventName=r'{}'.format(sampleIndex), 
                                        hardness_dataset=self.singleResult, 
                                        progs=100,
                                        batchInfo=smp
                                        )
                        currentResult = self.result.copy()
                        self.resultCallback(currentResult)
                        break
                    # go to next sample
                    self.set_result(self.singleResult['result'],'MEAR_NEXT', None, 
                                    eventName=r'{}'.format(sampleIndex), 
                                    hardness_dataset=self.singleResult,
                                    progs=100,
                                    batchInfo=smp)
                    currentResult = self.result.copy()
                    self.resultCallback(currentResult)
                    break
        self.commCallback('update_machine_status',{'dt':{'status':1, 'value':None},'temp':None, 'hum':None})
        return self.result

    def add_data(self, value, sampleIndexInBatch):      
        self.singleResult['dataset'].append(value)
            
        if self.get_mear_counts() >= self.get_max_mear_counts():
            self.singleResult['done'] = True
            
        if self.numericMethod == 'median':
            result = np.median(self.singleResult['dataset'])
        else:
            result = np.mean(self.singleResult['dataset'])
        stdev = np.std(self.singleResult['dataset'])
        self.singleResult['result'] = round(result,1)
        self.singleResult['std'] = round(stdev,1)
        self.singleResult['method'] = self.numericMethod
        self.singleResult['totalCounts'] = self.get_max_mear_counts()
        self.singleResult['sampleid'] = sampleIndexInBatch
    
    def get_max_mear_counts(self):
        if self.isRotation_model:
            if self.force_manual_mode:
                return self.numTests
            else:
                return self.system_numTests
        else:
            return self.numTests

    def get_mear_counts(self):
        return len(self.singleResult['dataset'])
    
    def reset_result(self):
        self.singleResult = {'dataset':[], 'result':0, 'std':0.0, 'done':False, 
        'method':self.numericMethod, 'totalCounts':self.get_max_mear_counts(), 'sampleid':0}

class WaitingStep(DigiCenterStep):
    def __init__(self):
        super(WaitingStep,self).__init__()
        self.condTime = 0 # min

    def set_paras(self,step):
        super().set_paras(step)
        self.condTime = float(list(filter(lambda name: name['name'] == 'conditioning time', self.paras))[0]['value'])

    @DigiCenterStep.deco
    def do(self):
        targetTime = self.condTime*60.0
        countdownTime = 0
        startTime = time.time()
        counter = 0
        loopInterval = 0.5 #second
        sendInterval = 10 #second
        # do time control
        while countdownTime<targetTime:
            if self.stopMsgQueue.qsize()>0:
                # stop process immediately
                break
            # time.sleep(0.27)
            time.sleep(0.27)
            endTime = time.time()
            countdownTime = endTime - startTime
            prog = round( countdownTime / targetTime * 100, 0)
            if counter*loopInterval >= sendInterval:
                self.set_result(round(countdownTime,1),'WAITING',unit='s', progs=prog)
                self.resultCallback(self.result)
                counter = 0
            else:
                self.set_result(round(countdownTime,1),'UPDATE_PROGRESS_ONLY',unit='s', progs=prog)
                self.resultCallback(self.result)
                counter += 1
        self.set_result(round(countdownTime,1),'PASS',unit='s', progs=100)
        return self.result


class ForLoopStartStep(DigiCenterStep):
    def __init__(self):
        super(ForLoopStartStep,self).__init__()
        self.loopCounts = 0
        self.containSteps = []
        self.loopid = 0

    def set_paras(self,step):
        super().set_paras(step)
        self.loopCounts = int(list(filter(lambda name: name['name'] == 'loop counts', self.paras))[0]['value'])
        self.loopid = list(filter(lambda name: name['name'] == 'loop id', self.paras))[0]['value']
    
    @DigiCenterStep.deco
    def do(self):
        print('Loop count {} in loop {}'.format(self.loopIter,self.loopid))            
        self.set_result(self.loopIter+1,'PASS')
        return self.result
    
    def set_containedSteps(self, containSteps):
         self.containSteps = containSteps
    
    def add_one_containStep(self, step):
        self.containSteps.append(step)

class ForLoopEndStep(DigiCenterStep):
    def __init__(self):
        super(ForLoopEndStep,self).__init__()
        self.loopCounts = 0
        self.loopid = 0
        self.loopDone = False

    def set_paras(self,step):
        super().set_paras(step)
        self.loopCounts = int(list(filter(lambda name: name['name'] == 'stop on', self.paras))[0]['value'])
        self.loopid = list(filter(lambda name: name['name'] == 'loop id', self.paras))[0]['value']
    
    @DigiCenterStep.deco
    def do(self):
        if self.loopIter >= self.loopCounts-1:
            self.loopDone = True
        self.set_result(self.loopIter+1,'PASS')
        return self.result
    
    def resetLoop(self):
        self.reset_loopiter()
        self.loopDone = False

class SubProgramStep(DigiCenterStep):
    def __init__(self):
        super(SubProgramStep,self).__init__()
        self.prog_path = None

    def set_paras(self,step):
        super().set_paras(step)
        self.prog_path = list(filter(lambda name: name['name'] == 'path', self.paras))[0]['value']

    @DigiCenterStep.deco
    def do(self):
        # do sub program control
        time.sleep(dummy_delay)
        self.set_result(1,'FAIL')
        return self.result

def main():
    pass


if __name__ == '__main__':
    main()