from productlib import pd_product
import corelib.utility.utility as util
import os
import productlib.digiCenter.digiCenter_seq as seqClass
import random
import asyncio
import types
import threading, queue

class DigiChamberProduct(pd_product.Product):
    def __init__(self, pd_name,seqPath=r"C:\\data_exports",msg_callback=None):
        super(DigiChamberProduct, self).__init__(pd_name)
        self.script = None
        self.setDefaultSeqFolder(seqPath)
        self.stepsClass = []
        self.mainClass = []
        self.dummyT_init = 23
        self.dummyT_decRate = 0.1
        self.curT = 23
        self.dummyH_init = 50
        self.curH = 50
        self.socketCallback = msg_callback
        self.loop = None
        self.ws = None
        self.testStop = False
        self.interruptStop = False

    async def run_script(self,websocket, scriptName, data=None):
        if scriptName=='ini_seq':
            await self.init_seq()
        elif scriptName=='save_seq':
            await self.save_seq(websocket,path=data['path'],seq_json=data['seq'])
        elif scriptName=='load_seq':
            await self.load_seq(websocket,data['path'])
        elif scriptName=='run_seq':
            await self.create_seq()
            await self.run_seq(websocket)
        elif scriptName=='get_default_seq_path':
            await self.socketCallback(websocket, 'update_sys_default_config', self.default_seq_folder)
        elif scriptName=='get_cur_temp_and_humi':
            await self.get_cur_temp_and_humi(websocket)
        else:
            print('No this case: {}'.format(scriptName))
        return 0

    async def init_seq(self):
        self.script=None
        return self.script

    async def save_seq(self,websocket, path,seq_json):
        newPath = os.path.join(self.default_seq_folder,path)
        util.write2JSON(newPath, seq_json)
        return self.script

    async def load_seq(self,websocket, path):
        data = util.readFromJSON(path)
        self.script=data
        await self.socketCallback(websocket, 'update_sequence', self.script)
    
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
                stepObj.set_sockect_callback(self.socketCallback)
                self.mainClass.append(stepObj)
            elif s['cat']=='hardness':
                stepObj = seqClass.HardnessStep()
                stepObj.set_paras(step=s)
                stepObj.set_sockect_callback(self.socketCallback)
                self.mainClass.append(stepObj)
            elif s['cat']=='waiting':
                stepObj = seqClass.WaitingStep()
                stepObj.set_paras(step=s)
                stepObj.set_sockect_callback(self.socketCallback)
                self.mainClass.append(stepObj)
            elif s['cat']=='loop':
                item = s['subitem']['item']
                if item == 'loop start':
                    stepObj = seqClass.ForLoopStartStep()
                    stepObj.set_paras(step=s)
                    stepObj.set_sockect_callback(self.socketCallback)
                    self.mainClass.append(stepObj)
                elif item == 'loop end':
                    stepObj = seqClass.ForLoopEndStep()
                    stepObj.set_paras(step=s)
                    stepObj.set_sockect_callback(self.socketCallback)
                    self.mainClass.append(stepObj)              
            elif s['cat']=='subprog':
                stepObj = seqClass.SubProgramStep()
                stepObj.set_paras(step=s)
                stepObj.set_sockect_callback(self.socketCallback)
                self.mainClass.append(stepObj)
            else:
                pass               
        
        # combine setup main teardown steps
        stepObj = seqClass.SetupStep()
        stepObj.set_paras(step=setup)
        stepObj.set_sockect_callback(self.socketCallback)
        self.stepsClass.append(stepObj)
        for m in self.mainClass:
            self.stepsClass.append(m)
        stepObj = seqClass.TeardownStep()
        stepObj.set_paras(step=teardown)
        stepObj.set_sockect_callback(self.socketCallback)
        self.stepsClass.append(stepObj)

    async def run_seq(self,websocket):
        self.stopMsgQueue = queue.Queue()
        self.testStop=False
        self.interruptStop=False
        self.create_result_callback_loop()
        self.ws = websocket
        totalStepsCounts = len(self.stepsClass)
        print(totalStepsCounts)
        cursor = 0
        while cursor < totalStepsCounts and not self.testStop:
            print('current cursor: {}'.format(cursor))
            step = self.stepsClass[cursor]
            step.set_result_callback(self.sendResultCallback)
            step.stopMsgQueue = self.stopMsgQueue
            await self.socketCallback(websocket,'update_cursor',cursor) 
            if step.category == 'loop' and step.itemname == 'loop end':
                testResult = step.do()
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
                testResult = step.do()
                if testResult['status'] in ['PASS','FAIL']:
                    cursor += 1
            if cursor >= totalStepsCounts:
                self.testStop=True
        try:
            if self.interruptStop:
                item = self.stopMsgQueue.get()
                self.stopMsgQueue.task_done()
                print('reached end_of_test, interrupted')
                await self.socketCallback(websocket,'end_of_test','test interrupted')
            else:
                print('reached end_of_test, all done')
                await self.socketCallback(websocket,'end_of_test','test all done') 
            self.loop.stop()
            
        except Exception as e:
            print(e)             

    async def get_cur_temp_and_humi(self, websocket):
        status = {'temp':random.random()*0.2 + self.curT, 'hum':random.random()*1 + self.curH}
        await self.socketCallback(websocket,'update_cur_status',status)

    def findLoopPair(self, loopid, mainClass):
        for i,s in enumerate(mainClass):
            if s.category == 'loop':
                if s.itemname == 'loop start' and s.loopid == loopid:
                    loopStarIndex = i
                elif s.itemname == 'loop end' and s.loopid == loopid:
                    loopEndIndex = i
                    return (loopStarIndex,loopEndIndex)
    
    def create_result_callback_loop(self):
        self.loop = asyncio.new_event_loop()
        def f(loop):
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        t = threading.Thread(target=f, args=(self.loop,))
        t.start()

    def sendResultCallback(self,result):
        future = asyncio.run_coroutine_threadsafe(self.socketCallback(self.ws,'update_step_result',result), self.loop)
    
    def set_test_stop(self):
        self.testStop=True
        self.interruptStop=True
        self.stopMsgQueue.put(True)

    