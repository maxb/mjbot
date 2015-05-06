from threading import Thread
import socket

class SocketServer(Thread):
    def __init__(self, bot):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.stop = False
        self.ssock = None

    def run(self):
        self.ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ssock.bind(('127.0.0.1', int(self.bot.config.messagesocket.port)))
        self.ssock.listen(5)
        while not self.stop:
            sock, addr = self.ssock.accept()
            ConnHandler(self.bot, sock).start()

class ConnHandler(Thread):
    def __init__(self, bot, sock):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.sock = sock
    def run(self):
        channel = self.bot.channels[0]
        data = self.sock.makefile(mode='r', encoding='utf8').read().strip()
        self.bot.notice(channel, data)
        self.sock.close()

def setup(bot):
    global server
    server = SocketServer(bot)
    server.start()

def shutdown(bot):
    server.stop = True
    server.ssock.close()
