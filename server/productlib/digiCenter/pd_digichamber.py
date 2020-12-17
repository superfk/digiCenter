import traceback
from productlib import pd_product
import corelib.utility.utility as util
import os, sys
import productlib.digiCenter.digiCenter_seq as seqClass
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading, queue
import time, datetime
import math,random
from loguru import logger
import traceback

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
        self.parentLoop = None
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
        self.force_manual_mode = False
        self.sysConfig = None
        self.stopMsgQueue = None
        self.interuptQueue = None
        self.digiChamberError = False
        self.digiTestError = False
    
    def set_sysConfig(self, sysConfig):
        self.sysConfig = sysConfig

    def set_lang(self, lang_data):
        self.lang_data = lang_data
    
    def set_logger(self, loggerObj):
        self.lg = loggerObj
    
    def set_parentLoop(self, loop):
        self.parentLoop = loop
    
    def set_testLoop(self, loop):
        self.loop = loop
    
    def set_log_to_db_func(self, logDBFunc):
        self.log_to_db_func = logDBFunc
    
    def set_force_manual_mode(self, forceManual):
        self.force_manual_mode = forceManual
        
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
        elif scriptName=='moveTableLast':
            await self.moveTableLast()
        elif scriptName=='moveTableHome':
            await self.moveTableHome()
        elif scriptName=='moveTableNext':
            await self.moveTableNext()
        elif scriptName=='goToIndex':
            await self.moveTableToIndex(data)
        else:
            self.log_to_db_func('No this case: {}'.format(scriptName), 'error', False)

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
        try:
            self.script = None
            data = util.readFromJSON(path)
            self.script = data
            await self.socketCallback(websocket, 'reply_load_seq', {'error':None, 'script': self.script})
        except FileNotFoundError:
            await self.socketCallback(websocket, 'reply_load_seq', {'error':self.lang_data['server_reply_batch_seq_not_found'], 'script': self.script})
    
    def setDefaultSeqFolder(self,seqPath):
        path = os.path.join(seqPath,'seq_files')
        self.default_seq_folder = path
        util.newPathIfNotExist(self.default_seq_folder)
    
    def setBatchInfo(self,batchInfo):
        self.batchInfo = batchInfo
    
    def create_seq(self):
        if self.script:
            setup = self.script['setup']
            main = self.script['main']
            teardown = self.script['teardown']
            self.stepsClass = []
            self.mainClass = []
            for s in main:
                stepObj = None
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
                if stepObj:
                    stepObj.set_paras(step=s)
                    stepObj.set_digiChamber_hw_control(self.dChamb)
                    stepObj.set_digitest_hw_control(self.digiTest)     
                    stepObj.set_digitest_force_manual_mode(self.force_manual_mode)         
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
            # self.lg.debug(self.stepsClass)
            return True
        else:
            return False

    def run_seq(self,websocket, batchInfoForSamples):
        '''
            0:
                batchInfo:
                    batch: "batch0716"
                    notes: ""
                    numSample: 5
                    project: "test0716"
                    sampleId: 1
                    seq_name: "C:\data_exports\seq_files\demoSeq.seq"
                color: "red"
                id: 0
                status: "filled"
        '''
        try:
            # preinit process
            self.in_test_mode = True
            self.testStop=False
            self.interruptStop=False
            self.ws = websocket
            self.errorMsg = None
            self.stopMsgQueue = queue.Queue()
            self.interuptQueue = queue.Queue()
            self.pauseQueue = queue.Queue()
            startTime = time.time()
            totalStepsCounts = len(self.stepsClass)
            cursor = 0
            self.log_to_db_func('totalStepsCounts: {}'.format(totalStepsCounts), 'info', False)

            # check script existed
            if self.script:
                for s in self.stepsClass:
                    # set inital start time to calculate relative time
                    s.set_initTime(startTime)
                    s.set_result_callback(self.sendResultCallback)
                    s.set_communicate_callback(self.sendCommunicateCallback)
                    s.stopMsgQueue = self.stopMsgQueue
                    s.interuptQueue = self.interuptQueue
                    s.pauseQueue = self.pauseQueue
                    s.set_batchinfo(self.batchInfo)
                    s.set_batchInfoForSamples(batchInfoForSamples)
                    s.set_sysConfig(self.sysConfig)
                    s.lg = self.lg
                    s.set_error_occurred(False)

                # main process 
                while True:
                    # check hw connection
                    if not self.dChamb.connected or not self.digiTest.connected:
                        pass
                        # self.set_test_stop()
                        # if not self.digiTest.connected:
                        #     self.errorMsg = self.lang_data['digitest_disconnect_msg']
                        #     self.log_to_db_func('digitest_disconnected', 'error', False)
                        # else:
                        #     self.errorMsg = self.lang_data['digichamber_disconnect_msg']
                        #     self.log_to_db_func('digichamber_disconnected', 'error', False)
                        # break
                    # check whether stop this loop
                    if cursor >= totalStepsCounts or self.testStop:
                        break
                    # continuous process
                    # self.log_to_db_func('current cursor: {}'.format(cursor), 'info', False)
                    # get payload step
                    step = self.stepsClass[cursor]

                    curStepName = step.__class__.__name__
                    self.log_to_db_func('current step name: {}'.format(curStepName), 'info', False)                    

                    # do step
                    testResult = step.do()
                    # testResult = await step.do()
                    # self.log_to_db_func('output of testResult: {}'.format(testResult), 'info', True)
                    self.lg.debug('output of testResult: {}'.format(testResult),)

                    # handle result
                    if testResult['status'] in ['PASS','FAIL','SKIP','MEAR_NEXT']:
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
                    elif testResult['status'] in ['ERROR_STOP']:
                        # set cursor to teardown step
                        cursor = totalStepsCounts-1
                        # set errormsg
                        if testResult['eventName'] == 'distance_too_big':
                            self.errorMsg = self.lang_data['digitest_distance_too_big']
                        elif testResult['eventName'] == 'move_fail':
                            self.errorMsg = self.lang_data['rotation_table_move_fail']
                        elif testResult['eventName'] == 'digiChamber_connection_error':
                            self.errorMsg = self.lang_data['digichamber_disconnect_msg']
                        elif testResult['eventName'] == 'digitest_connection_error':
                            self.errorMsg = self.lang_data['digitest_disconnect_msg']
                        else:
                            pass
                        # set error attribute to every step
                        for s in self.stepsClass:
                            s.set_error_occurred(True, self.errorMsg)

                    # check if finish final step
                    if cursor >= totalStepsCounts:
                        self.set_normal_test_stop()
            else:
                # script not exsisted
                self.set_test_stop()
                self.errorMsg = self.lang_data['script_not_existed']

        except Exception as e:
            self.errorMsg = traceback.format_exc()
            self.set_test_stop()

        finally:
            try:
                self.interuptQueue.task_done()
            except:
                pass
            if self.interruptStop:
                self.stopMsgQueue.get()
                self.stopMsgQueue.task_done()
                self.lg.debug('reached end_of_test, interrupted')
                if self.errorMsg:
                    self.log_to_db_func('error during test: {}'.format(self.errorMsg), 'error', True)
                    txt = self.lang_data['server_error_end_test_reason'] + ' ' + self.errorMsg
                    title = self.lang_data['server_error_end_test_title']
                    self.sendCommunicateCallback('end_of_test',{'interrupted':True,'title':title,'reason':txt})
                    self.errorMsg = None
                else:
                    self.log_to_db_func('manual stop the test', 'info', False)
                    txt = self.lang_data['server_manual_end_test_reason']
                    title = self.lang_data['server_manual_end_test_title']
                    self.sendCommunicateCallback('end_of_test',{'interrupted':True,'title':title,'reason':txt})
            else:
                self.log_to_db_func('reached end_of_test, all done', 'info', False)
                txt = self.lang_data['server_final_end_test_reason']
                title = self.lang_data['server_final_end_test_title']
                self.sendCommunicateCallback('end_of_test',{'interrupted':False,'title':title,'reason':txt})
            
            try:
                self.dChamb.set_manual_mode(False)
                self.sendCommunicateCallback('update_machine_status',{'dt':None,'temp':{'status':1, 'value':None}, 'hum':{'status':1, 'value':None}})
                self.digiTest.stop_mear()
                self.sendCommunicateCallback('update_machine_status',{'dt':{'status':1, 'value':None},'temp':None, 'hum':None})
                self.digiTest.set_remote(False)
            except:
                self.lg.debug('set hardware failed in the finall step of sequence')

            self.in_test_mode = False

    async def get_cur_temp_and_humi(self, websocket):
        dtInfo = {}
        dtInfo['status']=0
        dtInfo['value']=None
        tempInfo = {}
        tempInfo['status']=0
        tempInfo['value']=None
        humInfo = {}
        humInfo['status']=0
        humInfo['value']=None
        if not self.in_test_mode:
            try:
                if self.dChamb.connected:
                    self.curT = self.dChamb.get_real_temperature()
                    self.curH = self.dChamb.get_real_humidity()
                    isRunning = self.dChamb.is_test_running()
                    tempInfo['status']= 2 if isRunning else 1
                    tempInfo['value']=self.curT
                    humInfo['status']= 2 if isRunning else 1
                    humInfo['value']=self.curH
                else:
                    tempInfo['status']=0
                    tempInfo['value']=None
                    humInfo['status']=0
                    humInfo['value']=None 
            except Exception as e:
                err_msg = traceback.format_exc()
            finally:
                try:
                    if self.digiTest.connected:
                        statusCode, dtInfo['value'] =self.digiTest.get_single_value(dummyTemp=self.curT, immediate=True)
                        if statusCode == 1:
                            dtInfo['status'] = 1 
                        elif statusCode < 0:
                            dtInfo['status'] = 1 
                        else:
                            dtInfo['status'] = 2 # running
                    else:
                        dtInfo['value']= None
                except Exception as e:
                    err_msg = traceback.format_exc()
                finally:
                    status = {'dt':dtInfo,'temp':tempInfo, 'hum':humInfo}
                    asyncio.run_coroutine_threadsafe(self.socketCallback(websocket,'update_cur_status',status), self.parentLoop)
        else:
            await asyncio.sleep(0.1) 

    def findLoopPair(self, loopid, mainClass):
        loopStarIndex, loopEndIndex = 0, 0
        for i,s in enumerate(mainClass):
            if s.category == 'loop':
                if s.itemname == 'loop start' and s.loopid == loopid:
                    loopStarIndex = i
                elif s.itemname == 'loop end' and s.loopid == loopid:
                    loopEndIndex = i
                    break
        return (loopStarIndex,loopEndIndex)
    
    def sendResultCallback(self,result):
        if result['category'] == 'hardness' and result['status'] == 'PASS':
            self.saveResult2DatabaseCallback(result)
        elif result['category'] == 'hardness' and result['status'] == 'MEAR_NEXT':
            self.saveResult2DatabaseCallback(result)
        else:
            pass
        # asyncio.create_task(self.socketCallback(self.ws,'update_step_result',result))
        asyncio.run_coroutine_threadsafe(self.socketCallback(self.ws,'update_step_result',result), self.parentLoop)
        # asyncio.create_task(self.socketCallback(self.ws,'update_step_result',result))
    
    def sendCommunicateCallback(self,cmd, data=''):
        # await self.socketCallback(self.ws,cmd,data)
        asyncio.run_coroutine_threadsafe(self.socketCallback(self.ws,cmd,data), self.parentLoop)
        # asyncio.create_task(self.socketCallback(self.ws,cmd,data))
    
    def saveResult2DatabaseCallback(self,testResult):
        # await self.saveTestResult2DbCallback(testResult)
        # asyncio.run_coroutine_threadsafe(self.saveTestResult2DbCallback(testResult), self.parentLoop)
        self.saveTestResult2DbCallback(testResult)
        # asyncio.create_task(self.saveTestResult2DbCallback(testResult))
        
    def continuous_mear(self,status):
        if status == 'retry':
            self.interuptQueue.put('retry')
        elif status == 'continue':
            self.interuptQueue.put('continue')
        elif status == 'run_teardown':
            self.interuptQueue.put('run_teardown')
        elif status == 'resume':
            self.pauseQueue.put('resume')
        elif status == 'stop':
            self.interuptQueue.put('stop')
    
    def set_normal_test_stop(self):
        self.testStop=True
        self.interuptQueue.put('stop')

    def set_test_pause(self):
        self.pauseQueue.put('pause')

    def set_test_stop(self):
        self.testStop=True
        self.interruptStop=True
        self.stopMsgQueue.put(True)
        self.interuptQueue.put('stop')
        self.pauseQueue.put('resume')
    
    def init_digiChamber_controller(self,obj_digiChmaber):
        try:
            self.dChamb = obj_digiChmaber
            conn = self.dChamb.connect()
            info = self.dChamb.get_chamber_info()
            running = self.dChamb.is_test_running()
            self.log_to_db_func('digiChamber init ok', 'info', False)
            self.log_to_db_func('digiChamber system info: {}'.format(info), 'info', False)
            statusCode = 0
            if conn:
                statusCode = 1
            if running:
                statusCode = 2
            return statusCode
        except Exception as e:
            self.log_to_db_func('digiChamber init error: {}'.format(e), 'error', False)
            return 0

    def close_digiChamber_controller(self):
        self.dChamb.close()
    
    def init_digitest_controller(self,obj_digitest, COM='COM3'):
        try:
            self.digiTest = obj_digitest
            conn = self.digiTest.open_rs232(COM, timeout=5)
            self.digiTest.config(debug=False, wait_cmd = True)
            self.digiTest.setRotation()
            N, n = self.digiTest.get_rotation_info()
            dev_name = self.digiTest.get_dev_name()
            dev_sw_version = self.digiTest.get_dev_software_version()
            self.log_to_db_func('digitest init ok', 'info', False)
            self.log_to_db_func('digitest device name: {}, software version: {}'.format(dev_name, dev_sw_version), 'info', False)
            self.log_to_db_func('digitest N: {}, n: {}'.format(N, n), 'info', False)
            statusCode = 0
            if conn:
                statusCode = 1
            return statusCode
        except Exception as e:
            self.log_to_db_func('digitest init error: {}'.format(e), 'error', False)
            return 0

    def close_digitest_controller(self):
        self.digiTest.set_remote(False)
        self.digiTest.close_rs232()
    
    async def moveTableLast(self):
        success, res = self.digiTest.goLastSample()
        return success, res

    async def moveTableHome(self):
        success, res = self.digiTest.set_rotation_home()
        return success, res
            
    async def moveTableNext(self):
        success, res = self.digiTest.goNextSample()
        return success, res
    
    async def moveTableToIndex(self, index):
        N = int(index)
        n = 1
        if N == 0:
            n = 0
        success, res = self.digiTest.set_rotation_pos(N, n)
        return success, res

