import pyodbc
import traceback
import csv
from cryptography.fernet import Fernet
import pkgutil
import datetime
import csv_files

def progressBar(iterable, prefix='', suffix='', decimals=1, length=100, fill='█', printEnd="\r"):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    total = len(iterable)
    # Progress Bar Printing Function

    def printProgressBar(iteration):
        percent = ("{0:." + str(decimals) + "f}").format(100 *
                                                         (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end=printEnd)
    # Initial Call
    printProgressBar(0)
    # Update Progress Bar
    for i, item in enumerate(iterable):
        yield item
        printProgressBar(i + 1)
    # Print New Line on Complete
    print()

class DB():
    def __init__(self, server_name, dbName, username="",password=""):
        self.server_name = server_name
        self.db_name = dbName
        self.username = username
        self.password = password
        self.coxn = None
        self.connected = False
        self.cursor = None
    
    def connect(self):
        """ Connection String should be: 'DRIVER={ODBC Driver 13 for SQL Server};
        SERVER=SHAWNNB\SQLEXPRESS;DATABASE=HDA150;UID=BareissAdmin;PWD=BaAdmin'  """
        try:
            conn_str = r"DRIVER={ODBC Driver 11 for SQL Server};SERVER="+ self.server_name + ";DATABASE="+self.db_name+";UID="+ self.username+";PWD="+self.password+""
            self.coxn = pyodbc.connect(conn_str)
            self.coxn.autocommit = True
            self.cursor = self.coxn.cursor()
            self.connected = True
        except:
            self.connected = False
        return self.connected
    
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
        exe_str = r"CREATE TABLE {}({})".format(table, data_str)
        self.cursor.execute(exe_str) 
        self.coxn.commit()

    def drop_table(self, table):
        '''DROP TABLE table'''
        exe_str = r"DROP TABLE {};".format(table)
        self.cursor.execute(exe_str) 
        self.coxn.commit()

    def select(self, table, fields="*", condition=""):
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
        self.coxn.commit()
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

    def execute(self, sql, data=None, to_dict=False, dict_field=[], autoDateToString=False):
        '''return empty list if no result'''
        exe_str = sql
        if exe_str[-1] != ';':
            exe_str = exe_str+';'

        if data:
            self.cursor.execute(exe_str,data)
        else:
            self.cursor.execute(exe_str)
        try:
            rows =self.cursor.fetchall()
        except:
            rows = None
        self.coxn.commit()
        fmt_all_row = []
        if rows:
            for row in rows:
                if to_dict:
                    single_row_dict = {}
                    for k,v in zip(dict_field,row):
                        if autoDateToString and type(v) is datetime.datetime:
                            v = v.strftime('%Y-%m-%d %H:%M:%S')
                        single_row_dict[k] = v
                    fmt_all_row.append(single_row_dict)
                else:
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

def read_csv(filepath):
    help_bin = pkgutil.get_data( 'csv_files', filepath )
    csvContents = help_bin.decode('UTF-8', 'ignore')
    lines = []
    csvLines = csvContents.splitlines()
    contents = csv.reader(csvLines, delimiter=',')
    for row in contents:
        lines.append(row)
    return lines

def valueFormatter(valueList, formatList):
    fmtValues = []
    for i,v in enumerate(valueList):
        fmt = formatList[i]
        if fmt == 'int':
            value = int(v)
        elif fmt == 'float':
            value = float(v)
        else:
            value = v
        fmtValues.append(value)
    return fmtValues

def makeCondition(conditionFields,valueList):
    values = ["'{}'".format(x) if type(x) is str else x for x in valueList]
    conditions = [ col + "=" + str(val) for col,val in zip(conditionFields,values)]
    conditions = " AND ".join(conditions)
    conditionStr = "WHERE " + conditions
    return conditionStr

def bulkInsert(db, tablename, fields, dataList, datatype, fromIndex=0, conditionFields=[], debug=False):
    # tablename = tablename.lower()
    # fields = [x.lower() for x in fields]
    print('\nstart insert or update data to table {}'.format(tablename))
    insertCounter = 0
    updateCounter = 0
    for r in progressBar(dataList, prefix='Progress:', suffix='Complete', length=50):
        valueList = r[fromIndex:]
        fmtValue = valueFormatter(valueList, datatype)
        condition = makeCondition(fields, fmtValue)
        if len(conditionFields) > 0:
            condValues = []
            for f, v in zip(fields, fmtValue):
                if f in conditionFields:
                    condValues.append(v)
            serchCondition = makeCondition(conditionFields, condValues)
        else:
            serchCondition = condition
        if debug:
            print('')
            print(f'fields: {fields}')
            print(f'fmtValue: {fmtValue}')
            print(f'serchCondition: {serchCondition}')

        ret = db.select(tablename, fields, serchCondition)
        if len(ret) == 0:
            try:
                db.insert(tablename, fields, fmtValue)
                insertCounter += 1
            except Exception as e:
                print(e)
        else:
            try:
                db.update(tablename, fields, fmtValue, serchCondition)
                updateCounter += 1
            except Exception as e:
                print(e)
    return insertCounter, updateCounter

def insertFunctionList(db):
    allContents = read_csv(r'functionlist_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string', 'int', 'int']
    return bulkInsert(db,'FunctionList',['Functions','Tree_index','Display_order'], onlyContents, datatype, 1)

def insertUserList(db):
    allContents = read_csv(r'user_list_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string','string','string','string','string', 'int', 'int']
    return bulkInsert(db,'UserList',['User_Name','PW','User_Role', 'Creation_Date', 'Expired_Date','Status', 'First_login'], onlyContents, datatype, 1 )

def insertUserRoleList(db):
    allContents = read_csv(r'user_role_list_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string', 'int']
    return bulkInsert(db,'UserRoleList',['User_Role', 'User_Level'], onlyContents, datatype, 1 )

def insertUserPermissionList(db):
    allContents = read_csv(r'user_permission_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string', 'string','int', 'int']
    return bulkInsert(db,'UserPermission',['User_Role', 'Functions', 'Enabled', 'Visibled'], onlyContents, datatype, 1 )

def encrypt_password(pw):
    key = b'mASnZzVxJLLGLIe1H_y_tzl2cu7wzUf7l091-4SPTBo='
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(bytes(pw, 'utf-8')).decode("utf-8") 
    return cipher_text

def main():
    # for SQL Server
    db = DB(r"(localDB)\BareissLocalDB", "DigiChamber", 'BareissAdmin', 'BaAdmin')
    ok = db.connect()

    print('connection status: {}'.format(ok))
    if ok:
        funcs = [
            insertFunctionList,
            insertUserList,
            insertUserRoleList,
            insertUserPermissionList
        ]
        totalInsert = 0
        totalUpdate = 0
        for f in funcs:
            inserted, updated = f(db)
            totalInsert += inserted
            totalUpdate += updated

        print('')
        print('[Completed Insert Default Values]')
        print('{} of rows inserted'.format(totalInsert))
        print('{} of rows updated'.format(totalUpdate))

    db.close()
        


if __name__=="__main__":
    main()