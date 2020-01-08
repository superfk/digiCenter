from productlib import pd_product
import corelib.utility.utility as util
import os
import productlib.digiCenter.digiCenter_seq as seqClass
import random
import asyncio
import types
import threading, queue
import time
import math

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
        self.batchInfo = None
        self.dChamb = None

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
    
    def setBatchInfo(self,batchInfo):
        self.batchInfo = batchInfo
    
    def create_seq(self):
        setup = self.script['setup']
        main = self.script['main']
        teardown = self.script['teardown']
        self.stepsClass = []
        self.mainClass = []
        for s in main:
            if s['cat']=='temperature':
                stepObj = seqClass.TemperatureStep()
            elif s['cat']=='hardness':
                stepObj = seqClass.HardnessStep()
            elif s['cat']=='waiting':
                stepObj = seqClass.WaitingStep()
            elif s['cat']=='loop':
                item = s['subitem']['item']
                if item == 'loop start':
                    stepObj = seqClass.ForLoopStartStep()
                elif item == 'loop end':
                    stepObj = seqClass.ForLoopEndStep()           
            elif s['cat']=='subprog':
                stepObj = seqClass.SubProgramStep()
            else:
                pass
            stepObj.set_paras(step=s)
            stepObj.set_digiChamber_hw_control(self.dChamb)                
            self.mainClass.append(stepObj)         
        
        # combine setup main teardown steps
        stepObj = seqClass.SetupStep()
        stepObj.set_paras(step=setup)
        stepObj.set_digiChamber_hw_control(self.dChamb)     
        self.stepsClass.append(stepObj)
        for m in self.mainClass:
            self.stepsClass.append(m)
        stepObj = seqClass.TeardownStep()
        stepObj.set_paras(step=teardown)
        stepObj.set_digiChamber_hw_control(self.dChamb)
        self.stepsClass.append(stepObj)

    async def run_seq(self,websocket):
        try:
            # preinit process
            self.stopMsgQueue = queue.Queue()
            self.testStop=False
            self.interruptStop=False
            self.create_result_callback_loop()
            self.ws = websocket
            self.errorMsg = None
            startTime = time.time()
            totalStepsCounts = len(self.stepsClass)
            cursor = 0
            
            for s in self.stepsClass:
                # set inital start time to calculate relative time
                s.set_initTime(startTime)
                s.set_result_callback(self.sendResultCallback)
                s.set_communicate_callback(self.sendCommunicateCallback)
                s.stopMsgQueue = self.stopMsgQueue

            # main process 
            while True:
                # check whether stop this loop
                if cursor >= totalStepsCounts or self.testStop:
                    break
                # continuous process
                print('current cursor: {}'.format(cursor))
                # get payload step
                step = self.stepsClass[cursor]

                curStepName = step.__class__.__name__

                if curStepName == 'HardnessStep':
                    # only for demo, MUST remove later
                    senCoeff = 5
                    step.dummyHardBase = 50 - senCoeff*math.log10(self.dChamb.get_real_temperature()/23)

                # do step
                testResult = step.do()

                # handle result
                if testResult['status'] in ['PASS','FAIL','SKIP']:
                    if curStepName != 'ForLoopEndStep':
                        cursor += 1
                    else:
                        if not step.loopDone:
                            # starting from loop start
                            startIdx, endIdx = self.findLoopPair(step.loopid, self.stepsClass)
                            cursor = startIdx
                        else:
                            '''reset loop because if another loop run this loop again 
                            that not lead to immediately stop'''
                            startIdx, endIdx = self.findLoopPair(step.loopid, self.stepsClass)
                            for s in range(startIdx,endIdx+1):
                                self.stepsClass[s].reset_loopiter()
                            step.resetLoop()
                            cursor += 1

                # check if finish final step
                if cursor >= totalStepsCounts:
                    self.testStop=True

        except Exception as e:
            print(e)
            self.errorMsg = '{}'.format(e)
            self.interruptStop = True

        finally:
            if self.interruptStop:
                item = self.stopMsgQueue.get()
                self.stopMsgQueue.task_done()
                print('reached end_of_test, interrupted')
                if self.errorMsg:
                    self.sendCommunicateCallback('end_of_test',{'interrupted':True,'reason':self.errorMsg})
                else:
                    self.sendCommunicateCallback('end_of_test',{'interrupted':True,'reason':'Manually stop'})
            else:
                print('reached end_of_test, all done')
                self.sendCommunicateCallback('end_of_test',{'interrupted':False,'reason':'tests all done'})

    async def get_cur_temp_and_humi(self, websocket):
        try:
            self.curT = self.dChamb.get_real_temperature()
            status = {'temp':self.curT, 'hum':random.random()*1 + self.curH}
            await self.socketCallback(websocket,'update_cur_status',status)
        except:
            print('digiChamber get temperature error')

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
    
    def sendCommunicateCallback(self,cmd, data):
        future = asyncio.run_coroutine_threadsafe(self.socketCallback(self.ws,cmd,data), self.loop)
    
    def set_test_stop(self):
        self.testStop=True
        self.interruptStop=True
        self.stopMsgQueue.put(True)
    
    def init_digiChamber_controller(self,obj_digiChmaber):
        try:
            self.dChamb = obj_digiChmaber
            conn = self.dChamb.connect()
            return conn
        except:
            print('digichamber connection failed')
            return False

    def close_digiChamber_controller(self):
        try:
            self.dChamb.close()
        except:
            pass
    