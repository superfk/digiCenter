#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import sys
sys.path.append('server/corelib')
sys.path.append('server/corelib/hardwarelib/instrClass')
sys.path.append('server/productlib')
from corelib.hardwarelib.digiChamber import DigiChamber, DummyChamber
from corelib.hardwarelib.instrClass.digitest import Digitest, DummyDigitest
# from corelib.logging_module.baLogger import TimeRotateLogger
from corelib.usermanagelib.user_login import UserManag
from corelib.lang.lang_tool import load_json_lang_from_json
from productlib.digiCenter.pd_digichamber import DigiChamberProduct
from corelib.databaselib.db_operation import DB
import json
from corelib.utility import utility as util
import datetime
import os
import threading
import random
import asyncio
import websockets
import traceback
from loguru import logger


class BatchInfo(object):
    def __init__(self,project, batch, create_date, notes, seq_name, numOfSample):
        self.project = project
        self.batch = batch
        self.createDate = create_date
        self.notes = notes
        self.seq = seq_name
        self.numSamples = int(numOfSample)

class PyServerAPI(object):
    def __init__(self):
        self.users = set()
        self.digiTest = None # Digitest()
        self.digiChamber = None # DigiChamber()
        # self.lg = TimeRotateLogger('syslog', 'M', 5)
        logger.add(sys.stdout, format="{time} - {level} - {message}")
        logger.add(r"systemlog/{time:YYYY-MM-DD}/file_{time:YYYY-MM-DD}.log", rotation="5 MB")
        self.lg = logger
        # self.db = DB(r"SHAWNNB\SQLEXPRESS", 'BareissAdmin', 'BaAdmin')        
        self.db = DB(r"(localDB)\BareissLocalDB", r"BareissAdmin", r"BaAdmin")
        self.db.connect('DigiChamger')
        self.userMang = UserManag(self.db,"Guest", "Guest", 0, True)
        self.config = None
        self.productProcess = DigiChamberProduct('digiCenter',r"C:\\data_exports",self.sendMsg,self.saveTestData)
        self.productProcess.set_logger(self.lg)
        self.productProcess.set_log_to_db_func(self.local_log_to_db)
        self.initialized = False
        self.langFolder = ''
        self.batch = None
        self.lang_data = None

    async def register(self,websocket):
        self.users.add(websocket)
        self.lg.debug('new user connected: {}'.format(websocket))
        self.local_log_to_db('new user connected: {}'.format(websocket))

    async def unregister(self,websocket):
        self.users.remove(websocket)
        self.lg.debug('user disconnected: {}'.format(websocket))
        self.local_log_to_db('new user connected: {}'.format(websocket))

    async def handler(self,websocket, path):
        # register(websocket) sends user_event() to websocket
        await self.register(websocket)
        if not self.initialized:
            # loop = asyncio.get_event_loop()
            # task = loop.create_task(self.continousSend())
            self.initialized=True
        try:
            async for message in websocket:
                # print(message)
                # self.lg.debug(message)
                msg = json.loads(message)
                cmd = msg["cmd"]
                data = msg["data"]
                if cmd == 'pong':
                    print('client pong: {}'.format(data))
                elif cmd == 'load_sys_config':
                    await self.load_sys_config(websocket,data)
                elif cmd == 'load_default_lang':
                    appRoot = data
                    await self.load_default_lang(websocket,appRoot)
                elif cmd == 'update_default_lang':
                    appRoot = data['appRoot']
                    lang = data['lang']
                    await self.update_default_lang(websocket,appRoot,lang)
                elif cmd == 'get_server_time':
                    await self.get_server_time(websocket)
                elif cmd == 'getIP':
                    await self.getIP(websocket)
                elif cmd == 'get_digitest_com':
                    await self.get_digitest_com(websocket)
                elif cmd == 'get_digitest_manual_mode':
                    await self.get_digitest_manual_mode(websocket)
                elif cmd == 'getExportFolder':
                    await self.getExportFolder(websocket)
                elif cmd == 'getDBServer':
                    await self.getDBServer(websocket)
                elif cmd == 'getRotationTable_N':
                    await self.getRotationTable_N(websocket)
                elif cmd == 'update_machine_remote':
                    await self.update_machine_remote(websocket,data)
                elif cmd =='update_digitest_remote':
                    await self.update_digitest_remote(websocket,data)
                elif cmd =='update_digitest_manual_mode':
                    await self.update_digitest_manual_mode(websocket,data)
                elif cmd == 'update_database_server':
                    await self.update_database_server(websocket,data)
                elif cmd == 'check_config_updated':
                    await self.check_config_updated(websocket,data)
                elif cmd == 'getHostName':
                    await self.getHostName(websocket)
                elif cmd == 'backend_init':
                    await self.backend_init(websocket)
                elif cmd == 'login':
                    username = data['username']
                    password = data['password']
                    await self.login(websocket,username,password)
                elif cmd == 'logout':
                    await self.logout(websocket)
                elif cmd == 'get_user_account_list':
                    await self.get_user_account_list(websocket)
                elif cmd == 'add_new_user':
                    userid = data['userid']
                    role = data['role']
                    await self.add_new_user(websocket,userid,role)
                elif cmd == 'delete_user':
                    userid = data['userid']
                    await self.delete_user(websocket,userid)
                elif cmd == 'activate_user':
                    userid = data['userid']
                    await self.activate_user(websocket,userid)
                elif cmd == 'deactivate_user':
                    userid = data['userid']
                    await self.deactivate_user(websocket,userid)
                elif cmd == 'give_new_password':
                    userid = data['userid']
                    role = data['role']
                    await self.give_new_password(websocket,userid,role)
                elif cmd == 'get_user_role_list':
                    await self.get_user_role_list(websocket)
                elif cmd == 'get_function_list':
                    role = data['role']
                    await self.get_function_list(websocket,role)
                elif cmd == 'update_fnc_of_role':
                    role = data['role']
                    funcs = data['funcs']
                    enabled = data['enabled']
                    visibled = data['visibled']
                    await self.update_fnc_of_role(websocket,role,funcs,enabled,visibled)
                elif cmd == 'add_role':
                    level = data['level']
                    role = data['role']
                    await self.add_role(websocket,role,level)
                elif cmd == 'delete_role':
                    role = data['role']
                    await self.delete_role(websocket,role)
                elif cmd == 'set_new_password_when_first_login':
                    userid = data['userid']
                    curpw = data['curpw']
                    newpw = data['newpw']
                    newpwagain = data['newpaagain']
                    await self.set_new_password_when_first_login(websocket,userid,curpw,newpw,newpwagain)
                elif cmd == 'log_to_db':
                    msg = data['msg']
                    msg_type = data['msg_type']
                    audit = data['audit']
                    await self.log_to_db(websocket,msg,msg_type,audit)
                elif cmd == 'get_syslog_from_db':
                    start = data['start']
                    end = data['end']
                    await self.get_syslog_from_db(websocket, start, end)
                elif cmd == 'run_cmd':
                    await self.run_cmd(websocket,data)
                elif cmd == 'init_hw':
                    await self.init_hw(websocket)
                elif cmd == 'run_seq':
                    batchInfoForSamples = data['batchInfoForSamples']
                    loop = asyncio.new_event_loop()
                    def f(loop):
                        asyncio.set_event_loop(loop)
                        loop.run_forever()
                    t = threading.Thread(target=f, args=(loop,))
                    t.start()
                    future = asyncio.run_coroutine_threadsafe(self.run_seq(websocket,batchInfoForSamples), loop)
                elif cmd == 'continue_seq':
                    isRetry = data
                    self.productProcess.continuous_mear(isRetry)
                elif cmd == 'create_batch':
                    batches = data
                    for bc in batches:
                        project = bc['project']
                        batch = bc['batch']
                        notes = bc['notes']
                        seq_name = bc['seq_name']
                        numSamples = bc['numSample']
                        await self.create_batch(websocket,project, batch, notes, seq_name, numSamples)
                elif cmd == 'continue_batch':
                    batches = data
                    for bc in batches:
                        project = bc['project']
                        batch = bc['batch']
                        notes = bc['notes']
                        seq_name = bc['seq_name']
                        numSamples = bc['numSample']
                        await self.continues_batch(websocket,project, batch, notes, seq_name, numSamples)
                elif cmd == 'query_batch_history':
                    await self.query_batch_history(websocket)
                elif cmd == 'stop_seq':
                    self.stop_seq()
                elif cmd == 'export_test_data_from_client':
                    tabledata = data['tabledata']
                    path = data['path']
                    option = data['option']
                    await self.export_test_data_from_client(websocket,tabledata,path,option)
                elif cmd == 'query_data_from_db':
                    await self.query_data_from_db(websocket,data)
                elif cmd == 'get_digitest_is_rotaion_mode':
                    await self.get_digitest_is_rotaion_mode(websocket)
                elif cmd == 'close_all':
                    await self.close_all(websocket)
                else:
                    self.lg.debug('Not found this cmd: {}'.format(cmd))
        except Exception as e:
            try:
                err_msg = traceback.format_exc()
                self.lg.debug(err_msg)
                await self.sendMsg(websocket,'reply_server_error',{'error':err_msg})
            except:
                self.lg.debug('error during excetipn handling')
                self.lg.debug(e)

    async def sendMsg(self, websocket, cmd, data=None):
        msg = {'cmd': cmd, 'data': data}
        filter_cmd = ['update_cur_status', 'pong']
        if cmd not in filter_cmd:
            # self.lg.debug('server sent msg: {}'.format(msg))
            pass
        try:
            await websocket.send(json.dumps(msg))
        except Exception as e:
            err_msg = traceback.format_exc()
            self.lg.debug('error during send message with websocket')
            self.lg.debug(err_msg)
            
    async def continousSend(self):
        while True:
            try:
                if self.users:
                    await asyncio.wait([self.sendMsg(user,'ping', random.random()) for user in self.users])
            except Exception as e:
                err_msg = traceback.format_exc()
                self.lg.debug('error during send ping message with websocket')
                self.lg.debug(err_msg)
            finally:
                await asyncio.sleep(10)

    async def load_sys_config(self, websocket, path):
        self.config = util.read_system_config(path)
        self.config_path = path
        self.productProcess.setDefaultSeqFolder(self.config['system']['default_seq_folder'])
        self.productProcess.set_force_manual_mode(self.config['system']['digitest_manual_mode'])
        self.lg.debug('log system config: {}'.format(self.config))

    async def load_default_lang(self, websocket, appRoot):
        lang = self.config['system']['default_lang']
        self.langFolder = os.path.join(appRoot, 'lang')
        # self.lang_data = util.readLang(self.langFolder, lang)
        self.lang_data = load_json_lang_from_json(self.langFolder, lang)
        self.productProcess.set_lang(self.lang_data)
        self.lg.debug('loaded lang file with lang {}'.format(lang))
        self.userMang.set_lang(self.lang_data, lang)
        await self.sendMsg(websocket,'reply_update_default_lang',{'langID':lang, 'langData':self.lang_data})
    
    async def update_default_lang(self, websocket, appRoot, lang):
        self.config['system']['default_lang'] = lang
        util.write_system_config(path=self.config_path, data = self.config)
        self.langFolder = os.path.join(appRoot, 'lang')
        # self.lang_data = util.readLang(self.langFolder, lang)
        self.lang_data = load_json_lang_from_json(self.langFolder, lang)
        self.productProcess.set_lang(self.lang_data)
        self.lg.debug('update lang file with lang {}'.format(lang))
        self.userMang.set_lang(self.lang_data, lang)
        await self.sendMsg(websocket,'reply_update_default_lang', {'langID':lang, 'langData':self.lang_data})
    
    async def get_server_time(self, websocket):
        now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S")
        await self.sendMsg(websocket,'get_server_time',now)    
    async def getIP(self, websocket):
        await self.sendMsg(websocket,'get_ip',self.config['system']['machine_ip'])    
    async def get_digitest_com(self, websocket):
        await self.sendMsg(websocket,'get_digitest_com',self.config['system']['digitest_COM'])
    async def get_digitest_manual_mode(self, websocket):
        await self.sendMsg(websocket,'get_digitest_manual_mode',self.config['system']['digitest_manual_mode'])
    async def getExportFolder(self, websocket):
        await self.sendMsg(websocket,'get_export_folder',self.config['system']['default_export_folder'])    
    async def getDBServer(self, websocket):
        await self.sendMsg(websocket,'get_db_server',self.config['system']['database']["server"])
    async def getRotationTable_N(self, websocket):
        await self.sendMsg(websocket,'getRotationTable_N',self.config['system']['rotationTable_N'])
    async def update_machine_remote(self, websocket, ip):
        self.config['system']['machine_ip'] = ip
        util.write_system_config(path=self.config_path, data = self.config)
    async def update_digitest_remote(self, websocket, COM):
        self.config['system']['digitest_COM'] = COM
        util.write_system_config(path=self.config_path, data = self.config)
    async def update_digitest_manual_mode(self, websocket, enableManualMode):
        self.config['system']['digitest_manual_mode'] = enableManualMode
        util.write_system_config(path=self.config_path, data = self.config)
        self.productProcess.set_force_manual_mode(self.config['system']['digitest_manual_mode'])
    async def update_default_export_folder(self, websocket, folder):
        self.config['system']['default_export_folder'] = folder
        util.write_system_config(path=self.config_path, data = self.config)    
    async def update_database_server(self, websocket, servername):
        self.config['system']['database']["server"] = servername
        util.write_system_config(path=self.config_path, data = self.config)    
    async def check_config_updated(self, websocket, configs):
        results = []
        results.append(configs['machine_ip'] == self.config['system']['machine_ip'])
        results.append(configs['digitest_COM'] == self.config['system']['digitest_COM'])
        results.append(configs['digitest_manual_mode'] == self.config['system']['digitest_manual_mode'])
        results.append(configs['export_folder'] == self.config['system']['default_export_folder'])
        # results.append(configs['db_server'] == self.config['system']['database']["server"]) 
        await self.sendMsg(websocket,'reply_checking_config',all(results))
    
    async def getHostName(self, websocket):
        await self.sendMsg(websocket,'get_hostname',os.environ['COMPUTERNAME'])
    
    async def backend_init(self, websocket):
        # self.db = DB(self.config['system']['database']['server'], 'BareissAdmin', 'BaAdmin')
        # self.db = DB(r'' + os.environ['COMPUTERNAME'] + r'\SQLEXPRESS', 'BareissAdmin', 'BaAdmin')
        self.db = DB(r'(localDB)\BareissLocalDB', 'BareissAdmin', 'BaAdmin')
        res = {}
        if not self.db.connect('DigiChamber'):
            res['result']=0
            res['resp']='database connection error'
            self.lg.debug(res['resp'])
            await self.sendMsg(websocket,cmd='result_of_backendinit',data=res)
        else:
            res['result']=1
            res['resp']='database connection ok'
            self.lg.debug(res['resp'])
            self.userMang.db = self.db
            self.userMang.set_log_to_db_func(self.local_log_to_db)
            self.productProcess.db = self.db
            await self.sendMsg(websocket,cmd='result_of_backendinit',data=res)

    async def login(self, websocket, username, password):
        await self.sendMsg(websocket,'reply_login',self.userMang.login(username, password))
    
    async def logout(self, websocket):
        await self.sendMsg(websocket,'reply_logout',self.userMang.log_out())
        
    async def get_user_account_list(self, websocket):
        await self.sendMsg(websocket,'reply_get_user_account_list',self.userMang.get_user_account_list())
    
    async def add_new_user(self, websocket,userID, role):
        await self.sendMsg(websocket,'reply_add_new_user',self.userMang.add_new_user(userID, role, self.config['system']['default_export_folder']))
        
    async def delete_user(self, websocket, userID):
        await self.sendMsg(websocket,'reply_delete_user',self.userMang.delete_user(userID))

    async def activate_user(self, websocket, userID):
        await self.sendMsg(websocket,'reply_activate_user',self.userMang.activate_user(userID))
    
    async def deactivate_user(self, websocket, userID):
        await self.sendMsg(websocket,'reply_deactivate_user',self.userMang.deactivate_user(userID))

    async def give_new_password(self, websocket, userID, role):
        await self.sendMsg(websocket,'reply_give_new_password',self.userMang.give_new_password(userID, role))
    
    async def get_user_role_list(self, websocket):
        await self.sendMsg(websocket,'reply_get_user_role_list',self.userMang.get_user_role_list())
    
    async def get_function_list(self, websocket, userrole='Guest'):
        await self.sendMsg(websocket,'reply_get_function_list',self.userMang.get_function_list(userrole=userrole))

    async def update_fnc_of_role(self, websocket,role,funcs,enabled,visibled):
        await self.sendMsg(websocket,'reply_update_fnc_of_role',self.userMang.update_fnc_of_role(role,funcs,enabled,visibled))
    
    async def add_role(self, websocket, role, level):
        await self.sendMsg(websocket,'reply_add_role',self.userMang.add_role(role, level))
               
    async def delete_role(self, websocket,role):
        await self.sendMsg(websocket,'reply_delete_role',self.userMang.delete_role(role))

    async def set_new_password_when_first_login(self, websocket,userID, curPW, newPW, newPWagain):
        await self.sendMsg(websocket,'reply_set_new_password_when_first_login',
        self.userMang.set_new_password_when_first_login(userID, curPW, newPW, newPWagain))

    async def log_to_db(self, websocket, msg, msg_type='info', audit=False, reply=False):
        fields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
        now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")
        values = [now, self.userMang.user.username, self.userMang.user.role, msg_type, msg, audit]
        self.db.insert('System_log', fields, values)
        self.lg.debug('save system log into database with field: {}, values: {}'.format(fields,values))
        if reply:
            await self.sendMsg(websocket,'reply_log_to_db',str(values))
    
    def local_log_to_db(self,msg, msg_type='info', audit=False):
        try:
            fields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
            now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")
            values = [now, self.userMang.user.username, self.userMang.user.role, msg_type, msg, audit]
            self.db.insert('System_log', fields, values)
            self.lg.debug('save system log into database with field: {}, values: {}'.format(fields,values))
        except Exception as e:
            err_msg = traceback.format_exc()
            self.lg.debug('error when save system log into database in local function')
            self.lg.debug(err_msg)

    async def get_syslog_from_db(self,websocket, start, end):
        fields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
        condition = r"WHERE Timestamp>='{}' AND Timestamp <= '{}' ".format(start,end)
        ret = self.db.select('System_log',fields, condition)
        filename = datetime.datetime.now().strftime(r"%Y-%m-%d_%H%M%S")
        export_folder = self.config['system']['default_export_folder']
        export_folder = os.path.join(export_folder, 'syslog')
        await self.export_test_data(websocket, ret, export_folder=export_folder, filename=filename, options=['csv'], sep=',')
        link = os.path.join(export_folder, filename+'.csv')
        await self.sendMsg(websocket,'reply_get_syslog_from_db',[1, ret, "{}".format(self.lang_data['server_downloading_ok']).format(len(ret)), link])
    
    async def machine_connect(self, websocket):
        """Connnect to DigiChamber"""
        ip = self.config['system']['machine_ip']
        port = self.config['system']['machine_port']
        self.lg.debug("conntecting to machine with ip {}, port {}".format(ip,port))
        try:
            if self.digiChamber.connected:
                await self.sendMsg(websocket,"connection already established")
            else:
                self.digiChamber = DigiChamber(ip,port)
                self.digiChamber.connect()
                await self.sendMsg(websocket,"connection ok")
        except:
            try:
                self.digiChamber = DigiChamber(ip,port)
                self.digiChamber.connect()
                await self.sendMsg(websocket,"connection ok")
            except:
                await self.sendMsg(websocket,"connection failed")
    
    async def run_cmd(self, websocket,data):
        respObj = {'error':False,'res':None}
        data = json.loads(data)
        scriptName = data['cmd']
        data = data['data']
        response = await self.productProcess.run_script(websocket,scriptName,data)
    
    async def init_hw(self, websocket):
        ip = self.config['system']['machine_ip']
        port = self.config['system']['machine_port']
        COM = self.config['system']['digitest_COM']
        mode = self.config['system']['mode']
        isConn_chamber = False
        isConn_digitest= False
        # set instance of hw
        try:
            if mode == 'demo':
                self.digiChamber = DummyChamber(ip,port)
                self.digiTest = DummyDigitest()
            else:
                self.digiChamber = DigiChamber(ip,port)
                self.digiTest = Digitest()
            isConn_chamber = self.productProcess.init_digiChamber_controller(self.digiChamber)
            if isConn_chamber:
                self.lg.debug('digiChamber init OK')
            isConn_digitest = self.productProcess.init_digitest_controller(self.digiTest,COM)
            if isConn_digitest:
                self.lg.debug('digiTest init OK')
                self.get_digitest_is_rotaion_mode(websocket)
            await self.sendMsg(websocket,'reply_init_hw',{'resp_code':1, 'res':self.lang_data['server_hw_init_ok']})
            await self.sendMsg(websocket,'reply_init_hw_status',{'digitest':isConn_digitest, 'digichamber': isConn_chamber})
        except Exception as e:
            err_msg = traceback.format_exc()
            self.lg.debug('error during excetipn handling in init_hw')
            self.lg.debug(err_msg)
            await self.sendMsg(websocket,'reply_init_hw',{'resp_code':0, 'res':self.lang_data['server_hw_init_NG'], 'reason':'{}'.format(err_msg)})
            await self.sendMsg(websocket,'reply_init_hw_status',{'digitest':isConn_digitest, 'digichamber': isConn_chamber})

    async def run_seq(self, websocket, batchInfoForSamples=[]):
        self.productProcess.create_seq()
        self.lg.debug('batchInfoForSamples',batchInfoForSamples)
        await self.productProcess.run_seq(websocket, batchInfoForSamples)      

    def stop_seq(self):
        self.lg.debug('execute stop seq')
        self.productProcess.set_test_stop()

    async def create_batch(self,websocket, project, batch, notes, seq_name, numOfSample):
        # check project and batch name exsisted?
        fields = ["Project_Name", "Batch_Name", "Creation_Date", "Note", "Last_seq_name", "NumSample"]
        condition = r"WHERE Project_Name ='{}' AND Batch_Name='{}'".format(project,batch)
        data = self.db.select('Batch_data', fields, condition)
        if not len(data)==0:
            # unique batch already exsisted
            txt = self.lang_data['server_ask_cont_wehn_proj_batch_exist_reason'].format(batch)
            title = self.lang_data['server_ask_cont_wehn_proj_batch_exist_title']
            await self.sendMsg(websocket,'reply_create_batch', {'resp_code': 0, 'title':title,'reason':txt, 'batchName':batch})
        else:
            curtime = datetime.datetime.now()
            now = curtime.strftime(r"%Y/%m/%d %H:%M:%S.%f")
            self.batch = BatchInfo(project, batch, curtime, notes, seq_name, numOfSample)
            self.productProcess.setBatchInfo(self.batch)
            values = [project, batch, now, notes, seq_name, numOfSample]
            self.db.insert('Batch_data', fields, values)
            txt = self.lang_data['server_reply_batch_created_reason'].format(batch)
            title = self.lang_data['server_reply_batch_created_title']
            await self.sendMsg(websocket,'reply_create_batch',{'resp_code': 1, 'title':title,'reason':txt,'batchName':batch})

    async def continues_batch(self,websocket, project, batch, notes, seq_name, numOfSample):
        curtime = datetime.datetime.now()
        now = curtime.strftime(r"%Y/%m/%d %H:%M:%S.%f")
        self.batch = BatchInfo(project, batch, curtime, notes, seq_name, numOfSample)
        self.productProcess.setBatchInfo(self.batch)
        fields = ["Note", "Last_seq_name", "NumSample"]
        values = [notes, seq_name, numOfSample]
        condition = r"WHERE Project_Name ='{}' AND Batch_Name='{}'".format(project,batch)
        self.db.update("Batch_data",fields,values,condition)
        txt = self.lang_data['server_reply_batch_cont_reason']
        title = self.lang_data['server_reply_batch_cont_title']
    
    async def query_batch_history(self,websocket):
        # check project and batch name exsisted?
        fields = ["Project_Name", "Batch_Name", "Creation_Date", "Note", "Last_seq_name", "NumSample"]
        condition = r"ORDER BY Batch_Name"
        data = self.db.select('Batch_data', fields, condition)
        for i,d in enumerate(data):
            date = d['Creation_Date'].split('.')[0]
            data[i]['Creation_Date'] = date
        await self.sendMsg(websocket,'reply_query_batch_history', data)

    async def saveTestData(self,testResult):
        fields = ['Recordtime','Project_name','Batch_name','Seq_name','Operator','Seq_step_id','Sample_counter','Hardness_result',
        'Temperature','Humidity','Raw_data','Math_method']
        now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")
        recTime = now
        # BatchInfo(project, batch, curtime, notes, seq_name)
        proj = testResult['project']
        batch = testResult['batch']
        seq = testResult['seq_name']
        op = self.userMang.user.username
        seq_id = testResult['stepid']
        sampleCounter = testResult['hardness_dataset']['sampleid']
        h_result = testResult['value']
        temp_result = round(testResult['actTemp'],3)
        hum_result = round(testResult['actHum'],3)
        raw = testResult['hardness_dataset']['dataset']
        raw = json.dumps(raw)
        math_method = testResult['hardness_dataset']['method']
        values = [recTime,proj,batch,seq,op,seq_id,sampleCounter,h_result,temp_result,hum_result,raw,math_method]
        try:
            self.lg.debug('Save Test data')
            self.lg.debug(values)
            self.db.insert('Test_Data', fields, values)
        except Exception as e:
            err_msg = traceback.format_exc()
            self.lg.debug('Save Test Data error!')
            self.lg.debug(err_msg)
    
    async def export_test_data_from_client(self, websocket,tableData, filename='testdata', options=['csv']):
        export_folder = self.config['system']['default_export_folder']
        export_folder = os.path.join(export_folder, 'test_data')
        await self.export_test_data(websocket, tableData, export_folder, filename , options, sep=';')

    async def export_test_data(self, websocket, tableData, export_folder, filename='testdata', options=['csv'],sep=';'):
        try:
            util.newPathIfNotExist(export_folder)
            fieldname = list(tableData[0].keys())
            for op in options:
                new_path = os.path.join(export_folder, filename + '.' + op)
                if op == 'csv':
                    expt = util.CSV_ExportWorker(tableData,sep=sep)
                elif op == 'auto':
                    new_path = os.path.join(export_folder, filename + '.csv')
                    expt = util.CSV_ExportWorker(tableData)
                elif op == 'excel':
                    new_path = os.path.join(export_folder, filename + '.xlsx')
                    expt = util.Excel_ExportWorker(tableData)
                else:
                    pass
                expt.tabledata2DataFrame()
                expt.save(path=new_path)
            txt = self.lang_data['server_export_ok_reason']
            title = self.lang_data['server_export_ok_title']
            await self.sendMsg(websocket,'reply_export_test_data_from_client',{'resp_code': 1, 'title':title, 'res':txt})
        except Exception as e:
            err_msg = traceback.format_exc()
            self.lg.debug('export Test Data error!')
            self.lg.debug(err_msg)
            txt = self.lang_data['server_export_NG_reason']
            title = self.lang_data['server_export_NG_title']
            await self.sendMsg(websocket,'reply_export_test_data_from_client',{'resp_code': 0, 'title':title, 'res':txt})

    async def query_data_from_db(self, websocket, filters):
        condition = r"WHERE "
        fields = ["Recordtime", "Project_name", "Batch_name", "Seq_name", "Operator", "Seq_step_id", 
        "Sample_counter","Hardness_result","Temperature","Humidity","Raw_data","Math_method"]
        # types = ["datetime2", "varchar(255)", "varchar(255)", "nvarchar(1024)", "varchar(255)", "smallint", "float", "float", "float", "datetime2",
        #         "float", "float", "float", "float", "float"]
        if filters['date_start']:
            condition = condition + r"Recordtime>='{}' AND Recordtime < '{}' ".format(filters['date_start'], filters['date_end'])
        if filters['project'] and filters['project'] != '':
            condition = condition + r"AND Project_name LIKE '%{}%' ".format(filters['project'])
        if filters['batch'] and filters['batch'] != '':
            condition = condition + r"AND Batch_name LIKE '%{}%' ".format(filters['batch'])
        if filters['operator'] and filters['operator'] != '':
            condition = condition + r"AND Operator LIKE '%{}%';".format(filters['operator'])
        data = self.db.select('Test_Data',fields, condition)
        await self.sendMsg(websocket,'reply_query_data_from_db',{'resp_code': 1, 'res':data})

    async def get_digitest_is_rotaion_mode(self, websocket):
        isRotationMode = self.digiTest.isConnectRotation()
        await self.sendMsg(websocket,'get_digitest_is_rotaion_mode',isRotationMode)

    async def close_all(self, websocket):
        try:
            self.db.close()
            self.lg.debug('close database ok')
        except Exception as e:
            self.lg.debug('close database error!')
            self.lg.debug(e)
        try:
            self.productProcess.close_digiChamber_controller()
            self.digiChamber=None
            self.lg.debug('close digichamber ok')
        except Exception as e:
            self.lg.debug('close digichamber error!')
            self.lg.debug(e)
        try:
            self.productProcess.close_digitest_controller()
            self.digiTest = None
            self.lg.debug('close digiTest ok')
        except Exception as e:
            self.lg.debug('close digiTest error!')
            self.lg.debug(e)
        finally:
            await self.sendMsg(websocket,'reply_close_all')
        

def main():
    sokObj = PyServerAPI()
    port=5678
    start_server = websockets.serve(sokObj.handler, "127.0.0.1", port, ping_interval=30)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    addr = 'tcp://127.0.0.1:{}'.format(port)
    print('start running on {}'.format(addr))
    loop.run_forever()
    
if __name__ == '__main__':
    main()