from productlib import pd_product
import corelib.utility.utility as util
import os
import productlib.digiCenter.digiCenter_seq as seqClass

class DigiChamberProduct(pd_product.Product):
    def __init__(self, pd_name,seqPath=r"C:\\data_exports"):
        super(DigiChamberProduct, self).__init__(pd_name)
        self.script = None
        self.setDefaultSeqFolder(seqPath)
        self.stepsClass = []
        self.mainClass = []

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
        
        def findLoopPair(loopid,mainClass):
            for s in self.mainClass:
                if s.category == 'loop':
                    if s.itemname == 'loop start' and s.loopid == loopid:
                        loopStarIndex = s.stepid
                    elif s.itemname == 'loop end' and s.loopid == loopid:
                        loopEndIndex = s.stepid
                        return (loopStarIndex,loopEndIndex)

        # give loop the contain steps
        for s in self.mainClass:
            if s.category == 'loop':
                if s.itemname == 'loop start':
                    startIdx, endIdx = findLoopPair(s.loopid,self.mainClass)
                    curLoopSteps = self.mainClass[startIdx+1:endIdx]
                    internalLoop = list(filter(lambda x: x.category == 'loop', curLoopSteps))
                    isAnyLoopInside = len(internalLoop)>0
                    if isAnyLoopInside:
                        startIdx, endIdx = findLoopPair(internalLoop[0].loopid,self.mainClass)
                        actualLoop = []
                        for l in curLoopSteps:
                            l.insideLoop=True
                            self.mainClass[l.stepid].insideLoop=True
                            if l.stepid<=startIdx or l.stepid>endIdx:
                                actualLoop.append(l)
                        s.set_containedSteps(actualLoop)
                    else:
                        for l in curLoopSteps:
                            self.mainClass[l.stepid].insideLoop=True
                        s.set_containedSteps(self.mainClass[startIdx+1:endIdx])
                    
        
        # combine setup main teardown steps
        stepObj = seqClass.SetupStep()
        stepObj.set_paras(step=setup)
        self.stepsClass.append(stepObj)
        for m in self.mainClass:
            print(m.category)
            if not m.insideLoop:
                self.stepsClass.append(m)
            
        stepObj = seqClass.TeardownStep()
        stepObj.set_paras(step=teardown)
        self.stepsClass.append(stepObj)

    def run_seq(self):
        for s in self.stepsClass:
            s.do()