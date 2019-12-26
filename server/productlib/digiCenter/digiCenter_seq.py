
from datetime import datetime
import time
import threading
import random
import asyncio
import json
import types
import queue

dummy_delay = 0.1


class DigiCenterStep(object):
    def __init__(self):
        self.category = ''
        self.itemname = ''
        self.stepid = None
        self.contained_steps = []
        self.paras = []
        self.result = {'stepid':0,'name':None, 'value': None, 'status': 'FAIL','startT':None,'endT':None,'exeT':0}
        self.enabled = True
        self.startTime = None
        self.endTime = None
        self.insideLoop = False
        self.socketCallback = None
        self.resultCallback = None
        self.stopMsgQueue = False

    def set_paras(self,step):
        self.stepid = step['id']
        self.category = step['cat']
        self.itemname = step['subitem']['item']
        self.enabled = step['subitem']['enabled']
    
    @staticmethod
    def deco(func):
        def wrapper(self,*args ):
            print('start of do process')
            self.result = {'stepid':0,'name':None, 'value': None, 'status': 'FAIL','startT':None,'endT':None,'exeT':0}
            self.set_startTime()
            self.result['startT']=self.startTime
            self.result = func(self,*args)
            self.set_endTime()
            self.result['endT']=self.endTime
            self.result['exeT']=self.endTime-self.startTime
            self.resultCallback(self.result)
            print('end of do process')
            return self.result 
        return wrapper
    
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
    
    def set_result(self, value, status):
        self.result['stepid'] = self.stepid
        self.result['name'] = self.itemname
        self.result['value'] = value
        self.result['status'] = status
        return self.result

    def set_sockect_callback(self,socketCallback):
        self.socketCallback = socketCallback
    
    def set_result_callback(self,resultCallback):
        self.resultCallback = resultCallback

class SetupStep(DigiCenterStep):
    def __init__(self):
        super(SetupStep,self).__init__()
    
    def set_paras(self,step):
        super().set_paras(step)
    
    @DigiCenterStep.deco
    def do(self):
        time.sleep(dummy_delay)
        self.set_result('PASS','PASS')
        return self.result


class TeardownStep(DigiCenterStep):
    def __init__(self):
        super(TeardownStep,self).__init__()

    def set_paras(self,step):
        super().set_paras(step)

    @DigiCenterStep.deco
    def do(self):
        time.sleep(dummy_delay)
        self.set_result('PASS','PASS')
        return self.result

class TemperatureStep(DigiCenterStep):
    def __init__(self):
        super(TemperatureStep,self).__init__()
        self.targetTemp = 0.0
        self.slope = 0.0 #K/min -> 1/60 K/s

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.targetTemp = float(list(filter(lambda name: name['name'] == 'target temperature', paras))[0]['value'])
        self.slope = float(list(filter(lambda name: name['name'] == 'slope', paras))[0]['value'])
    
    @DigiCenterStep.deco
    def do(self):
        # do digichamber temperature control
        curT = random.random()*0.5 + 23
        tol = 0.5
        UL = self.targetTemp+tol
        CL = self.targetTemp-tol
        while curT>UL or curT<CL:
            if self.stopMsgQueue.qsize()>0:
                # stop process immediately
                break
            time.sleep(1)
            self.set_result(round(curT,1),'Waiting')
            self.resultCallback(self.result)
            # yield self.result
            if (self.targetTemp-curT)<0:
                signSlope = -self.slope
            else:
                signSlope = self.slope
            print('signSlope: {}'.format(signSlope))
            curT = curT + signSlope/60*1 + random.random()*0.02
            if curT<=UL and curT>=CL:
                break
        self.set_result(round(curT,1),'PASS')
        return self.result


class HardnessStep(DigiCenterStep):
    def __init__(self):
        super(HardnessStep,self).__init__()
        self.port = None
        self.method = None
        self.mode = None
        self.mearTime = None # sec

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.port = list(filter(lambda name: name['name'] == 'port', paras))[0]['value']
        self.method = list(filter(lambda name: name['name'] == 'method', paras))[0]['value']
        self.mode = list(filter(lambda name: name['name'] == 'mode', paras))[0]['value']
        self.mearTime = float(list(filter(lambda name: name['name'] == 'measuring time', paras))[0]['value'])

    @DigiCenterStep.deco
    def do(self):
        # do digiTest temperature control
        targetTime = self.mearTime
        countdownTime = 0
        startTime = time.time()
        # do time control
        while countdownTime<targetTime:
            if self.stopMsgQueue.qsize()>0:
                # stop process immediately
                break
            time.sleep(0.25)
            endTime = time.time()
            countdownTime = endTime - startTime
            dummpyHard = random.random()*10 + 50
            self.set_result(round(dummpyHard,1),'Waiting')
            self.resultCallback(self.result)
        self.set_result(round(dummpyHard,1),'PASS')
        return self.result


class WaitingStep(DigiCenterStep):
    def __init__(self):
        super(WaitingStep,self).__init__()
        self.condTime = 0 # min

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.condTime = float(list(filter(lambda name: name['name'] == 'conditioning time', paras))[0]['value'])

    @DigiCenterStep.deco
    def do(self):
        targetTime = self.condTime*60.0
        countdownTime = 0
        startTime = time.time()
        # do time control
        while countdownTime<targetTime:
            if self.stopMsgQueue.qsize()>0:
                # stop process immediately
                break
            time.sleep(1)
            endTime = time.time()
            countdownTime = endTime - startTime
            self.set_result(round(countdownTime,1),'Waiting')
            self.resultCallback(self.result)
        self.set_result(round(countdownTime,1),'PASS')
        return self.result


class ForLoopStartStep(DigiCenterStep):
    def __init__(self):
        super(ForLoopStartStep,self).__init__()
        self.loopCounts = 0
        self.containSteps = []
        self.loopid = 0

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.loopCounts = int(list(filter(lambda name: name['name'] == 'loop counts', paras))[0]['value'])
        self.loopid = list(filter(lambda name: name['name'] == 'loop id', paras))[0]['value']
    
    @DigiCenterStep.deco
    def do(self):
        for itr in range(self.loopCounts):
            print('Loop count {} in loop {}'.format(itr,self.loopid))
            self.set_result(itr,'Waiting')
            self.resultCallback(self.result)
            for stp in self.containSteps:
                stp.do()
            
        self.set_result(self.loopCounts,'PASS')
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
        self.loopIter = 0
        self.loopDone = False

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.loopCounts = int(list(filter(lambda name: name['name'] == 'stop on', paras))[0]['value'])
        self.loopid = list(filter(lambda name: name['name'] == 'loop id', paras))[0]['value']
    
    @DigiCenterStep.deco
    def do(self):
        self.loopIter += 1
        if self.loopIter >= self.loopCounts:
            self.loopDone = True
        self.set_result(self.loopIter,'PASS')
        return self.result
    
    def resetLoop(self):
        self.loopDone = False
        self.loopIter = 0

class SubProgramStep(DigiCenterStep):
    def __init__(self):
        super(SubProgramStep,self).__init__()
        self.prog_path = None

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.prog_path = list(filter(lambda name: name['name'] == 'path', paras))[0]['value']

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