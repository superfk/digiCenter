#!/usr/bin/python
# -*- coding: UTF-8 -*-

import sys, os, traceback
import time

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
DB_DIR = SCRIPT_DIR
indentLevel = 2
for i in range(indentLevel):
    DB_DIR = os.path.split(DB_DIR)[0]
sys.path.append(os.path.normpath(os.path.join(PACKAGE_PARENT,SCRIPT_DIR)))
sys.path.append(os.path.normpath(DB_DIR))

import pyodbc
import datetime
import calendar
import corelib.utility as util
 
class DB():
    def __init__(self, server_name, username="",password=""):
        self.server_name = server_name
        self.username = username
        self.password = password
        self.coxn = None
        self.connected = False
        self.cursor = None
        self.db_name = ''
    
    def connect(self, db_name, autoCommitInConnection=False):
        """ Connection String should be: 'DRIVER={ODBC Driver 13 for SQL Server};
        SERVER=SHAWNNB\SQLEXPRESS;DATABASE=HDA150;UID=BareissAdmin;PWD=BaAdmin'  """
        try:
            self.db_name = db_name
            conn_str = r"DRIVER={ODBC Driver 11 for SQL Server};SERVER="+ self.server_name + ";DATABASE="+db_name+";UID="+ self.username+";PWD="+self.password+""
            self.coxn = pyodbc.connect(conn_str, autocommit = autoCommitInConnection)
            self.coxn.autocommit = True
            self.cursor = self.coxn.cursor()
            self.connected = True
        except:
            err_msg = traceback.format_exc()
            print(err_msg)
            self.connected = False
        return self.connected
    
    def backup(self, destFolder):
        conn_str = r"DRIVER={ODBC Driver 11 for SQL Server};SERVER="+ self.server_name + ";DATABASE=master"+";UID="+ self.username+";PWD="+self.password+""
        coxn = pyodbc.connect(conn_str, autocommit = True)
        cursor = coxn.cursor()
        destPath = os.path.join(destFolder, f'{self.db_name}.bak')
        exe_str = f'''
        BACKUP DATABASE [{self.db_name}] TO DISK = N'{destPath}'
        WITH NOFORMAT, INIT,  NAME = N'{self.db_name}-Full Database Backup', SKIP, NOREWIND, NOUNLOAD,  STATS = 10
        '''
        cursor.execute(exe_str)
        while cursor.nextset():
            pass
        cursor.close()
        coxn.close()
        return True

    def restore(self, destFolder):
        try:
            self.close()
        except:
            pass
        finally:
            conn_str = r"DRIVER={ODBC Driver 11 for SQL Server};SERVER="+ self.server_name + ";DATABASE=master"+";UID="+ self.username+";PWD="+self.password+""
            coxn = pyodbc.connect(conn_str, autocommit = True)
            cursor = coxn.cursor()
            destPath = os.path.join(destFolder, f'{self.db_name}.bak')
            exe_str = f'''
            ALTER DATABASE [{self.db_name}]
            SET SINGLE_USER
            WITH ROLLBACK IMMEDIATE

            RESTORE DATABASE [{self.db_name}] FROM DISK = N'{destPath}' WITH REPLACE, RECOVERY 

            ALTER DATABASE [{self.db_name}] SET MULTI_USER
            '''
            cursor.execute(exe_str)
            while cursor.nextset():
                pass
            cursor.close()
            coxn.close()
        try:
            for i in range(5):
                print(f'retry to connect to db after restore database: retry {i+1}')
                success = self.connect(self.db_name, True)
                if success:
                    return success
                else:
                    time.sleep(1)
        except:
            return False
    
    def create_table(self, table, fields, types, primary_field=""):
        '''CREATE TABLE TestTable(symbol varchar(15), leverage double, shares integer, price double)'''
        pairs = []
        for f, typ in zip(fields, types):
            if primary_field == f:
                pairs.append(r"{} {} IDENTITY(1,1) PRIMARY KEY".format(f,typ))
            else:
                pairs.append(r"{} {}".format(f,typ))
        data_str = ','.join(map(str, pairs))
        print(data_str)
        exe_str = r"CREATE TABLE {}({});".format(table, data_str)
        self.cursor.execute(exe_str) 
        self.coxn.commit()

    def drop_table(self, table):
        '''DROP TABLE table'''
        exe_str = r"DROP TABLE {};".format(table)
        self.cursor.execute(exe_str) 
        self.coxn.commit()

    def select(self, table, fields="*", condition="", types=[]):
        """Sample select query"""
        fileds_str = ','.join(map(str, fields))
        exe_str = r"SELECT {} FROM {} {};".format(fileds_str, table, condition)
        # get columns type in this query table
        col = dict()
        cols = self.cursor.columns(table=table)
        fds = []
        for c in cols:
            fds.append(c.column_name)
            if c.column_name in fields or fields == "*":
                col[c.column_name] = c.type_name

        self.cursor.execute(exe_str) 
        rows =self.cursor.fetchall()

        fmt_all_row = []
        for row in rows:
            fmt_single_row = {}
            for j, r in enumerate(row):
                col_name = fields[j]
                col_type = col[col_name]
                if col_type == 'datetime2':
                    fmt_single_row[col_name] = r.strftime(r"%Y/%m/%d %H:%M:%S.%f")
                else:
                    fmt_single_row[col_name] = r
            fmt_all_row.append(fmt_single_row)
            
        #final_result = [json.dumps(dict(zip(fields,row)), default=str) for row in rows]
        
        return fmt_all_row

    def insert(self, table, fields, data):
        '''Sample insert query'''
        fileds_str = ','.join(map(str, fields))
        # values = ["'{}'".format(x) if type(x) is str else x for x in data]
        # data_str = ','.join(map(str, values))
        para_str = ','.join(map(str, '?'*len(data)))
        # print(data_str)
        exe_str = r"""INSERT INTO {} ({}) VALUES ({});""".format(table, fileds_str, para_str)
        # "insert into products(id, name) values (?, ?)", 'pyodbc', 'awesome library'
        self.cursor.execute(exe_str, data)
        self.coxn.commit()
    
    def update(self, table, fields, data, condition):
        '''UPDATE Table_Name SET Column1_Name = value1, Column2_Name = value2 WHERE condition'''
        values = ["'{}'".format(x) if type(x) is str else x for x in data]
        pairs = []
        for col in fields:
            pairs.append("{}=?".format(col))
        data_str = ','.join(map(str, pairs))
        exe_str = r"""UPDATE {} SET {} {};""".format(table, data_str, condition)
        self.cursor.execute(exe_str, data)
        self.coxn.commit()
    
    def delete(self, table, condition):
        '''DELETE FROM Table_Name WHERE condition'''
        exe_str = r"DELETE FROM {} {};".format(table, condition)
        self.cursor.execute(exe_str)
        self.coxn.commit()

    def execute(self, sql):
        exe_str = sql
        self.cursor.execute(exe_str+";")
        rows =self.cursor.fetchall()
        self.coxn.commit()
        fmt_all_row = []
        for row in rows:
            fmt_all_row.append([x for x in row])
        return fmt_all_row
    
    def close(self):
        self.cursor.close()
        self.coxn.close()
    
    def get_fields(self, table):
        exe_str = r"SELECT * FROM {} WHERE 1=0;".format(table)
        self.cursor.execute(exe_str)
        fields=[]
        for row in self.cursor.columns(table=table):
            fields.append(row.column_name)
        return fields


def create_data_table():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    fields = ["ID", "Recordtime","Sample_Counter", "Operator", "Compound_Folder", "Compound", "Batch", "Productiondate", "Hardness_1", "Hardness_2", "Hardness_3", "Timestamp",
                "T_sample", "WeightDry", "WeightWet", "T_Liquid", "Density"]
    types = ["int", "datetime2", "float", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(255)", "float", "float", "float", "datetime2",
            "float", "float", "float", "float", "float"]
    db.create_table("Test_Data", fields, types, "ID")
    db.close()

def create_syslog_table():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    fields = ["ID", "Timestamp", "User_Name", "User_Role", "Log_Type", "Log_Message", "Audit"]
    types = ["int", "datetime2", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(2048)", "bit"]
    db.create_table("System_log", fields, types, "ID")
    db.close()

def create_user_role_list_table():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    fields = ["ID", "User_Role", "User_Level"]
    types = ["int", "varchar(255)", "tinyint"]
    db.create_table("UserRoleList", fields, types, "ID")
    fields = ["User_Role", "User_Level"]
    data = ["System_Admin", 255 ]
    db.insert("UserRoleList",fields,data)
    db.close()

def create_userlist_table():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    fields = ["ID", "User_Name", "PW", "User_Role", "Creation_Date", "Expired_Date", "Status"]
    types = ["int", "varchar(255)", "varchar(255)" , "varchar(255)", "datetime2", "datetime2", "tinyint"]
    db.create_table("UserList", fields, types, "ID")
    fields = ["User_Name", "PW", "User_Role", "Creation_Date", "Expired_Date", "Status", "First_login"]
    tday = datetime.datetime.now()
    exp_date = add_months(tday, 12)
    # 2019/08/29 18:56:00.564205
    creat_time = tday.strftime(r"%Y/%m/%d %H:%M:%S.000000")
    exp_time = exp_date.strftime(r"%Y/%m/%d %H:%M:%S.000000")
    pw = util.encrypt_password("BaAdmin")
    data = ["BareissAdmin", pw, "System_Admin", creat_time, exp_time, 1 , 0]
    db.insert("UserList",fields,data)
    db.close()

def create_permission_table():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    fields = ["ID", "User_Role", "Functions", "Enabled", "Visibled"]
    types = ["int", "varchar(255)", "varchar(255)", "bit", "bit"]
    db.create_table("UserPermission", fields, types, "ID")

    fields = ["User_Role", "Functions", "Enabled", "Visibled"]
    fn_list = ["button-dataEx-upload", "button-dataEx-download", "button-report", "button-analysis", "download-data-from-plc",
    "download-data-from-file", "save-test-data-to-db", "upload-data-new", "upload-data-import", "send-batch-to-machine", "export-test-data-to-file"]
    for f in fn_list:
        data = ["System_Admin", f, 1, 1 ]
        db.insert("UserPermission",fields,data)
    en = [0,0,0,0,0,0,0,0,0,0,0]
    vis = [1,1,1,1,0,0,0,0,0,0,0] 
    for f, e, v in zip(fn_list, en, vis):
        data = ["Guest", f, e, v]
        db.insert("UserPermission",fields,data)
    db.close()

def create_funclist_table():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    fields = ["ID", "Functions", "Tree_index", "Display_order"]
    types = ["int", "varchar(255)", "tinyint", "smallint"]
    db.create_table("FunctionList", fields, types, "ID")

    fields = ["Functions", "Tree_index", "Display_order"]
    fn_list = ["button-dataEx-upload", "button-dataEx-download", "button-report", "button-analysis", "download-data-from-plc",
    "download-data-from-file", "save-test-data-to-db", "upload-data-new", "upload-data-import", "send-batch-to-machine", "export-test-data-to-file"]
    tree_idx = [0,0,0,0,1,1,1,1,1,1,1]
    disp_order = [0,4,8,10,5,6,7,1,2,3,9]

    for f, t, d in zip(fn_list, tree_idx, disp_order):
        data = [f, t, d]
        db.insert("FunctionList",fields,data)   
    db.close()

def add_new_function_to_all_user(funcs_value_list):
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    db.connect("HDA150")
    
    fnc = funcs_value_list[0]
    tree = funcs_value_list[1]
    disp = funcs_value_list[2]
    disp_name = funcs_value_list[3]

    # get all users
    fields = ["Functions"]
    condition = r"WHERE Functions = '{}'".format(fnc)
    anyFuncs = db.select('FunctionList', fields, condition)
    if len(anyFuncs)==0:
        fields = ["Functions", "Tree_index", "Display_order", 'Display_fnc_name']
        data = [fnc, tree, disp, disp_name]
        ret = db.insert("FunctionList",fields,data)
    else:
        print('Functions {} is already in Function List'.format(fnc))
        print('')
    

    # get all users
    fields = ["User_Role"]
    condition = r"GROUP BY User_Role"
    user_roles = db.select('UserPermission', fields, condition)
   
    for ur in user_roles:
        # check function exsist
        fields = ["Functions"]
        condition = '''
        WHERE EXISTS (SELECT Functions 
        FROM UserPermission WHERE Functions = '{}') AND User_Role='{}'
        '''.format(fnc, ur['User_Role'])
        anyFuncs = db.select('UserPermission', fields, condition)
        
        if len(anyFuncs) == 0:

            enab = 0
            if ur['User_Role'] == 'System_Admin':
                enab = 1
            fields = ["User_Role", "Functions", "Enabled", 'Visibled']
            data = [ur['User_Role'], fnc, enab, 1]
            ret = db.insert("UserPermission",fields,data)
        else:
            print('Functions {} is already in this User Role {}'.format(fnc, ur['User_Role']))
            print('')
        
    db.close()
        


def unit_test():
    db = DB(r"SHAWNNB\SQLEXPRESS", r"BareissAdmin", r"BaAdmin")
    connected = db.connect("HDA150")
    print(connected)
    

    try:
        data = db.select("unit_test")
        db.drop_table("unit_test")
    except:
        print("table not exist")
    finally:
        fields = ["ID", "Sample_Counter", "Operator", "Compound_Folder", "Compound", "Batch", "Productiondate", "Hardness_1", "Hardness_2", "Hardness_3", "Timestamp",
                "T_sample", "WeightDry", "WeightWet", "T_Liquid", "Density"]
        types = ["int", "int", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(255)", "varchar(255)", "float", "float", "float", "datetime2",
                "float", "float", "float", "float", "float"]
        db.create_table("unit_test", fields, types, "ID")

    data = db.select("unit_test")
    print(data)

    fields = ["Sample_Counter", "Batch", "Hardness_1", "Timestamp"]
    values = [1, "batch1", 0.111, "2019/08/29 18:56:00.564205"]
    db.insert("unit_test",fields,values)
    fields = ["Sample_Counter", "Batch", "Hardness_1", "Timestamp"]
    values = [2, "batch2", 0.221, "2019/09/29 18:56:00.564205"]
    db.insert("unit_test",fields,values)
    print(data)

    data = db.select("unit_test")
    print(data)

    fields = ["Sample_Counter", "Batch", "Hardness_1", "Timestamp"]
    values = [3, "batch3", 0.331, "2019/10/29 18:56:00.564205"]
    condition = "WHERE Sample_Counter=1"
    db.update("unit_test",fields,values,condition)
    data = db.select("unit_test")
    print(data)

    condition = "WHERE Sample_Counter=3"
    db.delete("unit_test",condition)
    data = db.select("unit_test")
    print(data)

    fields= db.get_fields("unit_test")
    print(fields)

    db.close()

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    hour = sourcedate.hour
    minutes = sourcedate.minute
    seconds = sourcedate.second
    return datetime.datetime(year, month, day, hour,minutes, seconds)

def test_restore():
    db = DB(r"(localDB)\BareissLocalDB", r"BareissAdmin", r"BaAdmin")
    print(id(db))
    db.connect("DigiChamber")
    db.backup(r"C:\data_exports\backup")
    success = db.restore(r"C:\data_exports\backup")
    print(f"database backup and recovery test: {success}")
    
    # db = DB(r"(localDB)\BareissLocalDB", r"BareissAdmin", r"BaAdmin")
    # ret = db.connect("DigiChamber", True)
    print(f"database connected?: {db.connected}")
    db.close()

if __name__=="__main__":
    test_restore()