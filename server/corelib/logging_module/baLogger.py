import logging
import logging.handlers
import time,os, sys

class BaseLog(object):
    def __init__(self, filename):
        self.fname = filename
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
            msg = self.append_lineNo(msg)
            msg = self.append_traceback_info(msg)
            self.logger.debug(msg.encode("utf8").decode('utf8',"ignore"))
        except Exception as e:
            self.logger.debug('WRITE LOG FAILED! REASON: {}'.format(e))
    def info(self, msg):
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.info(msg)
    def warning(self, msg):
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.warning(msg)
    def error(self, msg):
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.error(msg)
    def critical(self, msg):
        msg = self.append_lineNo(msg)
        msg = self.append_traceback_info(msg)
        self.logger.critical(msg)
    def log(self, level, msg):
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