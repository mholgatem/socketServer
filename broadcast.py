import thread
import select
import socket
import time

class Remotesy(object):

    BCAST_IP = "255.255.255.255"
    BCAST_PORT = 55535
    BUF_SIZE = 1024
    SECRET_KEY = "*4kap),dci30dm?"
    
    CURRENT_PORT = 2000
    thread_list = []

    def __init__(self, args):
        self.BCAST_IP = args.bcastip
        self.BCAST_PORT = args.bcastport
        self.CURRENT_PORT = min(args.port, 65536 - args.max_controllers)
        self.SECRET_KEY = str(args.key)
        
        self.args = args
        self.host = self.get_host()
        address = (self.BCAST_IP, self.BCAST_PORT)
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR,1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server_socket.bind(address)
        server_socket.setblocking(0)
        bcast_id = ''.join([self.SECRET_KEY, socket.gethostname(),'{',str(self.CURRENT_PORT),'}'])

        while True:
            result = select.select([server_socket],[],[])
            msg = result[0][0].recv(self.BUF_SIZE)
            if ((self.SECRET_KEY in msg) and msg != bcast_id):
                self.BCAST_TIMER = 10
                inviteAddress = (msg.replace(self.SECRET_KEY, ''), self.BCAST_PORT)
                bcast_id = ''.join([self.SECRET_KEY, socket.gethostname(),'{',str(self.CURRENT_PORT),'}'])
                server_socket.sendto(bcast_id, inviteAddress)
    
    
    def get_host(self):
        host = socket.gethostbyname(socket.gethostname())
        if not '127' in host:
            return host
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8",0))
        host = (s.getsockname()[0])
        s.close()
        return host