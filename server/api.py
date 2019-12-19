#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import sys
sys.path.append('server/corelib')
sys.path.append('server/instrClass')
sys.path.append('server/productlib')
import zerorpc
from corelib.hardwarelib.digiChamber import DigiChamber
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



class PyServerAPI(object):
    def __init__(self):
        self.digiTest = Digitest()
        self.digiChamber = DigiChamber()
        self.lg = TimeRotateLogger('syslog', 'M', 5)
        self.db = DB(r"SHAWNNB\SQLEXPRESS", 'BareissAdmin', 'BaAdmin')
        self.userMang = UserManag(self.db,"Guest", "Guest", 0, True)
        self.config_path = None
        self.productProcess = DigiChamberProduct('digiCenter')
        #self.config = read_system_config(r'C:\\BaDBManager\BaDBManager\\pymain\\config.json')
      
    def read_csv(self, path):
        try:
            return util.get_csv_content(path, delimiter=';')
        except Exception as e:
            return None

    def echo(self, text):
        """echo any text"""
        return text
    
    def load_sys_config(self, path):
        self.config = read_system_config(path)
        self.config_path = path
        self.productProcess.setDefaultSeqFolder(self.config['system']['default_seq_folder'])
        self.lg.debug(self.config)
        return self.config

    def load_default_lang(self, appRoot):
        lang = self.config['system']['default_lang']
        path = os.path.join(appRoot, 'lang')
        lang_data = util.readLang(path, lang)
        return lang_data
    
    def update_default_lang(self, appRoot, lang):
        self.config['system']['default_lang'] = lang
        write_system_config(path=self.config_path, data = self.config)
        return self.load_default_lang(appRoot)
    
    def get_server_time(self):
        return datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S")
    
    def getIP(self):
        return self.config['system']['machine_ip']
    
    def getExportFolder(self):
        return self.config['system']['default_export_folder']
    
    def getDBServer(self):
        return self.config['system']['database']["server"]

    def update_machine_remote(self, ip):
        self.config['system']['machine_ip'] = ip
        write_system_config(path=self.config_path, data = self.config)
        return self.load_sys_config(self.config_path)

    def update_default_export_folder(self, folder):
        self.config['system']['default_export_folder'] = folder
        write_system_config(path=self.config_path, data = self.config)
        return self.load_sys_config(self.config_path)
    
    def update_database_server(self, servername):
        self.config['system']['database']["server"] = servername
        write_system_config(path=self.config_path, data = self.config)
        return self.load_sys_config(self.config_path)
    
    def check_config_updated(self, configs):
        results = []
        results.append(configs['machine_ip'] == self.config['system']['machine_ip'])
        results.append(configs['export_folder'] == self.config['system']['default_export_folder'])
        results.append(configs['db_server'] == self.config['system']['database']["server"]) 
        return all(results)
    
    def getHostName(self):
        return os.environ['COMPUTERNAME']
    
    def backend_init(self):
        # self.db = DB(self.config['system']['database']['server'], 'BareissAdmin', 'BaAdmin')
        self.db = DB(r'' + self.getHostName() + r'\SQLEXPRESS', 'BareissAdmin', 'BaAdmin')
        if not self.db.connect(self.config['system']['database']['main_db']):
            return 0, "Error: Connect to database error"
        else:
            self.userMang = UserManag(self.db,"Guest", "Guest", 0, True)
            return 1, "database connected"

    def login(self, username, password):
        return self.userMang.login(username, password)
        
    def get_user_account_list(self):
        return self.userMang.get_user_account_list()
    
    def add_new_user(self,userID, role):
        return self.userMang.add_new_user(userID, role)
        
    def delete_user(self, userID):
        return self.userMang.delete_user(userID)

    def activate_user(self, userID):
        return self.userMang.activate_user(userID)
    
    def deactivate_user(self, userID):
        return self.userMang.deactivate_user(userID)

    def give_new_password(self, userID, role):
        return self.userMang.give_new_password(userID, role)
    
    def get_user_role_list(self):
        return self.userMang.get_user_role_list()
    
    def get_function_list(self, userrole='Guest'):
        return self.userMang.get_function_list(userrole='Guest')

    def update_fnc_of_role(self,role,funcs,enabled,visibled):
        return self.userMang.update_fnc_of_role(role,funcs,enabled,visibled)
    
    def add_role(self, role, level):
        return self.userMang.add_role(role, level)
               
    def delete_role(self,role):
        return self.userMang.delete_role(role)

    def set_new_password_when_first_login(self,userID, curPW, newPW, newPWagain):
        return self.userMang.set_new_password_when_first_login(userID, curPW, newPW, newPWagain)

    def log_to_db(self, msg, msg_type='info', audit=False):
        pass
        # fields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
        # now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")
        # values = [now, self.user.username, self.user.role, msg_type, msg, audit]
        # self.db.insert('System_log', fields, values)
        # return str(values)

    def machine_connect(self):
        """Connnect to DigiChamber"""
        ip = self.config['system']['machine_ip']
        port = self.config['system']['machine_port']
        print("conntect to machine with ip {}, port {}".format(ip,port))
        try:
            if self.digiChamber.connected:
                return "connection already established"
            else:
                self.digiChamber = DigiChamber(ip,port)
                self.digiChamber.connect()
                return "connection ok"
        except:
            try:
                self.digiChamber = DigiChamber(ip,port)
                self.digiChamber.connect()
                return "connection ok"
            except:
                return "connecton failed"
    
    def run_cmd(self,data):
        respObj = {'error':False,'res':None}
        try:
            data = json.loads(data)
            scriptName = data['scriptName']
            data = data['data']
            response = self.productProcess.run_script(scriptName,data)
            respObj['res']=response
        except Exception as e:
            self.lg.error(e)
            response = e
            respObj['error']=True
            respObj['res']=response
        finally:
            return respObj
    
    @zerorpc.stream
    def run_seq(self):
        self.productProcess.create_seq()
        return self.productProcess.run_seq()
    

    def export_test_data(self,tableData, path='testdata', options=['csv']):
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
            return 1, "Export data successfully!"
        except Exception as e:
            return 0, "Export data error ({})".format(e)

    def query_data_from_db(self, filters):
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
        return data
    
    def save_to_database(self, tableData):
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
                self.db.insert('Test_Data', fields, values)
            except:
                print("{} data is duplicated!")
                pass

    def close_all(self):
        try:
            self.db.close()
        except:
            pass
        try:
            self.digiChamber.close()
        except:
            pass
        try:
            self.digiTest.set_remote(False)
            self.digiTest.close_rs232()
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
    rpc = PyServerAPI()
    # print('reading config.json')
    # currentDirectory = os.getcwd()
    # rpc.load_sys_config(currentDirectory+'/config.json')
    # print('init database')
    # rpc.backend_init()

    addr = 'tcp://127.0.0.1:4242'
    s = zerorpc.Server(rpc, heartbeat=None)
    s.bind(addr)
    print('start running on {}'.format(addr))
    s.run()
    

if __name__ == '__main__':
    main()