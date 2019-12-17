
from datetime import datetime
import time
import threading

dummy_delay = 0.1

class DigiCenterStep(object):
    def __init__(self):
        self.category = ''
        self.itemname = ''
        self.stepid = None
        self.contained_steps = []
        self.paras = []
        self.result = [{'name':None, 'value': None}]
        self.enabled = True
        self.startTime = None
        self.endTime = None
        self.insideLoop = False

    def set_paras(self,step):
        self.stepid = step['id']
        self.category = step['cat']
        self.itemname = step['subitem']['item']
        self.enabled = step['subitem']['enabled']
    
    def do(self,step2run=None, async=False):
        print('cat: {}, itemname: {}, id: {}'.format(self.category,self.itemname,self.stepid))
        self.set_startTime()
        self.set_endTime()
        if async:
            thred = threading.Thread(target=step2run)
            thred.start()
        else:
            step2run()
            self.set_endTime()
            self.get_test_interval()
        
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


class SetupStep(DigiCenterStep):
    def __init__(self):
        super(SetupStep,self).__init__()
    
    def set_paras(self,step):
        super().set_paras(step)
    
    def do(self):
        def do_core():
            # do setup control
            time.sleep(dummy_delay)
        super().do(do_core)
        return self.result


class TeardownStep(DigiCenterStep):
    def __init__(self):
        super(TeardownStep,self).__init__()

    def set_paras(self,step):
        super().set_paras(step)

    def do(self):
        def do_core():
            # do teardown control
            time.sleep(dummy_delay)
        super().do(do_core)
        return self.result

class TemperatureStep(DigiCenterStep):
    def __init__(self):
        super(TemperatureStep,self).__init__()
        self.targetTemp = 0
        self.slope = 0

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.targetTemp = list(filter(lambda name: name['name'] == 'target temperature', paras))[0]['value']
        self.slope = list(filter(lambda name: name['name'] == 'slope', paras))[0]['value']

    def do(self):
        def do_core():
            # do digichamber temperature control
            time.sleep(dummy_delay)
        super().do(do_core)
        return self.result


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
        self.mearTime = list(filter(lambda name: name['name'] == 'measuring time', paras))[0]['value']

    def do(self):
        def do_core():
            # do digiTest temperature control
            time.sleep(dummy_delay)
        
        super().do(do_core)
        return self.result


class WaitingStep(DigiCenterStep):
    def __init__(self):
        super(WaitingStep,self).__init__()
        self.condTime = 0

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.condTime = list(filter(lambda name: name['name'] == 'conditioning time', paras))[0]['value']

    def do(self):
        def do_core():
            # do time control
            time.sleep(dummy_delay)
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
        super().do(do_core)
        return self.result
    
    def set_containedSteps(self, containSteps):
        self.containSteps = containSteps

class ForLoopEndStep(DigiCenterStep):
    def __init__(self):
        super(ForLoopEndStep,self).__init__()
        self.loopid = 0

    def set_paras(self,step):
        super().set_paras(step)
        paras = step['subitem']['paras']
        self.loopid = list(filter(lambda name: name['name'] == 'loop id', paras))[0]['value']
    
    def do(self):
        def do_core():
           pass
        super().do(do_core)
        return self.result

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
        super().do(do_core)
        return self.result



def main():
    pass


if __name__ == '__main__':
    main()