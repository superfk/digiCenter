#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import sys
sys.path.append('server/corelib')
sys.path.append('server/instrClass')
sys.path.append('server/productlib')
import zerorpc
from corelib.hardwarelib.digiChamber import DigiChamber, DummyChamber
from corelib.hardwarelib.instrClass.digitest import Digitest
from corelib.logging_module.baLogger import TimeRotateLogger
from corelib.UserManagement.user_login import UserManag
from productlib.digiCenter.pd_digichamber import DigiChamberProduct
import ctypes  # An included library with Python install.
import struct
from db_operation import DB
import json
from corelib.utility import utility as util
import datetime,time
import os
import locale
import re
import gevent
import pandas as pd
import string
import threading
import random
import asyncio
import websockets

class PyServerAPI(object):
    def __init__(self):
        self.users = set()
        self.digiTest = Digitest()
        self.digiChamber = DigiChamber()
        self.lg = TimeRotateLogger('syslog', 'M', 5)
        self.db = DB(r"SHAWNNB\SQLEXPRESS", 'BareissAdmin', 'BaAdmin')
        self.userMang = UserManag(self.db,"Guest", "Guest", 0, True)
        self.config = read_system_config(r'C:\\digiCenter\config.json')
        self.productProcess = DigiChamberProduct('digiCenter',r"C:\\data_exports",self.sendMsg)
        self.initialized = False

    async def register(self,websocket):
        self.users.add(websocket)
        print('new user connected: {}'.format(websocket))

    async def unregister(self,websocket):
        self.users.remove(websocket)
        print('user disconnected: {}'.format(websocket))

    async def handler(self,websocket, path):
        # register(websocket) sends user_event() to websocket
        await self.register(websocket)
        if not self.initialized:
            # loop = asyncio.get_event_loop()
            # task = loop.create_task(self.continousSend())
            self.initialized=True
        try:
            async for message in websocket:
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
                elif cmd == 'getExportFolder':
                    await self.getExportFolder(websocket)
                elif cmd == 'getDBServer':
                    await self.getDBServer(websocket)
                elif cmd == 'update_machine_remote':
                    await self.update_machine_remote(websocket,data)
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
                elif cmd == 'get_user_account_list':
                    await self.get_user_account_list(websocket)
                elif cmd == 'add_new_user':
                    userid = data['userid']
                    role = data['role']
                    await self.add_new_user(websocket,userid,role)
                elif cmd == 'delete_user':
                    await self.delete_user(websocket,data)
                elif cmd == 'activate_user':
                    await self.activate_user(websocket,data)
                elif cmd == 'deactivate_user':
                    await self.deactivate_user(websocket,data)
                elif cmd == 'give_new_password':
                    userid = data['userid']
                    role = data['role']
                    await self.give_new_password(websocket,userid,role)
                elif cmd == 'get_user_role_list':
                    await self.get_user_role_list(websocket)
                elif cmd == 'get_function_list':
                    await self.get_function_list(websocket,data)
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
                    await self.delete_role(websocket,data)
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
                elif cmd == 'machine_connect':
                    await self.machine_connect(websocket)
                elif cmd == 'run_cmd':
                    await self.run_cmd(websocket,data)
                elif cmd == 'init_hw':
                    self.init_hw(websocket)
                elif cmd == 'run_seq':
                    loop = asyncio.new_event_loop()
                    def f(loop):
                        asyncio.set_event_loop(loop)
                        loop.run_forever()
                    t = threading.Thread(target=f, args=(loop,))
                    t.start()
                    future = asyncio.run_coroutine_threadsafe(self.run_seq(websocket), loop)
                elif cmd == 'stop_seq':
                    self.stop_seq()
                elif cmd == 'export_test_data':
                    tabledata = data['tabledata']
                    path = data['path']
                    option = data['option']
                    await self.export_test_data(websocket,tabledata,path,option)
                elif cmd == 'query_data_from_db':
                    await self.query_data_from_db(websocket,data)
                elif cmd == 'save_to_database':
                    await self.save_to_database(websocket,data)
                elif cmd == 'close_all':
                    await self.close_all(websocket)
                else:
                    print('Not found this cmd: {}'.format(cmd))
        except Exception as e:
            self.lg.debug(e)
            await self.unregister(websocket)

    async def sendMsg(self, websocket, cmd, data=None):
        msg = {'cmd': cmd, 'data': data}
        print('server sent msg: {}'.format(msg))
        try:
            await websocket.send(json.dumps(msg))
        except Exception as e:
            print('error: {}'.format(e))
            
        
    async def continousSend(self):
        while True:
            try:
                if self.users:
                    await asyncio.wait([self.sendMsg(user,'ping', random.random()) for user in self.users])
            except Exception as e:
                print(e)
            finally:
                await asyncio.sleep(10)
            

    async def load_sys_config(self, websocket, path):
        self.config = read_system_config(path)
        self.config_path = path
        self.productProcess.setDefaultSeqFolder(self.config['system']['default_seq_folder'])

    async def load_default_lang(self, websocket, appRoot):
        lang = self.config['system']['default_lang']
        path = os.path.join(appRoot, 'lang')
        lang_data = util.readLang(path, lang)
        await self.sendMsg(websocket,'update_default_lang',lang_data)
    
    async def update_default_lang(self, websocket, appRoot, lang):
        self.config['system']['default_lang'] = lang
        write_system_config(path=self.config_path, data = self.config)
        lang = self.load_default_lang(websocket, appRoot)
        await self.sendMsg(websocket,'update_default_lang',lang)
    
    async def get_server_time(self, websocket):
        now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S")
        await self.sendMsg(websocket,'get_server_time',now)
    
    async def getIP(self, websocket):
        await self.sendMsg(websocket,'get_ip',self.config['system']['machine_ip'])
    
    async def getExportFolder(self, websocket):
        await self.sendMsg(websocket,'get_export_folder',self.config['system']['default_export_folder'])
    
    async def getDBServer(self, websocket):
        await self.sendMsg(websocket,'get_db_server',self.config['system']['database']["server"])

    async def update_machine_remote(self, websocket, ip):
        self.config['system']['machine_ip'] = ip
        write_system_config(path=self.config_path, data = self.config)
        await self.sendMsg(websocket,'update_machine_ip',self.load_sys_config(websocket, self.config_path))

    async def update_default_export_folder(self, websocket, folder):
        self.config['system']['default_export_folder'] = folder
        write_system_config(path=self.config_path, data = self.config)
        await self.sendMsg(websocket,'update_machine_ip',self.load_sys_config(websocket, self.config_path))
    
    async def update_database_server(self, websocket, servername):
        self.config['system']['database']["server"] = servername
        write_system_config(path=self.config_path, data = self.config)
        await self.sendMsg(websocket,self.load_sys_config(websocket, self.config_path))
    
    async def check_config_updated(self, websocket, configs):
        results = []
        results.append(configs['machine_ip'] == self.config['system']['machine_ip'])
        results.append(configs['export_folder'] == self.config['system']['default_export_folder'])
        results.append(configs['db_server'] == self.config['system']['database']["server"]) 
        await self.sendMsg(websocket,all(results))
    
    async def getHostName(self, websocket):
        await self.sendMsg(websocket,os.environ['COMPUTERNAME'])
    
    async def backend_init(self, websocket):
        # self.db = DB(self.config['system']['database']['server'], 'BareissAdmin', 'BaAdmin')
        self.db = DB(r'' + os.environ['COMPUTERNAME'] + r'\SQLEXPRESS', 'BareissAdmin', 'BaAdmin')
        res = {}
        if not self.db.connect('DigiChamber'):
            res['result']=0
            res['resp']="Error: Connect to database error"
            await self.sendMsg(websocket,cmd='result_of_backendinit',data=res)
        else:
            res['result']=1
            res['resp']="database connected"
            self.userMang = UserManag(self.db,"Guest", "Guest", 0, True)
            await self.sendMsg(websocket,cmd='result_of_backendinit',data=res)

    async def login(self, websocket, username, password):
        await self.sendMsg(websocket,self.userMang.login(username, password))
        
    async def get_user_account_list(self, websocket):
        await self.sendMsg(websocket,self.userMang.get_user_account_list())
    
    async def add_new_user(self, websocket,userID, role):
        await self.sendMsg(websocket,self.userMang.add_new_user(userID, role))
        
    async def delete_user(self, websocket, userID):
        await self.sendMsg(websocket,self.userMang.delete_user(userID))

    async def activate_user(self, websocket, userID):
        await self.sendMsg(websocket,self.userMang.activate_user(userID))
    
    async def deactivate_user(self, websocket, userID):
        await self.sendMsg(websocket,self.userMang.deactivate_user(userID))

    async def give_new_password(self, websocket, userID, role):
        await self.sendMsg(websocket,self.userMang.give_new_password(userID, role))
    
    async def get_user_role_list(self, websocket):
        await self.sendMsg(websocket,self.userMang.get_user_role_list())
    
    async def get_function_list(self, websocket, userrole='Guest'):
        await self.sendMsg(websocket,self.userMang.get_function_list(userrole='Guest'))

    async def update_fnc_of_role(self, websocket,role,funcs,enabled,visibled):
        await self.sendMsg(websocket,self.userMang.update_fnc_of_role(role,funcs,enabled,visibled))
    
    async def add_role(self, websocket, role, level):
        await self.sendMsg(websocket,self.userMang.add_role(role, level))
               
    async def delete_role(self, websocket,role):
        await self.sendMsg(websocket,self.userMang.delete_role(role))

    async def set_new_password_when_first_login(self, websocket,userID, curPW, newPW, newPWagain):
        await self.sendMsg(websocket,self.userMang.set_new_password_when_first_login(userID, curPW, newPW, newPWagain))

    async def log_to_db(self, websocket, msg, msg_type='info', audit=False):
        pass
        # fields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
        # now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")
        # values = [now, self.user.username, self.user.role, msg_type, msg, audit]
        # self.db.insert('System_log', fields, values)
        # return str(values)

    async def machine_connect(self, websocket):
        """Connnect to DigiChamber"""
        ip = self.config['system']['machine_ip']
        port = self.config['system']['machine_port']
        print("conntect to machine with ip {}, port {}".format(ip,port))
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
        try:
            data = json.loads(data)
            scriptName = data['cmd']
            data = data['data']
            response = await self.productProcess.run_script(websocket,scriptName,data)
        except Exception as e:
            self.lg.error(e)
    
    def init_hw(self, websocket):
        ip = self.config['system']['machine_ip']
        port = self.config['system']['machine_port']
        digiChamber_obj = DummyChamber(ip,port)
        self.productProcess.init_digiChamber_controller(digiChamber_obj)

    async def run_seq(self, websocket):
        self.productProcess.create_seq()
        await self.productProcess.run_seq(websocket)

    def stop_seq(self):
        print('execute stop seq')
        self.productProcess.set_test_stop()

    async def export_test_data(self, websocket,tableData, path='testdata', options=['csv']):
        try:
            export_folder = self.config['system']['default_export_folder']
            util.newPathIfNotExist(export_folder)
            fieldname = list(tableData[0].keys())
            for op in options:
                if op == 'csv':
                    util.newPathIfNotExist(os.path.join(export_folder,op))
                    new_path = os.path.join(export_folder,op , path + '.'+op)
                    expt = util.CSV_ExportWorker(tableData)
                    expt.tabledata2DataFrame()
                elif op == 'auto':
                    util.newPathIfNotExist(os.path.join(export_folder,op))
                    new_path = os.path.join(export_folder,op , path + '.csv')
                    expt = util.CSV_ExportWorker(tableData)
                    expt.tabledata2DataFrame() 
                elif op == 'pdf':
                    util.newPathIfNotExist(os.path.join(export_folder,op))
                    new_path = os.path.join(export_folder,op , path + '.'+op)
                elif op == 'html':
                    util.newPathIfNotExist(os.path.join(export_folder,op))
                    new_path = os.path.join(export_folder,op , path + '.'+op)
                elif op == 'excel':
                    util.newPathIfNotExist(os.path.join(export_folder,op))
                    new_path = os.path.join(export_folder,op , path + '.xlsx')
                    expt = util.Excel_ExportWorker(tableData)
                    expt.tabledata2DataFrame()
                else:
                    pass
                expt.save(path=new_path)
            await self.sendMsg(websocket,{1, "Export data successfully!"})
        except Exception as e:
            await self.sendMsg(websocket,{0, "Export data error ({})".format(e)})

    async def query_data_from_db(self, websocket, filters):
        condition = r"WHERE "
        print(filters)
        fields = ["Sample_Counter", "Operator", "Compound_Folder", "Compound", "Batch", "Productiondate", "Hardness_1", "Hardness_2", "Hardness_3", "Timestamp",
                "T_sample", "WeightDry", "WeightWet", "T_Liquid", "Density"]
        types = ["float", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(255)", "float", "float", "float", "datetime2",
                "float", "float", "float", "float", "float"]
        if filters['date_start']:
            condition = condition + r"Timestamp>='{}' AND Timestamp < '{}' ".format(filters['date_start'], filters['date_end'])
        if filters['batch'] and filters['batch'] != '':
            condition = condition + r"AND Batch LIKE '%{}%' ".format(filters['batch'])
        if filters['operator'] and filters['operator'] != '':
            condition = condition + r"AND Operator LIKE '%{}%';".format(filters['operator'])
        data = self.db.select('Test_Data',fields, condition,types)
        await self.sendMsg(websocket,{1, data})
    
    async def save_to_database(self, websocket, tableData):
        fields = self.config['system']['database']['test_data_fields'].split(",")
        fields_type = self.config['system']['database']['test_data_fields_type'].split(",")
        num_format = self.config['system']['locale_num_format']
        locale.setlocale(locale.LC_ALL, num_format)
        fields_not_include_first = fields_type[1:]
        #fields = ['Recordtime','Sample_Counter', 'Operator', 'Compound_Folder', 'Compound', 'Batch', 'Productiondate', 'Hardness_1', 'Hardness_2', 'Hardness_3', 'Timestamp', 'AreaTemp', 'AirHumidity', 'T_Sample', 'WeightDry', 'WeightWet', 'T_Liquid', 'Density']
        #fields_type = ['str', 'str','str','str','str','str','float','float','float','time', 'float','float','float','float','float']
        now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")

        for d in tableData:
            values = []
            values.append(now)
            for i, (key, value) in enumerate(d.items()):
                ftype = fields_not_include_first[i]
                if value:
                    if type(value) != str:
                        value = str(value)
                    if ftype == 'float':
                        value = locale.atof(value)
                    if ftype == 'time':
                        pattern = re.compile(r"[^a-z^A-Z^#: ,-][0-9]*")
                        match = re.findall(pattern, value)
                        if match:
                            match = [int(x) if len(x)<6 else int(x[0:6]) for x in match]
                            value = datetime.datetime(match[0],match[1], match[2],match[3],match[4], match[5], match[6])
                    values.append(value)
                else:
                    if ftype == 'str':
                        values.append('')
                    elif ftype == 'float':
                        values.append(0.0)
                    else:
                        values.append('')
            try:
                await self.db.insert('Test_Data', fields, values)
            except:
                print("{} data is duplicated!")
                pass

    async def close_all(self, websocket):
        try:
            await self.db.close()
        except:
            pass
        try:
            await self.productProcess.close_digiChamber_controller()
        except:
            pass
        try:
            await self.digiTest.set_remote(False)
            await self.digiTest.close_rs232()
        except:
            pass
        

def string_onlyPrintable(text):
    return ''.join(filter(lambda x: x in string.printable, text)).strip()

def read_system_config(path='config.json'):
    with open(path, 'r', encoding= 'utf-8') as f:
        data = json.load(f)
    return data

def write_system_config(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def Mbox(title='Ipnfo', text='', style=0):
    return ctypes.windll.user32.MessageBoxW(0, text, title, style)

def parse_port():
    port = 4242
    try:
        port = int(sys.argv[1])
    except Exception as e:
        pass
    return '{}'.format(port)

def main():
    sokObj = PyServerAPI()
    # asyncio.ensure_future(sokObj.backend_init(None))
    # sio.register_namespace(sokObj)
    # print('reading config.json')
    # currentDirectory = os.getcwd()
    # rpc.load_sys_config(currentDirectory+'/config.json')
    # print('init database')
    # rpc.backend_init()
    port=5678
    addr = 'tcp://127.0.0.1:{}'.format(port)
    print('start running on {}'.format(addr))
    # web.run_app(app,port=port)
    # eventlet.wsgi.server(eventlet.listen(('127.0.0.1', port)), app)
    # s = zerorpc.Server(rpc, heartbeat=None)
    # s.bind(addr)
    # s.run()

    start_server = websockets.serve(sokObj.handler, "localhost", port, ping_interval=10)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    # loop.create_task(sokObj.load_sys_config(None,r'C:\\digiCenter\config.json'))
    # loop.create_task(sokObj.backend_init(None))
    loop.run_forever()
    

if __name__ == '__main__':
    main()