from productlib import pd_product
import corelib.utility.utility as util
import os

class DigiChamberProduct(pd_product.Product):
    def __init__(self, pd_name,seqPath=r"C:\\data_exports"):
        super(DigiChamberProduct, self).__init__(pd_name)
        self.script = None
        self.setDefaultSeqFolder(seqPath)
        

    def run_script(self, scriptName, data=None):
        if scriptName=='ini_seq':
            return self.init_seq(data)
        elif scriptName=='save_seq':
            return self.save_seq(path=data['path'],seq_json=data['seq'])
        elif scriptName=='load_seq':
            return self.load_seq(data['path'])
        elif scriptName=='get_default_seq_path':
            return self.default_seq_folder
        else:
            print('No this case: {}'.format(scriptName))
        return 0

    def init_seq(self,data):
        self.script=None
        return data

    def save_seq(self,path,seq_json):
        newPath = os.path.join(self.default_seq_folder,path)
        util.write2JSON(newPath, seq_json)
        return 'file saved to: {}'.format(newPath)

    def load_seq(self,path):
        data = util.readFromJSON(path)
        self.script=data
        return data
    
    def setDefaultSeqFolder(self,seqPath):
        path = os.path.join(seqPath,'seq_files')
        self.default_seq_folder = path
        util.newPathIfNotExist(self.default_seq_folder)