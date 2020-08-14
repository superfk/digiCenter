import zerorpc
import sys
import os
from corelib.hardwarelib.instrClass.digitest import Digitest


class digitest_unittesting():
    def __init__(self):
        self.digiTest = Digitest()

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