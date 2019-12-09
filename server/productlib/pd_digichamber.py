from productlib import pd_product
import corelib.utility.utility as util

class DigiChamberProduct(pd_product.Product):
    def __init__(self, pd_name):
        super(DigiChamberProduct, self).__init__(pd_name)
        self.script = None

    def run_script(self, scriptName, data=None):
        if scriptName=='ini_seq':
            return self.init_seq(data)
        elif scriptName=='save_seq':
            return self.save_seq(path=data['path'],seq_json=data['seq'])
        elif scriptName=='load_seq':
            return self.load_seq(data['path'])
        else:
            print('No this case: {}'.format(scriptName))
        return 0

    def init_seq(self,data):
        self.script=None
        return data

    def save_seq(self,path,seq_json):
        util.write2JSON(path, seq_json)
        return 'file saved'

    def load_seq(self,path):
        data = util.readFromJSON(path)
        self.script=data
        return data