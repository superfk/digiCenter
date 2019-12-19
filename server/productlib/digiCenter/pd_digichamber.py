from productlib import pd_product
import corelib.utility.utility as util
import os
import productlib.digiCenter.digiCenter_seq as seqClass
import random

class DigiChamberProduct(pd_product.Product):
    def __init__(self, pd_name,seqPath=r"C:\\data_exports"):
        super(DigiChamberProduct, self).__init__(pd_name)
        self.script = None
        self.setDefaultSeqFolder(seqPath)
        self.stepsClass = []
        self.mainClass = []
        self.dummyT = 23
        self.dummyH = 50

    def run_script(self, scriptName, data=None):
        if scriptName=='ini_seq':
            return self.init_seq(data)
        elif scriptName=='save_seq':
            return self.save_seq(path=data['path'],seq_json=data['seq'])
        elif scriptName=='load_seq':
            return self.load_seq(data['path'])
        elif scriptName=='run_seq':
            self.create_seq()
            return self.run_seq()
        elif scriptName=='get_default_seq_path':
            return self.default_seq_folder
        elif scriptName=='get_cur_temp_and_humi':
            return self.get_cur_temp_and_humi()
        else:
            print('No this case: {}'.format(scriptName))
        return 0

    def init_seq(self,data):
        self.script=None
        return data

    def save_seq(self,path,seq_json):
        newPath = os.path.join(self.default_seq_folder,path)
        util.write2JSON(newPath, seq_json)
        return 'file saved to: {}'.format(newPath)

    def load_seq(self,path):
        data = util.readFromJSON(path)
        self.script=data
        return data
    
    def setDefaultSeqFolder(self,seqPath):
        path = os.path.join(seqPath,'seq_files')
        self.default_seq_folder = path
        util.newPathIfNotExist(self.default_seq_folder)
    
    def create_seq(self):
        setup = self.script['setup']
        main = self.script['main']
        teardown = self.script['teardown']
        self.stepsClass = []
        self.mainClass = []
        for s in main:
            if s['cat']=='temperature':
                stepObj = seqClass.TemperatureStep()
                stepObj.set_paras(step=s)
                self.mainClass.append(stepObj)
            elif s['cat']=='hardness':
                stepObj = seqClass.HardnessStep()
                stepObj.set_paras(step=s)
                self.mainClass.append(stepObj)
            elif s['cat']=='waiting':
                stepObj = seqClass.WaitingStep()
                stepObj.set_paras(step=s)
                self.mainClass.append(stepObj)
            elif s['cat']=='loop':
                item = s['subitem']['item']
                if item == 'loop start':
                    stepObj = seqClass.ForLoopStartStep()
                    stepObj.set_paras(step=s)
                    self.mainClass.append(stepObj)
                elif item == 'loop end':
                    stepObj = seqClass.ForLoopEndStep()
                    stepObj.set_paras(step=s)
                    self.mainClass.append(stepObj)              
            elif s['cat']=='subprog':
                stepObj = seqClass.SubProgramStep()
                stepObj.set_paras(step=s)
                self.mainClass.append(stepObj)
            else:
                pass               
        
        # combine setup main teardown steps
        stepObj = seqClass.SetupStep()
        stepObj.set_paras(step=setup)
        self.stepsClass.append(stepObj)
        for m in self.mainClass:
            self.stepsClass.append(m)
        stepObj = seqClass.TeardownStep()
        stepObj.set_paras(step=teardown)
        self.stepsClass.append(stepObj)

    def run_seq(self):
        totalStepsCounts = len(self.stepsClass)
        cursor = 0
        while cursor < totalStepsCounts:
            step = self.stepsClass[cursor]
            yield cursor
            if step.category == 'loop' and step.itemname == 'loop end':
                testResult = next(step.do())
                yield testResult
                if not step.loopDone:
                    # starting after loop start
                    startIdx, endIdx = self.findLoopPair(step.loopid, self.stepsClass)
                    cursor = startIdx + 1
                else:
                    '''reset loop because if another loop run this loop again 
                    that not lead to immediately stop''' 
                    step.resetLoop()
                    cursor += 1
            else:
                testResult = next(step.do())
                yield testResult
                if testResult['status'] in ['PASS','FAIL']:
                    cursor += 1
                
                
    def get_cur_temp_and_humi(self):
        return {'temp':random.random()*0.2 + self.dummyT, 'hum':random.random()*1 + self.dummyH}

    def findLoopPair(self, loopid, mainClass):
        for i,s in enumerate(mainClass):
            if s.category == 'loop':
                if s.itemname == 'loop start' and s.loopid == loopid:
                    loopStarIndex = i
                elif s.itemname == 'loop end' and s.loopid == loopid:
                    loopEndIndex = i
                    return (loopStarIndex,loopEndIndex)