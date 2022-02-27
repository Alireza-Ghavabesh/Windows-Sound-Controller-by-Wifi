from collections import defaultdict
from ctypes import cast, POINTER
from aiohttp.web_request import Request
from comtypes import CLSCTX_ALL
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
devices = AudioUtilities.GetSpeakers()
interface = devices.Activate(
    IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
volume = cast(interface, POINTER(IAudioEndpointVolume))
volume.GetMute()

vrange = volume.GetVolumeRange()

# ========================== aiohttp server ==============
import asyncio
import logging
import pathlib
import sys
from aiohttp import web
import aiohttp
import socket
import aiohttp_jinja2
import jinja2
import webbrowser



vlm = 40
fake_vlm = 40 

def get_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # doesn't even have to be reachable
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP


IP = get_ip()
PORT = 3400


# list of clients
client_counter = 0

CLIENTS = []

# routes
routes = web.RouteTableDef()





@aiohttp_jinja2.template("client.html")
class websocketPageHandler(web.View):
    
    async def get(self):
        context = {'IP': IP, 'PORT': PORT}
        return context


@routes.get('/ws')
async def websocket_handler(request: Request) -> web.WebSocketResponse:
    global vlm
    global fake_vlm
    global client_counter
    global CLIENTS
    
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if ws not in CLIENTS:
        CLIENTS.append(ws)
    # print(len(CLIENTS))
    # print(request.app['websockets'].values())
    async for msg in ws:
        if msg.type == aiohttp.WSMsgType.TEXT:
            if msg.data == 'close':
                await ws.close()
            else:
                v = int(80-int(msg.data))
                print(msg.data)
                volume.SetMasterVolumeLevel(-v, None)
                masterVolume = volume.GetMasterVolumeLevel()
                print(f"masterVolume: {masterVolume}")
                for ws in CLIENTS:
                    await ws.send_str(msg.data)
        elif msg.type == aiohttp.WSMsgType.ERROR:
            print('ws connection closed with exception %s' %
                ws.exception())
    

    print('websocket connection closed')

    return ws






if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)

    app = web.Application()
    app['websockets'] = defaultdict(dict)

    # setup jinja2 
    aiohttp_jinja2.setup(app,
        loader=jinja2.FileSystemLoader(
            'templates'
            ))
    app.add_routes(routes)
    app.router.add_get('/', websocketPageHandler, name="client")
    webbrowser.open(f"http://{IP}:{PORT}")
    web.run_app(app, port=PORT, host=IP)