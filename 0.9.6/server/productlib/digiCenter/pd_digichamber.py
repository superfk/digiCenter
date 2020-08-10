import traceback
from productlib import pd_product
import corelib.utility.utility as util
import os, sys
import productlib.digiCenter.digiCenter_seq as seqClass
import asyncio
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
    
    def set_sysConfig(self, sysConfig):
        self.sysConfig = sysConfig

    def set_lang(self, lang_data):
        self.lang_data = lang_data
    
    def set_logger(self, loggerObj):
        self.lg = loggerObj
    
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
            await self.socketCallback(websocket, 'update_sequence', self.script)
        except FileNotFoundError:
            await self.socketCallback(websocket, 'reply_server_error', {'error':self.lang_data['server_reply_batch_seq_not_found']})
    
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
            self.lg.debug(self.stepsClass)
            return True
        else:
            return False

    async def run_seq(self,websocket, batchInfoForSamples):
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
            self.stopMsgQueue = queue.Queue()
            self.pauseQueue = queue.Queue()
            self.testStop=False
            self.interruptStop=False
            self.create_result_callback_loop()
            self.ws = websocket
            self.errorMsg = None
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
                    s.pauseQueue = self.pauseQueue
                    s.set_batchinfo(self.batchInfo)
                    s.set_batchInfoForSamples(batchInfoForSamples)
                    s.set_sysConfig(self.sysConfig)
                    s.lg = self.lg

                # main process 
                while True:
                    # check hw connection
                    if not self.dChamb.connected or not self.digiTest.connected:
                        self.set_test_stop()
                        if not self.digiTest.connected:
                            self.errorMsg = self.lang_data['digitest_disconnect_msg']
                            self.log_to_db_func('digitest_disconnected', 'error', False)
                        else:
                            self.errorMsg = self.lang_data['digichamber_disconnect_msg']
                            self.log_to_db_func('digichamber_disconnected', 'error', False)
                        break
                    # check whether stop this loop
                    if cursor >= totalStepsCounts or self.testStop:
                        break
                    # continuous process
                    self.log_to_db_func('current cursor: {}'.format(cursor), 'info', False)
                    # get payload step
                    step = self.stepsClass[cursor]

                    curStepName = step.__class__.__name__
                    self.log_to_db_func('current step name: {}'.format(curStepName), 'info', False)                    

                    # do step
                    testResult = step.do()
                    self.log_to_db_func('output of testResult: {}'.format(testResult), 'info', True)

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

                    # check if finish final step
                    if cursor >= totalStepsCounts:
                        self.testStop=True
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
                self.pauseQueue.task_done()
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
                err_msg = traceback.format_exc()
                self.log_to_db_func('digiChamber get temperature error: {}'.format(err_msg), 'info', False)
            finally:
                try:
                    dtInfo['status']=self.digiTest.connected
                    if self.digiTest.connected:
                        statusCode, dtInfo['value'] =self.digiTest.get_single_value(self.curT)
                    else:
                        dtInfo['value']= None
                except Exception as e:
                    err_msg = traceback.format_exc()
                    self.log_to_db_func('digitest get value error: {}'.format(err_msg), 'info', False)
                finally:
                    status = {'dt':dtInfo,'temp':tempInfo, 'hum':humInfo}
                    await self.socketCallback(websocket,'update_cur_status',status)

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
    
    def create_result_callback_loop(self):
        self.loop = asyncio.new_event_loop()
        def f(loop):
            asyncio.set_event_loop(self.loop)
            self.loop.run_forever()
        t = threading.Thread(target=f, args=(self.loop,))
        t.start()

    def sendResultCallback(self,result):
        if result['category'] == 'hardness' and result['status'] == 'PASS':
            self.saveResult2DatabaseCallback(result)
        elif result['category'] == 'hardness' and result['status'] == 'MEAR_NEXT':
            self.saveResult2DatabaseCallback(result)
        else:
            pass
        future = asyncio.run_coroutine_threadsafe(self.socketCallback(self.ws,'update_step_result',result), self.loop)
    
    def sendCommunicateCallback(self,cmd, data):
        future = asyncio.run_coroutine_threadsafe(self.socketCallback(self.ws,cmd,data), self.loop)
    
    def saveResult2DatabaseCallback(self,testResult):
        future = asyncio.run_coroutine_threadsafe(self.saveTestResult2DbCallback(testResult), self.loop)
        
    def continuous_mear(self,retry=False):
        if retry:
            self.pauseQueue.put('retry')
        else:
            self.pauseQueue.put('continue')
    
    def set_normal_test_stop(self):
        self.testStop=True
        self.pauseQueue.put('stop')

    def set_test_stop(self):
        self.testStop=True
        self.interruptStop=True
        self.stopMsgQueue.put(True)
        self.pauseQueue.put('stop')
    
    def init_digiChamber_controller(self,obj_digiChmaber):
        try:
            self.dChamb = obj_digiChmaber
            conn = self.dChamb.connect()
            info = self.dChamb.get_chamber_info()
            info = self.dChamb.set_tempShift()
            self.log_to_db_func('digiChamber init ok', 'info', False)
            self.log_to_db_func('digiChamber system info: {}'.format(info), 'info', False)
            return conn
        except Exception as e:
            self.log_to_db_func('digiChamber init error: {}'.format(e), 'error', False)
            return False

    def close_digiChamber_controller(self):
        self.dChamb.close()
    
    def init_digitest_controller(self,obj_digitest, COM='COM3'):
        try:
            self.digiTest = obj_digitest
            conn = self.digiTest.open_rs232(COM, timeout=5)
            self.digiTest.setRotation()
            dev_name = self.digiTest.get_dev_name()
            dev_sw_version = self.digiTest.get_dev_software_version()
            self.log_to_db_func('digitest init ok', 'info', False)
            self.log_to_db_func('digitest device name: {}, software version: {}'.format(dev_name, dev_sw_version), 'info', False)
            return conn
        except Exception as e:
            self.log_to_db_func('digitest init error: {}'.format(e), 'error', False)
            return False

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

