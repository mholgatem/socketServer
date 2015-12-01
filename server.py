#! /usr/bin/env python
import SocketServer, subprocess, sys 
from threading import Thread
import thread
import time
from evdev import InputDevice, list_devices, InputEvent, ecodes as e, UInput
import json
import keys
import broadcast
import argparse

parser = argparse.ArgumentParser(description='PiScraper')
parser.add_argument('--max_controllers', 
						metavar = '4', default = 4, type = int,
						help='Maximum number of server threads to run.')
parser.add_argument('--port',
						metavar = '55536', default = 2000, type = int,
						help='Starting port number. Port range = port + max_controllers')
parser.add_argument('--bcastport',
						metavar = '55535', default = 55535, type = int,
						help='Starting port number. Port range = port + max_controllers')
parser.add_argument('--bcastip',
						metavar = '255.255.255.255', default = '255.255.255.255',
						type = str, help='Broadcast IP')
parser.add_argument('--key',
						metavar = '*4kap),dci30dm?', default = '*4kap),dci30dm?',
						type = str, help='Secret Handshake Key')
						
args = parser.parse_args()



HOST = '0.0.0.0'
PORT = args.port

keylist = [ value for key, value in keys.keyList.iteritems() ]
cap = {
        e.EV_KEY : keylist,
        e.EV_ABS : [
            (e.ABS_X, [-32767, 32767, 3, 1, 5, 6]),
            (e.ABS_Y, [-32767, 32767, 3, 1, 5, 6]),
            ]
}
ui = UInput(cap, name="STCKServer") #need to make new instance per player
thread.start_new_thread(broadcast.Remotesy, (args,))

''' Future capability to run commands '''
''' example: reply = pipe_command(my_unix_command, data)'''
def pipe_command(arg_list, standard_input=False):
    "arg_list is [command, arg1, ...], standard_input is string"
    pipe = subprocess.PIPE if standard_input else None
    subp = subprocess.Popen(arg_list, stdin=pipe, stdout=subprocess.PIPE)
    if not standard_input:
        return subp.communicate()[0]
    return subp.communicate(standard_input)[0]

'''doKey(ecodes.EV_KEY,ecodes.KEY_UP)'''
def doKey(inputKey, pressedState):
    ev = InputEvent(time.time(), 0, e.EV_KEY, inputKey, pressedState)
    #with UInput() as ui:
    ui.write_event(ev)
    ui.syn()

def setAxis(value):
    xAxis = value[0]
    yAxis = value[1]
    ui.write(e.EV_ABS, e.ABS_X, int(xAxis))
    ui.write(e.EV_ABS, e.ABS_Y, int(yAxis))
    ui.syn()
                

class SingleTCPHandler(SocketServer.BaseRequestHandler):
    "One instance per connection.  Override handle(self) to customize action."
    RUNNING = True;
    def handle(self):
        # self.request is the client connection
        while self.RUNNING:
            data = self.request.recv(1024)  # clip input at 1Kb
            if not data:
                break
            if 'exit' in data:
                break
            '''decode data'''
            dataChunks = data.split("|")
            for d in dataChunks[:-1]:
                try:
                    decode = json.loads(d)
                    self.handleType(decode)
                    reply = "{'success': True }"
                except ValueError:
                    reply = None
                if reply is not None:
                    self.request.send(reply)
        self.request.close()
    
    
    def handleType(self, decode):
        '''key press'''
        #print decode
        type = decode['type']
        if type == "EV_KEY":
            #print decode['key']
            if decode['key'] == "disconnect":
                self.RUNNING = False
                print 'disconnect'
            else:
                try:
                    inputKey = keys.keyList[str(decode['key'])]
                    inputState = int(decode['state'])
                    doKey(inputKey, inputState)
                except KeyError:
                    print "unknown key:", decode['key']
        '''mouse move'''
        if type == "EV_REL":
            pass
        '''joystick/wheel'''
        if type == "EV_ABS":
            value = eval(decode['value'])
            setAxis(value)
        '''run command'''
        if type == "runCommand":
            if int(decode['state']) == 0:
                try:
                    for command in decode['key'].split(';'):
                        print pipe_command(command.split(' '))
                except OSError:
                    print "invalid command:" + decode['key']



class SimpleServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    # Ctrl-C will cleanly kill all spawned threads
    daemon_threads = True
    # much faster rebinding
    allow_reuse_address = True

    def __init__(self, server_address, RequestHandlerClass):
        SocketServer.TCPServer.__init__(self, server_address, RequestHandlerClass)
        
        

if __name__ == "__main__":
    server = SimpleServer((HOST, PORT), SingleTCPHandler)
    # terminate with Ctrl-C
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.exit(0)
