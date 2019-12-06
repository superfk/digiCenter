import asyncio
import websockets
import json
import datetime
import random

data = json.dumps({"state": "state", "value": ''})
exit = False

def data2json(state,data):
    return json.dumps({"state": state, "value": data})

async def time(websocket, path):
    while True:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        await websocket.send(data2json('time', now))
        await asyncio.sleep(random.random() * 3)

async def pyapi(websocket, path):
    data = await websocket.recv()
    
    print(data)

    await websocket.send(data)

start_server = websockets.serve(time, "127.0.0.1", 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()