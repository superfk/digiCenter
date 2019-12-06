import websocket
import json
import threading
import datetime, time

data = json.dumps({"state": "state", "value": ''})

def data2json(state,data):
    return json.dumps({"state": state, "value": data})

class WsProtocol():
    def __init__(self, HOST='ws://127.0.0.1:12345', SUBPROTOCOLS = ['echo-protocol']):
        self.ws = None
        self.ws = websocket.WebSocketApp(HOST, subprotocols = SUBPROTOCOLS, on_open = self.onOpen, on_message = self.onMessage)
        self.exited = False
    
    def run(self):
        t = threading.Thread(target=self.ws.run_forever)
        t.daemon = True
        t.start()
        print('already run')

    def close(self):
        self.exited = True

    
    def onOpen(self, ws):
        sendMessage = 'python client connected'
        self.ws.send(data2json('msg', sendMessage))
    
    def onMessage(self, ws, msg):
        print("收到了從server傳來的message：" + msg)

    def cycleSend(self):
        while not self.exited:
            print(self.exited)
            try:
                timestr = datetime.datetime.strftime(datetime.datetime.now(),"%Y-%m-%d %H:%M:%S")
                self.ws.send(data2json('systime', timestr))
            except:
                pass
            finally:
                time.sleep(0.5)


def main():
    ws = WsProtocol()
    ws.run()
    t = threading.Thread(target=ws.cycleSend)
    t.start()
    time.sleep(5)
    ws.exited = True

    

if __name__ == '__main__':
    main()


