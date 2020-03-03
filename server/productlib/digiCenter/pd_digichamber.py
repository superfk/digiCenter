from productlib import pd_product
import corelib.utility.utility as util
import os, sys
import productlib.digiCenter.digiCenter_seq as seqClass
import random
import asyncio
import types
import threading, queue
import time, datetime
import math
from loguru import logger

class DigiChamberProduct(pd_product.Product):
    def __init__(self, pd_name,seqPath=r"C:\\data_exports",msg_callback=None, dbResult_callback=None, model='fix'):
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
        self.digiTest = None
        self.retry = False
        self.saveTestResult2DbCallback = dbResult_callback
        self.chamberModel = model
        self.lang_data = None
        self.lg = None
        self.log_to_db_func = None
        self.in_test_mode = False

    def set_lang(self, lang_data):
        self.lang_data = lang_data
    
    def set_logger(self, loggerObj):
        self.lg = loggerObj
    
    def set_log_to_db_func(self, logDBFunc):
        self.log_to_db_func = logDBFunc
        
    async def run_script(self,websocket, scriptName, data=None):
        if scriptName=='ini_seq':
            await self.init_seq()
        elif scriptName=='save_seq':
            await self.save_seq(websocket,path=data['path'],seq_json=data['seq'], force_save=data['force_save'])
        elif scriptName=='load_seq':
            await self.load_seq(websocket,data['path'])
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

    async def save_seq(self,websocket, path, seq_json, force_save=False):
        newPath = os.path.join(self.default_seq_folder,path)
        # check if newpth overwrite oldpath
        hasOldPath = os.path.exists(newPath)
        if hasOldPath:
            olddata = util.readFromJSON(newPath)
            same, reason = util.compareTwoJson(olddata, seq_json)
            if same:
                reason = '{} file saved'.format(newPath)
                self.log_to_db_func(reason, 'info', True)
                util.write2JSON(newPath, seq_json)
                self.script = seq_json
                return self.script
            elif force_save:
                reason = '{} file saved, {}'.format(newPath, reason)
                self.log_to_db_func(reason, 'info', True)
                util.write2JSON(newPath, seq_json)
                self.script = seq_json
                return self.script
            else:
                title = self.lang_data['seqEditor_inform_seq_differ_title']
                txt = self.lang_data['seqEditor_inform_seq_differ_txt'] + '\n' + reason
                await self.socketCallback(websocket, 'inform_user_seq_differ', {'title':title,'reason':txt})
        else:
            reason = '{} file saved'.format(newPath)
            self.log_to_db_func(reason, 'info', True)
            util.write2JSON(newPath, seq_json)
            self.script = seq_json
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
            stepObj.set_digitest_hw_control(self.digiTest)              
            self.mainClass.append(stepObj)         
        
        # combine setup main teardown steps
        stepObj = seqClass.SetupStep()
        stepObj.set_paras(step=setup)
        stepObj.set_digiChamber_hw_control(self.dChamb)
        stepObj.set_digitest_hw_control(self.digiTest) 
        self.stepsClass.append(stepObj)
        for m in self.mainClass:
            self.stepsClass.append(m)
        stepObj = seqClass.TeardownStep()
        stepObj.set_paras(step=teardown)
        stepObj.set_digiChamber_hw_control(self.dChamb)
        stepObj.set_digitest_hw_control(self.digiTest)
        self.stepsClass.append(stepObj)
        self.lg.debug('created steps class')
        self.lg.debug(self.stepsClass)

    async def run_seq(self,websocket):
        try:
            # preinit process
            self.in_test_mode = True
            self.stopMsgQueue = queue.Queue()
            self.testStop=False
            self.interruptStop=False
            self.create_result_callback_loop()
            self.ws = websocket
            self.errorMsg = None
            self.pause = False
            self.retry = False
            startTime = time.time()
            totalStepsCounts = len(self.stepsClass)
            cursor = 0
            
            for s in self.stepsClass:
                # set inital start time to calculate relative time
                s.set_initTime(startTime)
                s.set_result_callback(self.sendResultCallback)
                s.set_communicate_callback(self.sendCommunicateCallback)
                s.stopMsgQueue = self.stopMsgQueue
                s.set_batchinfo(self.batchInfo)

            # main process 
            while True:
                # check whether stop this loop
                if cursor >= totalStepsCounts or self.testStop:
                    break
                if self.pause:
                    # if this process pause, ignore remain procedure and go back to beginning of while loop
                    time.sleep(0.2)
                    continue
                # continuous process
                self.lg.debug('current cursor: {}'.format(cursor))
                # get payload step
                step = self.stepsClass[cursor]

                curStepName = step.__class__.__name__
                self.lg.debug('current step name: {}'.format(curStepName))

                if curStepName == 'HardnessStep':
                    step.retry = self.retry
                    self.retry = False
                    # only for demo, MUST remove later
                    senCoeff = 5
                    step.dummyHardBase = 50 - senCoeff*math.log10(self.dChamb.get_real_temperature()/23)

                # do step
                testResult = step.do()
                self.lg.debug('output of testResult: {}'.format(testResult))

                # handle result
                if testResult['status'] in ['PASS','FAIL','SKIP','MEAR_NEXT']:
                    if curStepName != 'ForLoopEndStep':
                        if curStepName == 'HardnessStep' and testResult['status'] == 'PASS':
                            self.saveResult2DatabaseCallback(testResult)
                            cursor += 1
                        elif curStepName == 'HardnessStep' and testResult['status'] == 'MEAR_NEXT':
                            self.saveResult2DatabaseCallback(testResult)
                        else:
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
                elif testResult['status'] in ['PAUSE']:
                    self.pause = True

                # check if finish final step
                if cursor >= totalStepsCounts:
                    self.testStop=True

        except Exception as e:
            self.lg.debug('error during excetipn handling in test sequence prcess')
            self.lg.debug(e)
            self.errorMsg = '{}'.format(e)
            self.interruptStop = True

        finally:
            if self.interruptStop:
                item = self.stopMsgQueue.get()
                self.stopMsgQueue.task_done()
                self.lg.debug('reached end_of_test, interrupted')
                if self.errorMsg:
                    txt = self.lang_data['server_manual_end_test_reason'] + self.errorMsg
                    title = self.lang_data['server_manual_end_test_title']
                    self.sendCommunicateCallback('end_of_test',{'interrupted':True,'title':title,'reason':txt})
                    self.errorMsg = None
                else:
                    txt = self.lang_data['server_manual_end_test_reason']
                    title = self.lang_data['server_manual_end_test_title']
                    self.sendCommunicateCallback('end_of_test',{'interrupted':True,'title':title,'reason':txt})
            else:
                self.lg.debug('reached end_of_test, all done')
                txt = self.lang_data['server_final_end_test_reason']
                title = self.lang_data['server_final_end_test_title']
                self.sendCommunicateCallback('end_of_test',{'interrupted':False,'title':title,'reason':txt})
            
            try:
                self.dChamb.set_manual_mode(False)
                self.digiTest.stop_mear()
                self.digiTest.set_remote(False)
            except:
                self.lg.debug('set hardware failed in the finall step of sequence')

            self.in_test_mode = False

    async def get_cur_temp_and_humi(self, websocket):
        dtInfo = {}
        dtInfo['status']=False
        dtInfo['value']=None
        tempInfo = {}
        tempInfo['status']=False
        tempInfo['value']=None
        humInfo = {}
        humInfo['status']=False
        humInfo['value']=None
        if not self.in_test_mode:
            try:
                dtInfo['status']=self.digiTest.connected
                if self.digiTest.connected:
                    dtInfo['value']=self.digiTest.get_single_value()
                else:
                    dtInfo['value']= None
            except Exception as e:
                self.lg.debug('digitest get value error')
                self.lg.debug(e)
            try:
                if self.dChamb.connected:
                    self.curT = self.dChamb.get_real_temperature()
                    self.curH = self.dChamb.get_real_humidity()
                    tempInfo['status']=self.dChamb.connected
                    tempInfo['value']=self.curT
                    humInfo['status']=self.dChamb.connected
                    humInfo['value']=self.curH
                else:
                    tempInfo['status']=False
                    tempInfo['value']=None
                    humInfo['status']=False
                    humInfo['value']=None 
            except Exception as e:
                self.lg.debug('digiChamber get temperature error')
                self.lg.debug(e)
            finally:
                status = {'dt':dtInfo,'temp':tempInfo, 'hum':humInfo}
                await self.socketCallback(websocket,'update_cur_status',status)
                # print('###################')
                # print(status)

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
    
    def saveResult2DatabaseCallback(self,testResult):
        future = asyncio.run_coroutine_threadsafe(self.saveTestResult2DbCallback(testResult), self.loop)
        
    def continuous_mear(self,retry=False):
        self.pause = False
        self.retry = retry
    
    def set_test_stop(self):
        self.testStop=True
        self.interruptStop=True
        self.stopMsgQueue.put(True)
    
    def init_digiChamber_controller(self,obj_digiChmaber):
        try:
            self.dChamb = obj_digiChmaber
            conn = self.dChamb.connect()
            return conn
        except Exception as e:
            self.lg.debug('digiChamber init error: {}'.format(e))
            return False

    def close_digiChamber_controller(self):
        self.dChamb.close()
    
    def init_digitest_controller(self,obj_digitest, COM='COM3'):
        try:
            self.digiTest = obj_digitest
            conn = self.digiTest.open_rs232(COM, timeout=5)
            return conn
        except Exception as e:
            self.lg.debug('digitest init error: {}'.format(e))
            return False

    def close_digitest_controller(self):
        self.digiTest.set_remote(False)
        self.digiTest.close_rs232()

