#!/usr/bin/python
# -*- coding: UTF-8 -*-

from cryptography.fernet import Fernet
import os
import string
import random
import time
import datetime
import calendar
import csv
import pandas as pd
import json
import re
import openpyxl as opx

def string_onlyPrintable(text):
    return ''.join(filter(lambda x: x in string.printable, text)).strip()

def read_system_config(path='config.json'):
    with open(path, 'r', encoding= 'utf-8') as f:
        data = json.load(f)
    return data

def write_system_config(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def isPW_complex(pw):
    z = re.match("^(?=.*[a-z])(?=.*[A-Z])(?=.*\d).+$", pw)
    if z:
        return True
    else:
        return False

def encrypt_password(pw):
    key = b'mASnZzVxJLLGLIe1H_y_tzl2cu7wzUf7l091-4SPTBo='
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(bytes(pw, 'utf-8')).decode("utf-8") 
    return cipher_text

def decrypt_password(decrypy_pw):
    key = b'mASnZzVxJLLGLIe1H_y_tzl2cu7wzUf7l091-4SPTBo='
    cipher_suite = Fernet(key)
    plain_text = cipher_suite.decrypt(bytes(decrypy_pw, 'utf-8')).decode("utf-8") 
    return plain_text

def newPathIfNotExist(path):
    if not os.path.exists(path):
        os.makedirs(path)

def randomStringDigits(stringLength=6):
    """Generate a random string of letters and digits """
    lettersAndDigits = string.ascii_letters + string.digits
    return ''.join(random.choice(lettersAndDigits) for i in range(stringLength))

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year,month)[1])
    hour = sourcedate.hour
    minutes = sourcedate.minute
    seconds = sourcedate.second
    return datetime.datetime(year, month, day, hour,minutes, seconds)

def save_password_to_json(folder_path, userID, role, pw):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    exp_pw_path = os.path.join(folder_path, '{}_{}.json'.format(role,userID))
    exp_json = {}
    exp_json['pw']= pw
    exp_json['role']= role
    exp_json['userID']= userID
    write2JSON(exp_pw_path,exp_json)
    return exp_json

def write2JSON(path, data_dict):
    with open(path, 'w', encoding='utf-8') as outfile:
        json.dump(data_dict, outfile, ensure_ascii=False)

def readFromJSON(path):
    with open(path, 'r', encoding='utf-8') as outfile:
        data = json.load(outfile)
    return data

def readLang(lang_folder, lang='en'):
    path = os.path.join(lang_folder, lang+".json")
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data

def get_csv_content(path, delimiter=';'):
    data = []
    
    with open(path, newline='') as csvfile:
        rows = csv.reader(csvfile, delimiter=delimiter)

        data_lines = 0
        dataset = []

        for i, row in enumerate(rows):
            if i==0:
                header = row
            else:
                dataset.append(row)
                data_lines +=1

        if data_lines == 0:
            single_data = {}
            for i in range(len(header)):
                single_data[header[i]] = "empty"
            data.append(single_data)
        else:
            for i, row in enumerate(dataset):
                if i != 0:
                    single_data = {}
                    for j, d in enumerate(row[:len(header)]):
                        single_data[header[j]] = d
                    data.append(single_data)
    
    return data

def set_csv_content(data_dict_list, path, fieldnames, delimiter=';'):
    with open(path, "w", newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for d in data_dict_list:
            writer.writerow(d)

def ordered(obj):
    if isinstance(obj, dict):
        return [ordered(v) for k, v in obj.items()]
    if isinstance(obj, list):
        return [ordered(x) for x in obj]
    else:
        return obj

def flatList(obj):
    finallist = []
    for elm in obj:
        if isinstance(elm, list):
            finallist.extend(flatList(elm))
        else:
            finallist.append(elm)
    return finallist

def flatten_dictionary(d):
    result = {}
    stack = [iter(d.items())]
    keys = []
    while stack:
        for k, v in stack[-1]:
            keys.append(k)
            if isinstance(v, dict):
                stack.append(iter(v.items()))
                break
            else:
                result['.'.join(keys)] = v
                keys.pop()
        else:
            if keys:
                keys.pop()
            stack.pop()
    return result

def compareTwoJson(json1, json2):
    try:
        # check structure
        same = json1.keys() == json2.keys()
        if not same:
            return False, 'structure invalid'
        
        # check setup
        ## check enable
        p1 = json1['setup']['subitem']['enabled']
        p2 = json2['setup']['subitem']['enabled']
        same = p1 == p2
        if not same:
            differ = 'changed from {} to {} of "Setup" step'.format(p1, p2)
            return False, 'Setup paras changes, reason: {}'.format(differ)

        ## check paras
        para1 = json1['setup']['subitem']['paras']
        para2 = json2['setup']['subitem']['paras']
        same = para1 == para2
        if not same:
            differ = 'change from {} to {}'.format(para1, para2)
            return False, 'Setup paras changes, reason: {}'.format(differ)

        # check teardown
        ## check enable
        p1 = json1['setup']['subitem']['enabled']
        p2 = json2['setup']['subitem']['enabled']
        same = p1 == p2
        if not same:
            differ = 'changed from {} to {} of "Teardown" step'.format(p1, p2)
            return False, 'Teardown paras changes, reason: {}'.format(differ)
        ## check paras
        para1 = json1['teardown']['subitem']['paras']
        para2 = json2['teardown']['subitem']['paras']
        same = para1 == para2
        if not same:
            differ = 'change from {} to {}'.format(para1, para2)
            return False, 'Teardown paras changes, reason: {}'.format(differ)

        # check main length
        length1 = json1['main']
        length2 = json2['main']
        same = len(length1) == len(length2)
        if not same:
            return False, 'the length of main sequences stucture is different'

        # check main content
        reason = []
        seq1 = json1['main']
        seq2 = json2['main']
        for s1, s2 in zip(seq1, seq2):
            k1 = s1['cat']
            k2 = s2['cat']
            same = k1 == k2
            if not same:
                differ = 'change from {} to {} in step "{}"'.format(k1, k2, int(s1['id'])+1)
                reason.append(differ)
        if len(reason)>0:
            differ = '\n'.join(map(str, reason))
            return False, 'the content of main sequences is different, reason: {}'.format(differ)

        # check main para
        reason = []
        seq1 = json1['main']
        seq2 = json2['main']
        for s1, s2 in zip(seq1, seq2):
            # check enable
            p1 = s1['subitem']['enabled']
            p2 = s2['subitem']['enabled']
            same = p1 == p2
            if not same:
                differ = '"enable property" changed from {} to {} of subitem "{}" in step {}'.format(p1, p2, s1['subitem']['item'], int(s1['id'])+1)
                reason.append(differ)

            # check paras
            p1 = s1['subitem']['paras']
            p2 = s2['subitem']['paras']
            for sub1, sub2 in zip(p1,p2):
                # check value
                k1 = sub1['value']
                k2 = sub2['value']
                same = k1 == k2
                if not same:
                    differ = '"{}" changed from {} to {} of subitem "{}" in step {}'.format(sub1['name'], k1, k2, s1['subitem']['item'], int(s1['id'])+1)
                    reason.append(differ)
        if len(reason)>0:
            differ = '\n'.join(map(str, reason))
            return False, 'the parameters of main sequences is different, reason: {}'.format(differ)
        
        return True, 'exactly the same'

    except:
        return False, 'check file difference error'


'''
########################
# Define Export class
########################
'''
class ExportWorker(object):
    def __init__(self, tabledata):
        self.tabledata = tabledata
        self.df = None
    
    def tabledata2DataFrame(self):
        self.df = pd.DataFrame(self.tabledata)

    def save(self, path=''):
        pass

class CSV_ExportWorker(ExportWorker):
    def __init__(self, tabledata,sep=';'):
        super(CSV_ExportWorker,self).__init__(tabledata)
        self.sep = sep

    def save(self, path):
        self.df.to_csv(path,index=0, encoding = "utf-8-sig", sep=self.sep)


class Excel_ExportWorker(ExportWorker):
    def __init__(self, tabledata):
        super(Excel_ExportWorker,self).__init__(tabledata)

    def save(self, path):
        df_obj = self.df.select_dtypes(['object'])
        self.df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        print(self.df)
        self.df.to_excel(path,  sheet_name='Test_Data', engine='openpyxl')

class OpenExcel():
    def __init__(self):
        self.wb = None

    def open_wb(self,path):
        self.wb = opx.load_workbook(path)

    def write_batch_info(self):
        st = self.wb.active
        rg_product = self.wb.defined_names['Project_']
        rg_batch = self.wb.defined_names['Batch_']
        rg_op = self.wb.defined_names['Operator_']
        rg_product.value="HDA150"
        rg_batch="batch1"
        rg_op="Shawn"

    def read_batch_info(self):
        st = self.wb.active
        rgs = self.wb.defined_names
        for r in rgs:
            print(r.value)

    def close_wb(self, path, save_changes = True):
        self.wb.save(filename = path)


if __name__ == '__main__':
    # pw = 'BaAdmin'
    # e_pw = encrypt_password(pw)
    # print(e_pw)
    # d_pw = decrypt_password(e_pw)
    # print(d_pw)

    # pw = randomStringDigits(10)
    # print(pw)

    # e_pw = encrypt_password(pw)
    # print(e_pw)
    # d_pw = decrypt_password(e_pw)
    # print(d_pw)

    # pw = 'erwej99ijR'
    # print(isPW_complex(pw))

    # tabledata = []
    # try:
    #     ex = Excel_ExportWorker(tabledata)
    #     ex.save('D:\\aaa.xlsx')
    # except Exception as e:
    #     print(e)

    # exc = OpenExcel()
    # exc.open_wb(r'C:\BareissInstr\trunk\BareissInstr\report.xlsx')
    # exc.write_batch_info()
    # exc.read_batch_info()
    # exc.close_wb(r'D:\testreport.xlsx')

    j1 = readFromJSON(r'C:\data_exports\seq_files\singleLoop.seq')
    j2 = readFromJSON(r'C:\data_exports\seq_files\singleLoopCopy.seq')
    ret = compareTwoJson(j1,j2)
    print(ret)
    print(ret[1])