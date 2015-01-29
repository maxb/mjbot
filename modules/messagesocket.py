from threading import Thread
import socket

class SocketServer(Thread):
    def __init__(self, bot):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
    def run(self):
        ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        ssock.bind(('127.0.0.1', 12345))
        ssock.listen(5)
        while True:
            sock, addr = ssock.accept()
            ConnHandler(self.bot, sock).start()

class ConnHandler(Thread):
    def __init__(self, bot, sock):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.sock = sock
    def run(self):
        channel = self.bot.channels[0]
        data = self.sock.makefile().read().strip()
        self.bot.notice(channel, data)
        self.sock.close()

def setup(bot):
    SocketServer(bot).start()
