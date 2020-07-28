import pyodbc
import traceback
import csv

class DB():
    def __init__(self, server_name, username="",password=""):
        self.server_name = server_name
        self.username = username
        self.password = password
        self.coxn = None
        self.connected = False
        self.cursor = None
    
    def connect(self, db_name):
        """ Connection String should be: 'DRIVER={ODBC Driver 13 for SQL Server};
        SERVER=SHAWNNB\SQLEXPRESS;DATABASE=HDA150;UID=BareissAdmin;PWD=BaAdmin'  """

        try:
            conn_str = r"DRIVER={ODBC Driver 11 for SQL Server};SERVER="+ self.server_name + ";DATABASE="+db_name+";UID="+ self.username+";PWD="+self.password+""
            self.coxn = pyodbc.connect(conn_str)
            self.cursor = self.coxn.cursor()
            self.connected = True
        except:
            error_msg = traceback.format_exc()
            print(error_msg)
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
        exe_str = r"DROP TABLE {}".format(table)
        self.cursor.execute(exe_str) 
        self.coxn.commit()

    def select(self, table, fields="*", condition="", types=[]):
        """Sample select query"""
        fileds_str = ','.join(map(str, fields))
        exe_str = r"SELECT {} FROM {} {}".format(fileds_str, table, condition)
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
        para_str = ','.join(map(str, '?'*len(data)))
        exe_str = r"""INSERT INTO {} ({}) VALUES ({})""".format(table, fileds_str, para_str)
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
        exe_str = r"""UPDATE {} SET {} {}""".format(table, data_str, condition)
        self.cursor.execute(exe_str, data)
        self.coxn.commit()
    
    def delete(self, table, condition):
        '''DELETE FROM Table_Name WHERE condition'''
        exe_str = r"DELETE FROM {} {}".format(table, condition)
        self.cursor.execute(exe_str)
        self.coxn.commit()

    def execute(self, sql):
        exe_str = sql
        self.cursor.execute(exe_str)
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

def read_csv(filepath):
    with open(filepath, newline='') as csvfile:
        contents = csv.reader(csvfile, delimiter=',')
        lines = []
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

def bulkInsert(db, tablename, fields, dataList, datatype, fromIndex=0):
    print('\nstart insert or update data to table {}'.format(tablename)) 
    insertCounter = 0
    updateCounter = 0
    for r in dataList:
        valueList = r[fromIndex:]
        fmtValue = valueFormatter(valueList, datatype)
        condition = makeCondition(fields, fmtValue)
        print(condition)
        ret = db.select(tablename, fields, condition)
        if len(ret)==0:
            db.insert(tablename,fields, valueList)
            insertCounter += 1
        else:
            db.update(tablename,fields, valueList,condition)
            updateCounter += 1

    print('{} of rows inserted'.format(insertCounter)) 
    print('{} of rows updated'.format(updateCounter)) 

def insertFunctionList(db):
    allContents = read_csv(r'.\functionlist_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string', 'int', 'int']
    bulkInsert(db,'FunctionList',['Functions','Tree_index','Display_order'], onlyContents, datatype, 1)

def insertUserList(db):
    allContents = read_csv(r'.\user_list_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string','string','string','string','string', 'int', 'int']
    bulkInsert(db,'UserList',['User_Name','PW','User_Role', 'Creation_Date', 'Expired_Date','Status', 'First_login'], onlyContents, datatype, 1 )

def insertUserRoleList(db):
    allContents = read_csv(r'.\user_role_list_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string', 'int']
    bulkInsert(db,'UserRoleList',['User_Role', 'User_Level'], onlyContents, datatype, 1 )

def insertUserPermissionList(db):
    allContents = read_csv(r'.\user_permission_default.csv')
    onlyContents = allContents[1:]
    datatype = ['string', 'string','int', 'int']
    bulkInsert(db,'UserPermission',['User_Role', 'Functions', 'Enabled', 'Visibled'], onlyContents, datatype, 1 )



def main():
    db = DB(r"(localDB)\BareissLocalDB", 'BareissAdmin', 'BaAdmin')
    ok = db.connect('DigiChamber')
    print('connection status: {}'.format(ok))
    if ok:
        # insert Function List
        insertFunctionList(db)     
        # insert user_list_default
        insertUserList(db)
        # insert user role list
        insertUserRoleList(db)
        # insert user permission list
        insertUserPermissionList(db)

        db.close()


if __name__=="__main__":
    main()