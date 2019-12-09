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
        os.mkdir(path)

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
    write2JSON(exp_pw_path,exp_json)

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
    def __init__(self, tabledata):
        super(CSV_ExportWorker,self).__init__(tabledata)

    def save(self, path):
        self.df.to_csv(path,index=0, encoding = "utf-8", sep=';')


class Excel_ExportWorker(ExportWorker):
    def __init__(self, tabledata):
        super(Excel_ExportWorker,self).__init__(tabledata)

    def save(self, path):
        df_obj = self.df.select_dtypes(['object'])
        self.df[df_obj.columns] = df_obj.apply(lambda x: x.str.strip())
        self.df.to_excel(path, index=False, sheet_name='Test_Data')

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

    exc = OpenExcel()
    exc.open_wb(r'C:\BareissInstr\trunk\BareissInstr\report.xlsx')
    exc.write_batch_info()
    exc.read_batch_info()
    exc.close_wb(r'D:\testreport.xlsx')