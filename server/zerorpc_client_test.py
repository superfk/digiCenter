import zerorpc, os

c = zerorpc.Client(heartbeat=None)
c.connect("tcp://127.0.0.1:4242")
config = c.load_sys_config(r"C:\BareissInstr\trunk\BareissInstr\config.json")
print(config)
print(c.echo('I am echo'))
filter = {
    'batch': "a",
    'operator': "e",
    'date_start': '2019-09-04T14:55:02.568',
    'date_end': '2019-09-05T14:55:02.568'
  }
tableData = [{'Batch': 'Batch 2', 'Compound': 'TEST', 'Compound Folder': 'Folder 2', 'Operator': 'David', 'Production Date': '21.09.2018'}, {'Batch': 'Batch 3', 'Compound': 'TEST', 'Compound Folder': 'Folder 3', 'Operator': 'David', 'Production Date': '22.09.2018'}, {'Batch': 'Batch 4', 'Compound': 'TEST', 'Compound Folder': 'Folder 4', 'Operator': 'David', 'Production Date': '23.09.2018'}, {'Batch': 'Batch 5', 'Compound': 'TEST', 'Compound Folder': 'Folder 5', 'Operator': 'David', 'Production Date': '23.09.2018'}]
ret = 'Batch 2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00TEST\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00Folder 2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00David\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x0021.09.2018\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
currentDirectory = os.getcwd()
#print(c.load_sys_config(currentDirectory+'/config.json'))
print(c.backend_init())
print(c.connect_DT())

for i in range(20):
  c.set_DT_remote(True)
  c.start_DT_mear()
  print(c.get_DT_single_data())

c.close_all()


