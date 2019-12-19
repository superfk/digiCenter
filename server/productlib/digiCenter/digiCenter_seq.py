
from datetime import datetime
import time
import threading
import random

dummy_delay = 0.1

class DigiCenterStep(object):
    def __init__(self):
        self.category = ''
        self.itemname = ''
        self.stepid = None
        self.contained_steps = []
        self.paras = []
        self.result = {'stepid':0,'name':None, 'value': None, 'status': 'FAIL'}
        self.enabled = True
        self.startTime = None
        self.endTime = None
        self.insideLoop = False

    def set_paras(self,step):
        self.stepid = step['id']
        self.category = step['cat']
        self.itemname = step['subitem']['item']
        self.enabled = step['subitem']['enabled']
    
    def do(self,step2run=None, asyn=False):
        print('cat: {}, itemname: {}, id: {}'.format(self.category,self.itemname,self.stepid))
        self.set_startTime()
        self.set_endTime()
        if asyn:
            thred = threading.Thread(target=step2run)
            thred.start()
        else:
            step2run()
            self.set_endTime()
            self.get_test_interval()
        yield self.result

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


class SetupStep(DigiCenterStep):
    def __init__(self):
        super(SetupStep,self).__init__()
    
    def set_paras(self,step):
        super().set_paras(step)
    
    def do(self):
        def do_core():
            # do setup control
            time.sleep(dummy_delay)
            yield self.set_result('PASS','PASS')
        yield from super().do(do_core)


class TeardownStep(DigiCenterStep):
    def __init__(self):
        super(TeardownStep,self).__init__()

    def set_paras(self,step):
        super().set_paras(step)

    def do(self):
        def do_core():
            # do teardown control
            time.sleep(dummy_delay)
            yield self.set_result('PASS','PASS')
        yield from super().do(do_core)

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

    def do(self):
        def do_core():
            # do digichamber temperature control
            curT = random.random()*0.5 + 23
            tol = 0.5
            UL = self.targetTemp+tol
            CL = self.targetTemp-tol
            while curT>UL or curT<CL:
                time.sleep(1)
                yield self.set_result(curT, 'Waiting')
                if (self.targetTemp-curT)<0:
                    signSlope = -self.slope
                else:
                    signSlope = self.slope
                curT = curT + signSlope/60*1 + random.random()*0.2
            yield self.set_result(curT, 'PASS')
        yield from super().do(do_core)


class HardnessStep(DigiCenterStep):
    def __init__(self):
        super(HardnessStep,self).__init__()
        self.port = None
        self.method = None
        self.mode = None
        self.mearTime = None

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.port = list(filter(lambda name: name['name'] == 'port', paras))[0]['value']
        self.method = list(filter(lambda name: name['name'] == 'method', paras))[0]['value']
        self.mode = list(filter(lambda name: name['name'] == 'mode', paras))[0]['value']
        self.mearTime = float(list(filter(lambda name: name['name'] == 'measuring time', paras))[0]['value'])

    def do(self):
        def do_core():
            # do digiTest temperature control
            time.sleep(self.mearTime)
            dummpyHard = random.random()*10 + 50
            self.set_result(dummpyHard,'PASS')
        super().do(do_core)
        return self.result


class WaitingStep(DigiCenterStep):
    def __init__(self):
        super(WaitingStep,self).__init__()
        self.condTime = 0 # min

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.condTime = float(list(filter(lambda name: name['name'] == 'conditioning time', paras))[0]['value'])

    def do(self):
        def do_core():
            # do time control
            time.sleep(self.condTime/60)
            self.set_result(0,'PASS')
        super().do(do_core)
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
    
    def do(self):
        def do_core(counts = self.loopCounts, steps = self.containSteps):
            # do loop control
            for itr in range(counts):
                print('Loop count {} in loop {}'.format(itr,self.loopid))
                for stp in steps:
                    stp.do()
            self.set_result(0,'PASS')
        super().do(do_core)
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
    
    def do(self):
        def do_core():
            self.loopIter += 1
            if self.loopIter >= self.loopCounts:
                self.loopDone = True
            self.set_result(0,'PASS')
        super().do(do_core)
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

    def do(self):
        def do_core():
            # do sub program control
            time.sleep(dummy_delay)
            self.set_result(0,'PASS')
        super().do(do_core)
        return self.result



def main():
    pass


if __name__ == '__main__':
    main()