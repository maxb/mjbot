from threading import Thread
import socket

"""
It appears to be strangely challenging to close a listening socket and re-open
it within a Python process, without running into 'address in use' errors. Even
after experimenting with a variety of non-blocking options, and attempting to
manually make a connection to the listening socket to knock another thread out
of a blocking accept call, nothing seemed to work. Thus, in the interests of
achieving a working, if somewhat weird, solution, the server socket is now
cached on the bot object beyond the lifetime of the plugin module. Even with
that measure, the first connection after a module reload attempt will still go
to the old code and thread (after which it will then exit and leave the new
code and thread to carry on).
"""

class SocketServer(Thread):
    def __init__(self, bot):
        Thread.__init__(self)
        self.daemon = True
        self.bot = bot
        self.stop = False
        self.addr = ('127.0.0.1', int(self.bot.config.messagesocket.port))

        self.ssock = getattr(bot, 'messagesocket_ssock', None)
        if self.ssock is None:
            self.ssock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.ssock.bind(self.addr)
            self.ssock.listen(5)
            bot.messagesocket_ssock = self.ssock

        self.start()

    def request_stop(self):
        self.stop = True

    def run(self):
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

def shutdown(bot):
    server.request_stop()
