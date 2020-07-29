
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
    
    def pause_step(self):
        self.pauseQueue.put(True)

    def wait_for_continue(self):
        retStatus = self.pauseQueue.get()
        self.pauseQueue.task_done()
        return retStatus

class SetupStep(DigiCenterStep):
    def __init__(self):
        super(SetupStep,self).__init__()
    
    def set_paras(self,step):
        super().set_paras(step)
    
    @DigiCenterStep.deco
    def do(self):
        if self.hwDigitest.isConnectRotation():
            self.hwDigitest.set_rotation_home()
        self.set_result('PASS','PASS')
        return self.result


class TeardownStep(DigiCenterStep):
    def __init__(self):
        super(TeardownStep,self).__init__()

    def set_paras(self,step):
        super().set_paras(step)
        self.safeTemp = float(list(filter(lambda name: name['name'] == 'safe temperature', self.paras))[0]['value'])

    @DigiCenterStep.deco
    def do(self):
        time.sleep(dummy_delay)
        # to set the temperature to safe range
        self.hwDigichamber.set_gradient_up(0)
        self.hwDigichamber.set_gradient_down(0)
        target = self.safeTemp
        tol = 0.05
        UL = target * (1+tol)
        LL = target * (1-tol)
        self.hwDigichamber.set_setPoint(target)
        self.commCallback('update_gauge_ref',target)
        self.hwDigichamber.set_manual_mode(True)
        curT = self.hwDigichamber.get_real_temperature()
        initT = curT
        while True:
            if self.isInterrupted():
                # stop process immediately
                break
            ## START ##########only for simulation of chamber###########
            if (target-curT)<0:
                signSlope = -1*60
            else:
                signSlope = 60
            curT = curT + signSlope/60*1 + random.random()*0.02
            self.hwDigichamber.set_dummy_act_temp(round(curT,1))
            ## END   ###################################################
            curT = self.hwDigichamber.get_real_temperature()
            roundValue = round(curT,1)
            prog = round( (abs(roundValue - initT) / abs(target-initT)) * 100, 0)
            self.set_result(roundValue,'WAITING',unit='&#8451', progs=prog)
            self.resultCallback(self.result)
            if curT<=UL and curT>=LL:
                break
            time.sleep(1)
            self.lg.debug('[In teardown step] curt: {}'.format(curT))
        try:
            self.hwDigichamber.set_manual_mode(False)
            self.hwDigitest.stop_mear()
            self.hwDigitest.set_remote(False)
        except:
            print('teardown set hardware failed')
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
    
    @DigiCenterStep.deco
    def do(self):
        # set start temperature
        curT = self.hwDigichamber.get_real_temperature()
        roundValue = round(curT,1)
        initT = curT
        self.update_actTarget()
        self.set_gradient_process(self.actTarget,self.slope)

        # set manual mode on
        self.hwDigichamber.set_manual_mode(True)

        # update new target ref to client
        self.commCallback('update_gauge_ref',self.actTarget)

        UL = self.actTarget + self.tol
        LL = self.actTarget - self.tol
        counter = 0
        loopInterval = 0.5 #second
        sendInterval = 10 #second
        while curT>UL or curT<LL:
            print('target value {}'.format(self.actTarget))
            if self.stopMsgQueue.qsize()>0:
                # stop process immediately
                roundValue = round(curT,1)
                self.set_result(roundValue,'FAIL',unit='&#8451', progs=100)
                break
            time.sleep(loopInterval)
            roundValue = round(curT,1)
            prog = round( (abs(roundValue - initT) / abs(self.actTarget-initT)) * 100, 0)
            # prog = round( (1-(abs(roundValue - self.actTarget) / self.actTarget)) * 100, 0)
            if counter*loopInterval >= sendInterval:
                
                self.set_result(roundValue,'WAITING',unit='&#8451', progs=prog)
                self.resultCallback(self.result)
                counter = 0
            else:
                self.set_result(roundValue,'UPDATE_PROGRESS_ONLY',unit='&#8451', progs=prog)
                self.resultCallback(self.result)
                counter += 1
            # yield self.result
            if (self.actTarget-curT)<0:
                signSlope = -self.slope
            else:
                signSlope = self.slope
            ## START ##########only for simulation of chamber###########
            curT = curT + signSlope/60*1 + random.random()*0.02
            self.hwDigichamber.set_dummy_act_temp(round(curT,1))
            ## END   ###################################################
            curT = self.hwDigichamber.get_real_temperature()
            roundValue = round(curT,1)
            if curT<=UL and curT>=LL:
                break
        self.set_result(roundValue,'PASS',unit='&#8451', progs=100)
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
        # self.port = list(filter(lambda name: name['name'] == 'port', self.paras))[0]['value']
        self.method = list(filter(lambda name: name['name'] == 'method', self.paras))[0]['value']
        self.mode = list(filter(lambda name: name['name'] == 'mode', self.paras))[0]['value']
        self.mearTime = float(list(filter(lambda name: name['name'] == 'measuring time', self.paras))[0]['value'])
        self.numTests = int(list(filter(lambda name: name['name'] == 'number of measurement', self.paras))[0]['value'])
        self.numericMethod = list(filter(lambda name: name['name'] == 'numerical method', self.paras))[0]['value']
    
    def config_digitest(self):
        self.hwDigitest.set_remote(True)
        self.hwDigitest.set_mode(self.mode)
        self.hwDigitest.set_ms_duration(self.mearTime)
        self.hwDigitest.config(debug=False, wait_cmd = True)
        try:
            sampleSize, self.system_numTests = self.hwDigitest.get_rotation_info()
            self.isRotation_model = self.hwDigitest.isConnectRotation()
        except:
            pass
    
    def mear_process(self):
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
            h_data = self.hwDigitest.get_single_value(curT)
            endTime = time.time()
            countdownTime = endTime - startTime
            prog = round( countdownTime / (self.mearTime+20) * 100, 0)
            if h_data is not None:
                output_data = round(h_data,1)
                self.commCallback('only_update_hardness_indicator',output_data)
                self.set_result(output_data,'WAITING',hardness_dataset=self.singleResult, progs=100)
                self.resultCallback(self.result)
                return output_data
            else:
                self.set_result(None,'WAITING',hardness_dataset=self.singleResult, progs=prog)
                self.resultCallback(self.result)
                time.sleep(0.1)

    def go_next_measurment_process(self):
        # handle process between different model of digiChamber
        if not self.isRotation_model:
            # self.set_result(self.singleResult['result'],'PAUSE',hardness_dataset=self.singleResult, progs=100) 
            # self.resultCallback(self.result)
            self.commCallback('show_move_sample_dialog',self.singleResult)
            self.pause_step()
            retStatus = self.wait_for_continue()
            if retStatus == 'retry':
                self.retry = False
                self.singleResult['done'] = False
                self.singleResult['dataset'].pop()
            return None
        else:
            # rotate on next position sample
            self.lg.debug('rotate to next position of {}'.format(len(self.singleResult['dataset'])))
            move_completed, response = self.hwDigitest.goNext()
            if move_completed:
                return None
            else:
                return 'move_fail'

    @DigiCenterStep.deco
    def do(self):            
        # config
        self.config_digitest()
        # rotate on next position sample
        self.lg.debug('rotate to first sample with position')
        move_completed, response = self.hwDigitest.set_rotation_pos(1,1)
        # mear
        for smp in self.batchInfoForSamples:
            self.lg.debug('####### current sample ######')
            # {'id': 0, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 0}, 'color': 'red'}
            # {'id': 1, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 1}, 'color': 'red'}
            # {'id': 2, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 2}, 'color': 'red'}
            # {'id': 3, 'status': 'filled', 'batchInfo': {'project': '0729', 'batch': '2', 'notes': '', 'seq_name': 'C:\\data_exports\\seq_files\\singletest.seq', 'numSample': 4, 'sampleId': 3}, 'color': 'red'}
            self.lg.debug('{}'.format(smp))
            self.lg.debug('####### current sample ######')
            while True:
                if self.isInterrupted():
                    self.set_result(round(0.0,1),'FAIL',hardness_dataset=self.singleResult, progs=100)
                    return self.result
                
                sampleIndex = smp['id']
                self.lg.debug('[sampleIndex] {}'.format(sampleIndex))
                output_data = self.mear_process()
                self.lg.debug('[output_data] {}'.format(output_data))

                if output_data:
                    self.add_data(output_data,sampleIndex)
                    self.lg.debug('[self.singleResult] {}'.format(self.singleResult))

                if self.singleResult['done']:
                    # all points in current sample done
                    if sampleIndex >= len(self.batchInfoForSamples)-1:
                        # finishd all samples
                        self.set_result(self.singleResult['result'],'PASS', 
                                        eventName=r'{}'.format(sampleIndex), 
                                        hardness_dataset=self.singleResult, 
                                        progs=100,
                                        batchInfo=smp
                                        )
                        self.reset_result()
                        return self.result
                    # go to next sample
                    self.set_result(self.singleResult['result'],'MEAR_NEXT', None, 
                                    eventName=r'{}'.format(sampleIndex), 
                                    hardness_dataset=self.singleResult,
                                    progs=100,
                                    batchInfo=smp) 
                    self.resultCallback(self.result)
                    self.reset_result()
                    status = self.go_next_measurment_process()
                    if status == 'move_fail':
                        self.set_result(round(0.0,1),'FAIL',hardness_dataset=self.singleResult, progs=100)
                        return self.result
                    break
                
                if self.isInterrupted():
                    self.set_result(round(0.0,1),'FAIL',hardness_dataset=self.singleResult, progs=100)
                    return self.result

                status = self.go_next_measurment_process()
                if status == 'move_fail':
                    self.set_result(round(0.0,1),'FAIL',hardness_dataset=self.singleResult, progs=100)
                    return self.result

        return self.result

    def add_data(self, value, sampleIndex):      
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
        self.singleResult['sampleid'] = sampleIndex
    
    def get_max_mear_counts(self):
        if self.isRotation_model:
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