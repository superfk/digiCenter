import csv, os
import json
import pandas as pd
from loguru import logger
import logging.handlers
import time,os, sys

# sys.stdout.write('chcp 65001')

class BaseLog(object):
    def __init__(self, filename):
        self.fname = filename
        logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")
        self.logger=logging.getLogger(self.fname)
        self.logger.setLevel(logging.DEBUG)
        #format='[%Y-%m-%d %H:] - %(levelname)s - %(name)s : %(message)s'
        self.formatter=logging.Formatter(fmt="%(asctime)s.%(msecs)03d-[%(levelname)s]-%(name)s:%(message)s ", datefmt="%Y-%m-%d_%H:%M:%S")
        streamhandler=logging.StreamHandler()
        streamhandler.setFormatter(self.formatter)
        self.logger.addHandler(streamhandler)
        self.logtime = time.strftime("%Y-%m-%d", time.localtime())
        #logfile='./logs/' + "{}"self.fname + '.log'
        if not os.path.exists("./systemlog"):
            os.mkdir("./systemlog")
        if not os.path.exists("./systemlog/{}".format(self.fname)):
            os.mkdir("./systemlog/{}".format(self.fname))
        if not os.path.exists("./systemlog/{}/{}".format(self.fname, self.logtime)):
            os.mkdir("./systemlog/{}/{}".format(self.fname, self.logtime))
        self.logfile= "./systemlog/{}/{}/{}.log".format(self.fname, self.logtime, self.logtime)
    def append_lineNo(self,msg):
        fr = sys._getframe(2)
        line = fr.f_lineno
        fun = os.path.split(fr.f_code.co_filename)[1]
        msg = '{}-line {} from {}'.format(msg, line, fun)
        return msg
    def append_traceback_info(self, msg):
        exc_type, exc_obj, exc_tb = sys.exc_info()
        if exc_tb is None:
            return msg
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        msg = '{} [error type: {}, fname: {}, lineNo: {}]'.format(msg, exc_type, fname, exc_tb.tb_lineno)
        return msg
    def debug(self, msg):
        try:
            # msg = str(msg).encode('utf-8').decode('cp950',errors='ignore')
            msg = self.append_lineNo(msg)
            msg = self.append_traceback_info(msg)
            self.logger.debug(msg)
        except Exception as e:
            self.logger.debug('WRITE LOG FAILED! REASON: {}'.format(e))
    def info(self, msg):
        msg = str(msg).encode('utf-8').decode('cp950',errors='ignore')
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.info(msg)
    def warning(self, msg):
        msg = str(msg).encode('utf-8').decode('cp950',errors='ignore')
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.warning(msg)
    def error(self, msg):
        msg = str(msg).encode('utf-8').decode('cp950',errors='ignore')
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.error(msg)
    def critical(self, msg):
        msg = str(msg).encode('utf-8').decode('cp950',errors='ignore')
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.critical(msg)
    def log(self, level, msg):
        msg = str(msg).encode('utf-8').decode('cp950',errors='ignore')
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.log(level, msg)
    def setLevel(self, level):
        self.logger.setLevel(level)
    def disable(self):
        logging.disable(50)

class Syslog(BaseLog):
    def __init__(self, filename):
        BaseLog.__init__(self, filename)
        filehandler=logging.FileHandler(self.logfile)
        filehandler.setFormatter(self.formatter)
        self.logger.addHandler(filehandler)

class MsgLogger(BaseLog):
    def __init__(self, filename):
        BaseLog.__init__(self,filename)
        rotatehandler = logging.handlers.RotatingFileHandler(self.logfile, maxBytes=1024, backupCount=5)
        rotatehandler.setFormatter(self.formatter)
        self.logger.addHandler(rotatehandler)

class TimeRotateLogger(BaseLog):
    def __init__(self, filename, when='M', interval=5):
        BaseLog.__init__(self, filename)
        rotatehandler = logging.handlers.TimedRotatingFileHandler(self.logfile, when=when, interval=interval, backupCount=24)
        rotatehandler.setFormatter(self.formatter)
        rotatehandler.suffix = "%Y%m%d-%H%M.log"
        self.logger.addHandler(rotatehandler)

def writeSingleToExcel(lang):
    with open('{}.json'.format(lang), encoding='utf-8-sig') as f_input:
        data = json.load(f_input)
        
        dataset = []
        head = ''
        for k,v in data.items():
            if not k == 'display_name':
                d={}
                d['name'] = k
                d['text'] = v
                dataset.append(d)
            else:
                head = v

        df = pd.DataFrame(dataset)
        df = df.rename(columns={'text': head})
        print(df)

    df.to_excel('{}.xlsx'.format(lang), encoding='utf-8-sig', index=True)

def writeAllToJson(source):
    df = pd.read_excel(source,engine='openpyxl', index_col=[0])
    print(df)
    df = df.set_index('name')
    print(df)
    lang_names = list(df)
    print(lang_names)
    for ln in lang_names:
        print(df[ln])
        jfile = '{}.json'.format(ln)
        with open(jfile, 'w', encoding='utf-8-sig') as file:
            df[ln].to_json(file, force_ascii=False, orient='index',indent=2)

def load_json_lang_from_xlsx(source, langID='en'):
    df = pd.read_excel(source,engine='openpyxl', index_col=[0])
    df = df.set_index('name')
    lang_names = list(df)
    data = None
    for ln in lang_names:
        if ln == langID:
            jfile = '{}.json'.format(ln)
            print('read lang file={}'.format(jfile))
            data = df[ln].to_json(force_ascii=False, orient='index',indent=2)
            break
    return data

def load_json_lang_from_json(lang_folder, langID='en'):
    path = os.path.join(lang_folder, langID+".json")
    with open(path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    return data

if __name__ == '__main__':
    langset = ['en','de','zh_tw']
    # lg = TimeRotateLogger('syslog', 'M', 5)
    # writeSingleToExcel('de')
    writeAllToJson(source='all_lang_V1.4.xlsx')
    data = load_json_lang_from_json('','de')
    logger.debug(data)
    # data = str(data).encode("utf8").decode("utf8", "ignore")
    # data = load_json_lang_from_xlsx('all.xlsx', 'en')