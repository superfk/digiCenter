#!/usr/bin/python
# -*- coding: UTF-8 -*-

from __future__ import print_function
import sys
import zerorpc
from digiChamber.digiChamber import DigiChamber
sys.path.append('server/instrClass')
from instrClass.digitest import Digitest
import ctypes  # An included library with Python install.
import struct
from db_operation import DB
import json
from user import User
import utility as util
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
        self.db = DB(r"SHAWNNB\SQLEXPRESS", 'BareissAdmin', 'BaAdmin')
        self.user = User("Guest", "Guest", 0, True)
        self.config_path = None
        #self.config = read_system_config(r'C:\\BaDBManager\BaDBManager\\pymain\\config.json')
      
    def read_csv(self, path):
        try:
            return util.get_csv_content(path, delimiter=';')
        except Exception as e:
            return None
    
    def read_upload_csv(self, path):
        try:
            data = util.get_csv_content(path, delimiter=';')
            
            if len(data)>0:
                col = list(data[0].keys())
                if len(col) != 5 or col[0] != 'Operator':
                    return 0 , 'file is not compatible'
                else:
                    return 1, data
            else:
                return 0, 'Cannot found contents'
        except Exception as e:
            return 0, 'Read File Error'
    
    def read_download_csv(self, path):
        try:
            data = util.get_csv_content(path, delimiter=';')
            print(data)
            
            if len(data)>0:
                col = list(data[0].keys())
                if len(col) != 15 or col[0] != 'Sample-Counter':
                    return 0 , 'file is not compatible'
                else:
                    return 1, data
            else:
                return 0, 'Cannot found contents'
        except Exception as e:
            return 0, 'Read File Error'

    def echo(self, text):
        """echo any text"""
        return text
    
    def load_sys_config(self, path):
        self.config = read_system_config(path)
        self.config_path = path
        print(self.config)
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
            return 1, "database connected"

    def login(self, username, password):
        login_ok = False
        reason = ""
        role = ""
        user = ""
        fn_list = list()
        first = False

        if username == "":
            # user is empty
            login_ok = False
            reason = "Please keyin username!"
            role = ""
            user = ''
            return login_ok, reason, user, role, fn_list
        if password == "" and username != "Guest":
            # password is empty
            login_ok = False
            reason = "Please keyin password!"
            role = ""
            user = ''
            return login_ok, reason, user, role, fn_list
        print("Username: {}".format(username))
        fields = ["User_Name", "PW", "User_Role", "Creation_Date", "Expired_Date", "Status", "First_login"]
        # status == 2 means deleted user
        condition = r"WHERE User_Name='{}' AND Status<>2;".format(username)
        data = self.db.select('UserList',fields,condition)
        print("Query data: {}".format(data))
        if len(data)>0:
            result = data[0] # should be only one match, each row is dict format
            exp_date = result["Expired_Date"]
            exp_date = datetime.datetime.strptime(exp_date, r'%Y/%m/%d %H:%M:%S.%f')
            now = datetime.datetime.now()
            if username != 'Guest':
                d_pw = util.decrypt_password(result["PW"])
            else:
                d_pw = ""
            if result["Status"] == 0:
                # user not enabled
                login_ok = False
                reason = "User is not enabled"
                role = ""
                user = ''
                return login_ok, reason, user, role, fn_list, first
            if exp_date < now:
                # user expired
                f = ["Status"]
                condition = r"WHERE User_Name='{}'".format(username)
                self.db.update('UserList', f, [0], condition)
                login_ok = False
                reason = "User is expired"
                role = ""
                user = ''
                return login_ok, reason, user, role, fn_list, first
            if password != d_pw and username != 'Guest':
                # user password not correct
                login_ok = False
                reason = "Password is not correct"
                role = ""
                user = ''
                return login_ok, reason, user, role, fn_list, first
            if result['First_login']:
                # user first login, need to change pw
                login_ok = False
                reason = "First Login, Please Change Password!"
                role = ""
                user = ''
                first = True
                return login_ok, reason, user, role, fn_list, first
            else:
                # user login ok
                f = ["User_Level"]
                condition = r"WHERE User_Role='{}'".format(result["User_Role"])
                role_level = self.db.select('UserRoleList',f, condition)[0]["User_Level"]
                f = ["Functions", "Enabled", "Visibled"]
                condition = r"WHERE User_Role='{}'".format(result["User_Role"])
                query = self.db.select('UserPermission',f, condition)
                for q in query:
                    fn={}
                    fn['function']=q['Functions']
                    fn['enable']=q['Enabled']
                    fn['visible']=q['Visibled']
                    fn_list.append(fn)
                login_ok = True if username != "Guest" else False
                reason = "Login ok" if username != "Guest" else "Guest login"
                role = result["User_Role"]
                user = username
                self.user = User(username, role, role_level, login_ok)
                return login_ok, reason, user, role, fn_list, first
        else:
            # user not found
            login_ok = False
            reason = "The '{}' user is not found".format(username)
            role = ""
            user = ""
            return login_ok, reason, user, role, fn_list, first

    def get_user_account_list(self):
        fields = ['User_Name', 'User_Role', 'Status', 'First_login', 'Creation_Date', 'Expired_Date']
        if self.user.role == 'System_Admin':
            condition = r"ORDER BY User_Name"
        else:
            condition = r" WHERE User_Role <> 'System_Admin' AND Status < 2 ORDER BY User_Name"      
        user_lists = self.db.select('UserList',fields, condition)
        new_user_list = []
        for d in user_lists:
            item={}
            item['User Name'] = d['User_Name']
            item['Role'] = d['User_Role']
            item['Status'] = d['Status']
            item['First?'] = d['First_login']
            item['Creation Date'] = datetime.datetime.strptime(d['Creation_Date'], r'%Y/%m/%d %H:%M:%S.%f').strftime(r'%Y/%m/%d %H:%M:%S')
            item['Expired Date'] = datetime.datetime.strptime(d['Expired_Date'], r'%Y/%m/%d %H:%M:%S.%f').strftime(r'%Y/%m/%d %H:%M:%S')
            new_user_list.append(item)
        return new_user_list
    
    def add_new_user(self,userID, role):
        # check if this user exsisted
        fields = ['User_Name']
        condition = r"WHERE User_Name = '{}' AND Status < 2".format(userID)
        user_lists = self.db.select('UserList',fields, condition)
        if len(user_lists) > 0:
            return 0,"This User already exsisted!", ''
        # check if this role exsisted
        fields = ["User_Role"]
        condition = r" WHERE User_Role = '{}'".format(role)
        user_role = self.db.select('UserRoleList', fields, condition)
        if len(user_role) == 0:
            return 0,"Please assign user role!", ''
        
        # generate random pw
        rnd_pw = util.randomStringDigits(6)
        ency_pw = util.encrypt_password(rnd_pw)

        # insert user
        fields = ["User_Name", "PW", "User_Role", "Creation_Date", "Expired_Date", "Status", "First_login"]
        tday = datetime.datetime.now()
        exp_date = util.add_months(tday, 6)
        creat_time = tday.strftime(r"%Y/%m/%d %H:%M:%S.000000")
        exp_time = exp_date.strftime(r"%Y/%m/%d %H:%M:%S.000000")
        values = [userID, ency_pw, role, creat_time, exp_time, 1, 1]
        try:
            self.db.insert("UserList",fields,values)
            folder_path = os.path.join(self.config['system']['default_export_folder'], 'first_pw')
            util.save_password_to_json(folder_path, userID, role, rnd_pw)
            return 1, 'Adding User Successfully!', rnd_pw
        except Exception as e:
            return 0, 'Error: adding user error ({})'.format(e), ''
        
    def delete_user(self, userID):
        if userID == 'Guest':
            return 0,"Guest user cannot be deleted!"
        if userID == 'BareissAdmin':
            return 0,"Super user cannot be deleted!"
        if userID == '':
            return 0,"Please selected one user first!"
        condition = r"WHERE User_Name = '{}'".format(userID)
        try:
            fields = ["Status"]
            self.db.update("UserList", fields,[2],condition)
            return 1, 'User Deleted Successfully!'
        except Exception as e:
            return 0, 'Error: deleting user error ({})'.format(e)

    def activate_user(self, userID):
        if userID == 'Guest':
            return 0,"Guest is always activated!"
        if userID == 'BareissAdmin':
            return 0,"Super user is always activated!"
        if userID == '':
            return 0,"Please selected one user first!"
        fields = ["Status"]
        condition = r" WHERE User_Name = '{}' AND Status < 2".format(userID)
        try:
            self.db.update("UserList", fields,[1],condition)
            return 1, 'User Activated Successfully!'
        except Exception as e:
            return 0, 'Error: activating user error ({})'.format(e)
    
    def deactivate_user(self, userID):
        if userID == 'Guest':
            return 0,"Guest user cannot be deactivated!"
        if userID == 'BareissAdmin':
            return 0,"Super user cannot be deactivated!"
        if userID == '':
            return 0,"Please selected one user first!"
        fields = ["Status"]
        condition = r" WHERE User_Name = '{}' AND Status < 2".format(userID)
        try:
            self.db.update("UserList", fields,[0],condition)
            return 1, 'User Deactivated Successfully!'
        except Exception as e:
            return 0, 'Error: eactivating user error ({})'.format(e)

    def give_new_password(self, userID, role):
        if userID == 'Guest':
            return 0,"Guest user don't need password!",""
        if userID == 'BareissAdmin':
            return 0,"Super user password is protected and do not need to be changed!",""
        if userID == '':
            return 0,"Please selected one user first!",""

        # generate random pw
        rnd_pw = util.randomStringDigits(6)
        ency_pw = util.encrypt_password(rnd_pw)

        fields = ["PW", "Expired_Date", "Status", "First_login"]
        now = datetime.datetime.now()
        exp_date = util.add_months(now, 6)
        exp_time = exp_date.strftime(r"%Y/%m/%d %H:%M:%S.000000")
        values = [ency_pw, exp_time, 1, 1]
        condition = r" WHERE User_Name = '{}' AND Status < 2".format(userID)
        try:
            self.db.update("UserList", fields,values, condition)
            folder_path = os.path.join(self.config['system']['default_export_folder'], 'first_pw')
            util.save_password_to_json(folder_path, userID, role, rnd_pw)
            return 1, 'User Reset Password Successfully!', rnd_pw
        except Exception as e:
            return 0, 'Error: eactivating user error ({})'.format(e),""
    
    def get_user_role_list(self):
        f = ["User_Role"]
        condition = r" WHERE User_Level < 255 ORDER BY User_Level DESC"
        user_role = self.db.select('UserRoleList',f, condition)
        return user_role
    
    def get_function_list(self, userrole='Guest'):
        # f = ["Functions", "Enabled", "Visibled"]
        # condition = r" INNER JOIN [FunctionList] ON [UserPermission].Functions=[FunctionList].Functions WHERE [User_Role]='{}' ORDER BY [FunctionList].[Display_order]".format(userrole)
        # fn_list = self.db.select('UserRoleList',f, condition)
        exe_str = """
        SELECT FunctionList.Display_order, FunctionList.Display_fnc_name, UserPermission.[Enabled], UserPermission.Visibled, FunctionList.Tree_index, FunctionList.Functions
        FROM FunctionList
        LEFT JOIN UserPermission ON FunctionList.Functions = UserPermission.Functions
		WHERE UserPermission.User_Role = '{}'
        ORDER BY FunctionList.Display_order;
        """.format(userrole)
        fn_list = self.db.execute(exe_str)
        final_fun = []
        for f in fn_list:
            d = {}
            d['Index'] = f[0]
            d["Functions"] = "{}{}".format(f[4]*"==", "> " if f[4]>0 else "+ ") + f[1]
            d["Enabled"] = f[2]
            d["Visibled"] = f[3]
            d['Tree Index'] = f[4]
            d['fnc_name']= f[5]
            final_fun.append(d)
        return final_fun

    def update_fnc_of_role(self,role,funcs,enabled,visibled):
        fields = ["Enabled", "Visibled"]
        if role=='':
            return 0, "Please Select One Role first"
        if role == "Guest":
            return 0, "Role of Guest cannot be modified!"

        try:
            for f, e, v in zip(funcs, enabled, visibled):
                condition = r"WHERE User_Role='{}' AND Functions = '{}'".format(role, f)
                self.db.update('UserPermission', fields, [e,v], condition)
            return 1, "Update Successfully!"
        except Exception as e:
            return 0, "Error: Updating user permission error ({})".format(e)
    
    def add_role(self, role, level):
        fields = ["User_Role", "User_Level"]
        condition = r"WHERE User_Role='{}'".format(role)
        ret = self.db.select("UserRoleList", fields, condition=condition)
        isExist = False
        if ret == None:
            isExist = True
        elif len(ret) == 0:
            isExist = True
        
        if isExist:
            try:
                level = max(1,min(254,int(level))) # limit 1 - 254
                self.db.insert("UserRoleList", fields, [role, level])
                # copy user permission from guest
                fields = ["Functions", "Enabled", "Visibled"]
                condition = r"WHERE User_Role='{}'".format('Guest')
                ret = self.db.select("UserPermission", fields, condition=condition)
                for d in ret:
                    fields = ["User_Role","Functions", "Enabled", "Visibled"]
                    fn = d['Functions']
                    enb = d['Enabled']
                    visb = d['Visibled']
                    self.db.insert("UserPermission",fields=fields,data=[role,fn,enb,visb])
                return 1, "Add Role Successfully"
            except Exception as e:
                return 0, "Error: Add Role error ({})".format(e)
        else:
            return 0, "This Role {} already exsisted!".format(role)
               
    def delete_role(self,role):
        if role=='':
            return 0, "Please Select One Role first"
        if role == "Guest":
            return 0, "Role of Guest cannot be deleted!"

        condition = r"WHERE User_Role='{}'".format(role)
        try:
            self.db.delete("UserPermission",condition)
            self.db.delete("UserRoleList",condition)
            fields = ["User_Role"]
            self.db.update("UserList", fields,['Guest'],condition)
            return 1, "Delete Role Successfully"
        except Exception as e:
            return 0, "Error: Delete Role error ({})".format(e)

    def set_new_password_when_first_login(self,userID, curPW, newPW, newPWagain):
        # check current password is correct
        fields = ["PW"]
        condition = r"WHERE User_Name = '{}'".format(userID)
        ret = self.db.select('UserList',fields, condition)
        result = ret[0]
        pwIndb = result['PW']

        if not curPW == util.decrypt_password(pwIndb):
            return 0, "Current Password is not correct" 

        # check new password policy
        if len(newPW) < 6:
            return 0, "Length of new password should be greater than 5"
        if not util.isPW_complex(newPW):
            return 0, "New password should contain at least one capital letter, lowercase letter and number"
        if newPW != newPWagain:
            return 0, "Repeating password is not identical to new password"

        # update passowrd
        encp_pw = util.encrypt_password(newPW)
        now = datetime.datetime.now()
        exp_date = util.add_months(now, 6)
        exp_time = exp_date.strftime(r"%Y/%m/%d %H:%M:%S.000000")
        f = ["PW", "Expired_Date","First_login"]
        condition = r"WHERE User_Name='{}'".format(userID)
        try:
            self.db.update('UserList', f, [encp_pw, exp_time, 0], condition)
            return 1, "Password is saved successfully! Please login again!"
        except Exception as e:
            return 0, "Error: First Login error ({})".format(e)

    def log_to_db(self, msg, msg_type='info', audit=False):
        pass
        # fields = ["Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
        # now = datetime.datetime.now().strftime(r"%Y/%m/%d %H:%M:%S.%f")
        # values = [now, self.user.username, self.user.role, msg_type, msg, audit]
        # self.db.insert('System_log', fields, values)
        # return str(values)

    def machine_connect(self):
        """Connnect to PLC"""
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
            
    def get_actual_control_variable_temp_value(self):
        return self.digiChamber.get_real_control_variable_value()
    
    def set_control_variable_temp_value(self,value):
        return self.digiChamber.set_setPoint(value)
    
    def get_control_variable_temp_value(self):
        return self.digiChamber.get_setPoint()
    
    def set_gradup_temp_value(self,value):
        return self.digiChamber.set_gradient_up(value)
    
    def set_graddown_temp_value(self,value):
        return self.digiChamber.set_gradient_down(value)
    
    def get_control_variable_temp_maxmin(self):
        info = self.digiChamber.get_control_variables_info()
        temp_max = None
        temp_min = None
        for v in info:
            if v['name'] == 'Temperature':
                temp_max = v['max']
                temp_min = v['min']
                
        return temp_min, temp_max

    def get_actual_temp(self):
        return self.digiChamber.get_real_temperature()
    
    def get_info(self):
        return self.digiChamber.get_chamber_info()
    
    def start_run(self):
        return self.digiChamber.set_manual_mode(True)
    
    def stop_run(self):
        return self.digiChamber.set_manual_mode(False)
    
    def connect_DT(self):
        self.digiTest.open_rs232("COM3", timeout=10)
    
    def get_DT_info(self):
        info = {}
        info['dev_name'] = self.digiTest.get_dev_name()
        info['sv'] = self.digiTest.get_dev_software_version()
        info['duration'] = self.digiTest.get_ms_duration()
        info['method'] = self.digiTest.get_ms_method()
        info['mode'] = self.digiTest.get_mode()
        return info

    def set_DT_remote(self, enabled):
        self.digiTest.set_remote(enabled=enabled)
    
    def set_DT_mode(self, mode):
        self.digiTest.set_mode(mode)

    def set_DT_duration(self, duration):
        self.digiTest.set_ms_duration(duration)

    def start_DT_mear(self):
        self.set_DT_remote(True)
        self.digiTest.start_mear()
    
    def stop_DT_mear(self):
        self.digiTest.stop_mear()

    def get_DT_single_data(self):
        return self.digiTest.get_single_value()
    
    @zerorpc.stream
    def get_DT_graph_data(self):
        self.digiTest.config(debug=True)
        getBuffer = self.digiTest.get_buffered_value()
        for b in getBuffer:
            yield b

    def auto_filter_mode(self):
        return self.digiTest.get_suitable_mode()

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
        

def parse_download_data(data):
    start_byte = 0
    dataset = {}
    # sample no
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['Sample-Counter']= parsing_data
    start_byte += byteSize
    print('Sample-Counter {}'.format(parsing_data))
    # Operator
    byteSize = 32
    endBytes = start_byte+byteSize
    parsing_data = string_onlyPrintable(data[start_byte:endBytes].decode("utf-8"))
    dataset['Operator']= parsing_data
    start_byte += byteSize
    print('Operator {}'.format(parsing_data))
    # Compound folder
    byteSize = 32
    endBytes = start_byte+byteSize
    parsing_data = string_onlyPrintable(data[start_byte:endBytes].decode("utf-8"))
    dataset['Compound_Folder']= parsing_data
    start_byte += byteSize
    print('Compound_Folder {}'.format(parsing_data))
    # Compound
    byteSize = 32
    endBytes = start_byte+byteSize
    parsing_data = string_onlyPrintable(data[start_byte:endBytes].decode("utf-8"))
    dataset['Compound']= parsing_data
    start_byte += byteSize
    print('Compound {}'.format(parsing_data))
    # Batch
    byteSize = 32
    endBytes = start_byte+byteSize
    parsing_data = string_onlyPrintable(data[start_byte:endBytes].decode("utf-8"))
    dataset['Batch']= parsing_data
    start_byte += byteSize
    print('Batch {}'.format(parsing_data))
    # Productiondate
    byteSize = 12
    endBytes = start_byte+byteSize
    parsing_data = string_onlyPrintable(data[start_byte:endBytes].decode("utf-8"))
    dataset['Productiondate']= parsing_data
    start_byte += byteSize
    print('Productiondate {}'.format(parsing_data))
    # Hardness_1
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['Hardness_1']= parsing_data
    start_byte += byteSize
    print('Hardness_1 {}'.format(parsing_data))
    # Hardness_2
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['Hardness_2']= parsing_data
    start_byte += byteSize
    print('Hardness_2 {}'.format(parsing_data))
    # Hardness_3
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['Hardness_3']= parsing_data
    start_byte += byteSize
    print('Hardness_3 {}'.format(parsing_data))
    # Timestamp
    byteSize = 12
    endBytes = start_byte+byteSize
    decode_data = data[start_byte:endBytes]
    year = struct.unpack(">H", decode_data[0:2])[0]
    month = struct.unpack(">b", decode_data[2:3])[0]
    day = struct.unpack(">b", decode_data[3:4])[0]
    hour = struct.unpack(">b", decode_data[5:6])[0]
    mintue = struct.unpack(">b", decode_data[6:7])[0]
    second = struct.unpack(">b", decode_data[7:8])[0]
    fract = struct.unpack(">I", decode_data[8:12])[0]
    dataset['Timestamp']= 'DTL#{:04d}-{:02d}-{:02d}-{:02d}:{:02d}:{:02d},{:09d}'.format(year,month,day,hour,mintue,second,fract) # DTL#2019-05-21-16:50:26,126643000
    start_byte += byteSize
    print('Timestamp {}'.format('DTL#{:04d}-{:02d}-{:02d}-{:02d}:{:02d}:{:02d},{:09d}'.format(year,month,day,hour,mintue,second,fract)))
    # T_sample
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['T_sample']= parsing_data
    start_byte += byteSize
    print('T_sample {}'.format(parsing_data))
    # AreaTemp
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    # dataset['AreaTemp']= parsing_data
    start_byte += byteSize
    print('AreaTemp {}'.format(parsing_data))
    # AirHumidity
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    # dataset['AirHumidity']= parsing_data
    start_byte += byteSize
    print('AirHumidity {}'.format(parsing_data))
    # WeightDry
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['WeightDry']= parsing_data
    start_byte += byteSize
    print('WeightDry {}'.format(parsing_data))
    # WeightWet
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['WeightWet']= parsing_data
    start_byte += byteSize
    print('WeightWet {}'.format(parsing_data))
    # T_Liquid
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['T_Liquid']= parsing_data
    start_byte += byteSize
    print('T_Liquid {}'.format(parsing_data))
    # Density
    byteSize = 8
    endBytes = start_byte+byteSize
    parsing_data = struct.unpack('>d', data[start_byte:endBytes])[0]
    dataset['Density']= parsing_data
    start_byte += byteSize
    print('Density {}'.format(parsing_data))

    return dataset

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