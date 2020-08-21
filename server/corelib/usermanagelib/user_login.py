import datetime
from corelib.utility import utility as util
import os

class User(object):
    def __init__(self, username="", role="", level=0, enabled=False):
        self.username = username
        self.role = role
        self.level = level
        self.create_date = ""
        self.exp_date = ""
        self.enabled = enabled
        self.lang_data = None

class UserManag(object):
    def __init__(self,dbinstance, username="", role="", level=0, enabled=False):
        self.db = dbinstance
        self.user = User("Guest", "Guest", level=0, enabled=True)
        self.pw_export_folder = None
        self.lang = None
        self.lang_key = 'en'
        self.log_to_db_func = None
    
    def set_lang(self, lang_data, lang_key):
        self.lang = lang_data
        self.lang_key = lang_key
    
    def set_log_to_db_func(self, logDBFunc):
        self.log_to_db_func = logDBFunc
        
    
    def savelog(self,msg, msg_type='info', audit=False):
        try:
            self.log_to_db_func(msg, msg_type, audit)
        except Exception as e:
            print('save log error in user management mudole')
    
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
            reason = self.lang['server_pls_keyin_username']
            role = ""
            user = ''
            self.savelog(reason)
            return login_ok, reason, user, role, fn_list
        if password == "" and username != "Guest":
            # password is empty
            login_ok = False
            reason = self.lang['server_pls_keyin_pw']
            role = ""
            user = ''
            self.savelog(reason)
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
                reason = self.lang['server_user_not_active']
                role = ""
                user = ''
                self.savelog(reason)
                return login_ok, reason, user, role, fn_list, first
            if exp_date < now:
                # user expired
                f = ["Status"]
                condition = r"WHERE User_Name='{}'".format(username)
                self.db.update('UserList', f, [0], condition)
                login_ok = False
                reason = self.lang['server_user_expired']
                role = ""
                user = ''
                self.savelog(reason)
                return login_ok, reason, user, role, fn_list, first
            if password != d_pw and username != 'Guest':
                # user password not correct
                login_ok = False
                reason = self.lang['server_pw_not_correct']
                role = ""
                user = ''
                self.savelog(reason)
                return login_ok, reason, user, role, fn_list, first
            if result['First_login']:
                # user first login, need to change pw
                login_ok = False
                reason = self.lang['server_first_login_change_pw']
                role = ""
                user = ''
                first = True
                self.savelog(reason,audit=True)
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
                reason = self.lang['server_login_ok'] if username != "Guest" else "Guest login"
                role = result["User_Role"]
                user = username
                self.user = User(username, role, role_level, login_ok)
                self.savelog(reason,audit=True)
                return login_ok, reason, user, role, fn_list, first
        else:
            # user not found
            login_ok = False
            reason = self.lang['server_user_not_found'].format(username)
            role = ''
            user = ''
            self.savelog(reason)
            return login_ok, reason, user, role, fn_list, first

    def log_out(self):
        fn_list=list()
        user = self.lang['head_login_username']
        role = 'Guest'
        first=False
        self.user = User(user, role, level=0, enabled=True)
        # Guest login ok
        f = ["User_Level"]
        condition = r"WHERE User_Role='{}'".format(role)
        role_level = self.db.select('UserRoleList',f, condition)[0]["User_Level"]
        f = ["Functions", "Enabled", "Visibled"]
        condition = r"WHERE User_Role='{}'".format(role)
        query = self.db.select('UserPermission',f, condition)
        for q in query:
            fn={}
            fn['function']=q['Functions']
            fn['enable']=q['Enabled']
            fn['visible']=q['Visibled']
            fn_list.append(fn)
        login_ok = False
        reason = "Guest logout"
        self.savelog(reason,audit=True)
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
    
    def add_new_user(self,userID, role, pw_export_folder=None):
        # check if this user exsisted
        fields = ['User_Name']
        condition = r"WHERE User_Name = '{}'".format(userID)
        user_lists = self.db.select('UserList',fields, condition)
        if len(user_lists) > 0:
            return 0, self.lang['server_user_exist'], ''
        # check if this role exsisted
        fields = ["User_Role"]
        condition = r" WHERE User_Role = '{}'".format(role)
        user_role = self.db.select('UserRoleList', fields, condition)
        if len(user_role) == 0:
            return 0, self.lang['server_user_assign_role'], ''
        
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
            if pw_export_folder:
                folder_path = os.path.join(pw_export_folder, 'first_pw')
                util.save_password_to_json(folder_path, userID, role, rnd_pw)
            self.savelog(self.lang['server_user_add_ok'],audit=True)
            return 1, self.lang['server_user_add_ok'], rnd_pw
        except Exception as e:
            self.savelog(self.lang['server_user_add_error'])
            return 0, self.lang['server_user_add_error'].format(e), ''
        
    def delete_user(self, userID):
        if userID == 'Guest':
            self.savelog(self.lang['server_guest_not_delete'])
            return 0, self.lang['server_guest_not_delete']
        if userID == 'BareissAdmin':
            self.savelog(self.lang['server_superuser_not_delete'])
            return 0, self.lang['server_superuser_not_delete']
        if userID == '':
            self.savelog(self.lang['server_select_one_user'])
            return 0, self.lang['server_select_one_user']
        if userID == self.user.username:
            self.savelog(self.lang['server_cannot_delete_self'])
            return 0, self.lang['server_cannot_delete_self']
        condition = r"WHERE User_Name = '{}'".format(userID)
        try:
            fields = ["Status"]
            self.db.update("UserList", fields,[2],condition)
            self.savelog(self.lang['server_user_delete_ok'], audit=True)
            return 1, self.lang['server_user_delete_ok']
        except Exception as e:
            self.savelog('Error: deleting user error ({})'.format(e))
            return 0, 'Error: deleting user error ({})'.format(e)

    def activate_user(self, userID):
        if userID == 'Guest':
            self.savelog(self.lang['server_guest_aws_active'])
            return 0, self.lang['server_guest_aws_active']
        if userID == 'BareissAdmin':
            self.savelog(self.lang['server_superuuser_aws_active'])
            return 0, self.lang['server_superuuser_aws_active']
        if userID == '':
            self.savelog(self.lang['server_select_one_user'])
            return 0, self.lang['server_select_one_user']
        fields = ["Status"]
        condition = r" WHERE User_Name = '{}' AND Status < 2".format(userID)
        try:
            self.db.update("UserList", fields,[1],condition)
            self.savelog(self.lang['server_user_active_ok'], audit=True)
            return 1, self.lang['server_user_active_ok']
        except Exception as e:
            self.savelog('Error: activating user error ({})'.format(e))
            return 0, 'Error: activating user error ({})'.format(e)
    
    def deactivate_user(self, userID):
        if userID == 'Guest':
            self.savelog(self.lang['server_guest_not_deactive'])
            return 0, self.lang['server_guest_not_deactive']
        if userID == 'BareissAdmin':
            self.savelog(self.lang['server_superuser_not_deactive'])
            return 0, self.lang['server_superuser_not_deactive']
        if userID == '':
            self.savelog(self.lang['server_select_one_user'])
            return 0, self.lang['server_select_one_user']
        fields = ["Status"]
        condition = r" WHERE User_Name = '{}' AND Status < 2".format(userID)
        try:
            self.db.update("UserList", fields,[0],condition)
            self.savelog(self.lang['server_user_deactive_ok'], audit=True)
            return 1, self.lang['server_user_deactive_ok']
        except Exception as e:
            return 0, 'Error: deactivating user error ({})'.format(e)

    def give_new_password(self, userID, role, pw_export_folder=None):
        if userID == 'Guest':
            return 0, self.lang['server_guest_no_pw'],""
        if userID == 'BareissAdmin':
            return 0, self.lang['server_superuser_no_pw'],""
        if userID == '':
            return 0, self.lang['server_select_one_user'],""

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
            exp_json = {}
            exp_json['pw']= rnd_pw
            exp_json['role']= role
            exp_json['userID']= userID
            if pw_export_folder:
                folder_path = os.path.join(pw_export_folder, 'first_pw')
                util.save_password_to_json(folder_path, userID, role, rnd_pw)
            self.savelog(self.lang['server_user_rest_pw_ok'], audit=True)
            return 1, self.lang['server_user_rest_pw_ok'], exp_json
        except Exception as e:
            self.savelog('Error: ({})'.format(e))
            return 0, 'Error: ({})'.format(e),""
    
    def get_user_role_list(self):
        f = ["User_Role", "User_Level"]
        condition = r" WHERE User_Level < 255 ORDER BY User_Level DESC"
        user_role = self.db.select('UserRoleList',f, condition)
        return user_role
    
    def get_function_list(self, userrole='Guest'):
        # f = ["Functions", "Enabled", "Visibled"]
        # condition = r" INNER JOIN [FunctionList] ON [UserPermission].Functions=[FunctionList].Functions WHERE [User_Role]='{}' ORDER BY [FunctionList].[Display_order]".format(userrole)
        # fn_list = self.db.select('UserRoleList',f, condition)
        exe_str = """
        SELECT FunctionList.Display_order, UserPermission.[Enabled], UserPermission.Visibled, FunctionList.Tree_index, FunctionList.Functions
        FROM FunctionList
        Left JOIN UserPermission ON (FunctionList.Functions = UserPermission.Functions AND UserPermission.User_Role = '{}')
        ORDER BY FunctionList.Display_order;
        """.format(userrole)
        fn_list = self.db.execute(exe_str)
        final_fun = []
        for f in fn_list:
            d = {}
            d['Index'] = f[0]
            try:
                translatedFuncName = self.lang[f[4]]
            except KeyError:
                translatedFuncName = f[4]
            d["Functions"] =  {'indent':f[3],'name':translatedFuncName}
            d["Enabled"] = f[1]
            d["Visibled"] = f[2]
            d['Tree Index'] = f[3]
            d['fnc_name']= f[4]
            final_fun.append(d)
        return final_fun

    def update_fnc_of_role(self,role,funcs,enabled,visibled):
        fields = ["Enabled", "Visibled"]
        if role=='':
            return 0, self.lang['server_select_one_userrole']
        if role == "Guest":
            return 0, self.lang['server_guest_role_not_change']

        try:
            for f, e, v in zip(funcs, enabled, visibled):
                if e == None:
                    e = False
                if v == None:
                    v = False
                # check function existed in sepcific role
                fields = ["Functions"]
                condition = r"WHERE User_Role='{}' AND Functions='{}'".format(role,f)
                ret = self.db.select("UserPermission", fields, condition=condition)
                if ret:
                    # function existed
                    fields = ["Enabled", "Visibled"]
                    condition = r"WHERE User_Role='{}' AND Functions = '{}'".format(role, f)
                    self.savelog('Update user role "{}" with permission "enable" to {} and "visible" to {} of function "{}"'.format(role, e, v, f), audit=True)
                    self.db.update('UserPermission', fields, [e,v], condition)
                else:
                    # function not existed
                    fields = ["User_Role","Functions", "Enabled", "Visibled"]
                    self.savelog('Insert user role "{}" with permission "enable" to {} and "visible" to {} of function "{}"'.format(role, e, v, f), audit=True)
                    self.db.insert("UserPermission",fields=fields,data=[role,f,e,v])
            return 1, self.lang['server_update_ok']
        except Exception as e:
            self.savelog("Error: Updating user permission error ({})".format(e))
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
                    self.savelog('Insert new user role "{}" with permission "enable" to {} and "visible" to {} of function "{}"'.format(role, enb, visb, fn), audit=True)
                return 1, self.lang['server_role_add_ok']
            except Exception as e:
                self.savelog("Error: Add Role error ({})".format(e))
                return 0, "Error: Add Role error ({})".format(e)
        else:
            return 0, self.lang['server_role_exist'].format(role)
               
    def delete_role(self,role):
        if role=='':
            return 0, self.lang['server_select_one_userrole']
        if role == "Guest":
            return 0, self.lang['server_guest_role_not_delete']

        condition = r"WHERE User_Role='{}'".format(role)
        try:
            self.db.delete("UserPermission",condition)
            self.db.delete("UserRoleList",condition)
            fields = ["User_Role"]
            self.db.update("UserList", fields,['Guest'],condition)
            self.savelog('Delete user role "{}"'.format(role), audit=True)
            return 1, self.lang['server_role_delete_ok']
        except Exception as e:
            self.savelog("Error: Delete Role error ({})".format(e))
            return 0, "Error: Delete Role error ({})".format(e)

    def set_new_password_when_first_login(self,userID, curPW, newPW, newPWagain):
        # check current password is correct
        fields = ["PW"]
        condition = r"WHERE User_Name = '{}'".format(userID)
        ret = self.db.select('UserList',fields, condition)
        result = ret[0]
        pwIndb = result['PW']

        if not curPW == util.decrypt_password(pwIndb):
            return 0, self.lang['server_cur_pw_not_correct']

        # check new password policy
        if len(newPW) < 6:
            return 0, self.lang['server_pw_greater_5']
        if not util.isPW_complex(newPW):
            return 0, self.lang['server_pw_contain_letter']
        if newPW != newPWagain:
            return 0, self.lang['server_pw_not_match']

        # update passowrd
        encp_pw = util.encrypt_password(newPW)
        now = datetime.datetime.now()
        exp_date = util.add_months(now, 6)
        exp_time = exp_date.strftime(r"%Y/%m/%d %H:%M:%S.000000")
        f = ["PW", "Expired_Date","First_login"]
        condition = r"WHERE User_Name='{}'".format(userID)
        try:
            self.db.update('UserList', f, [encp_pw, exp_time, 0], condition)
            self.savelog(self.lang['server_pw_save_ok'], audit=True)
            return 1, self.lang['server_pw_save_ok']
        except Exception as e:
            return 0, "Error: First Login error ({})".format(e)