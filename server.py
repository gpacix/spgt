#!/usr/bin/env python3

import socketserver
import random
ri = random.randint

current = 128
color_offset = 3 # 3=blue, 2=green, 1=red

delay_update = 3

def log(level, *rest):
    if VERBOSITY >= level:
        print('server: ', *rest)

def draw_random(databytes, x, y, d, current):
    for p in range(x*y):
        databytes[p*d+1] = ri(0,255)
        databytes[p*d+3] = current

def draw_lines(databytes, x, y, d, current):
    for j in range(y):
        for i in range(0,x,max(current,1)):
            databytes[(j*x + i)*4+color_offset] = 255

class Surface(object):
    def __init__(self, w, h, d):
        self.data = [0] * (w*h*d)
        self.w = w
        self.h = h
        self.d = d

    def point(self, x, y, color):
        p = (x + y*self.w)*4
        self.data[p + 0] = color[0]
        self.data[p + 1] = color[1]
        self.data[p + 2] = color[2]
        self.data[p + 3] = color[3]

    # TODO: make this more efficient
    def plot(self, x, y, scale, color):
        for dx in range(scale):
            for dy in range(scale):
                self.point(x*scale+dx, y*scale+dy, color)
        #self.data[(x + y*self.w)*4*scale + color_offset] = 255


SC = 6
SZ=480//SC  

def draw_life(s, current):
    #c = (255, 192, 128, 0)
    c = [0,0,0,0]
    c[color_offset] = 255
    for x in range(SZ):
        for y in range(SZ):
            if life[x][y] != 0:
                s.plot(x, y, SC, c)
                #s.point(x, y, c)

life = [[1,0,0,0,0,0,0,0] * (SZ//8) for _ in range(SZ)]
for _ in range(200):
    life[ri(0,SZ-1)][ri(0,SZ-1)] = 1

def update_life():
    global life
    l2 = [[0] * SZ for _ in range(SZ)]
    for x in range(1,SZ-1):
        for y in range(1,SZ-1):
            neighbors = (life[x-1][y-1] + life[x-1][y] + life[x-1][y+1] +
                         life[x  ][y-1] +                life[x  ][y+1] +
                         life[x+1][y-1] + life[x+1][y] + life[x+1][y+1] )
            if (life[x][y] and neighbors in [2, 3] or
                life[x][y] == 0 and neighbors == 3):
                l2[x][y] = 1
    life = l2
    


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
        global delay_update
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
            if delay_update == 0:
                update_life()
            else:
                delay_update -= 1

    def make_image(self):
        # 256 x 256, grayscale: [ 1, 0, 1, 0, 1]
        x,y,d = self.width, self.height, self.depth
        size = [ (x//256), (x%256), (y//256), (y%256), d]
        log(1, size)
        # So we're sending ARGB. Strange.
        databytes = [0] * (x*y*d)
        s = Surface(x, y, d)
        draw_life(s, current)
        log(2, "current is now ", current)
        return bytearray(size + s.data) # TODO: make size part of Surface

if __name__ == '__main__':
    HOST, PORT = "localhost", 9999
    VERBOSITY = 0
    tcp_server = socketserver.TCPServer((HOST, PORT), TheRequestHandler)
    tcp_server.serve_forever()
