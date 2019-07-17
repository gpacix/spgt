#!/usr/bin/env python3

import socketserver
import random

current = 128
color_offset = 3 # 3=blue, 2=green, 1=red

def log(level, *rest):
    if VERBOSITY >= level:
        print('server: ', *rest)

def draw_random(databytes, x, y, d, current):
    for p in range(x*y):
        databytes[p*d+1] = random.randint(0,255)
        databytes[p*d+3] = current

def draw_lines(databytes, x, y, d, current):
    for j in range(y):
        for i in range(0,x,max(current,1)):
            databytes[(j*x + i)*4+color_offset] = 255


class TheRequestHandler(socketserver.BaseRequestHandler):
    """ TCP Request handler """

    def handle(self):
        self.width, self.height = 640, 480
        self.depth = 4  # in bytes
        while True:
            self.data = self.request.recv(1024).strip()
            if (len(self.data) == 0):
                break
            # logging:
            log(2, "{} sent:".format(self.client_address[0]))
            log(2, self.data)
            self.handle_event(self.data)
            # response:
            image = self.make_image()
            #log(3, "self.request class:", type(self.request))
            #log(3, "dir self.request:", dir(self.request))
            self.request.sendall(image)

    def handle_event(self, data):
        if data.startswith(b'MOUSEBUTTONDOWN'):
            # MOUSEBUTTONDOWN (34, 41) 1
            x = int(data.split()[1][1:-1])
            y = int(data.split()[2][:-1])
            global current
            if x < self.width/3:
                current -= 16
            elif x > 2*self.width/3:
                current += 16
            elif y < self.height/3:
                global color_offset
                color_offset = (color_offset % 3) + 1
            current = current % 256

    def make_image(self):
        # black image:
        # 256 x 256, grayscale: [ 1, 0, 1, 0, 1]
        x,y,d = self.width, self.height, self.depth
        size = [ (x//256), (x%256), (y//256), (y%256), d]
        log(1, size)
        # So we're sending ARGB. Strange.
        #databytes = [0, 0, 0, current] * (x * y)
        databytes = [0] * (x*y*d)
        draw_lines(databytes, x, y, d, current)
        log(2, "current is now ", current)
        return bytearray(size + databytes)

if __name__ == '__main__':
    HOST, PORT = "localhost", 9999
    VERBOSITY = 0
    tcp_server = socketserver.TCPServer((HOST, PORT), TheRequestHandler)
    tcp_server.serve_forever()

