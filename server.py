#!/usr/bin/env python3

import socketserver
import random
ri = random.randint

from parsearguments import parse
from colors import *

UP, DOWN, RIGHT, LEFT = 273, 274, 275, 276

delay_update = 3

def log(level, *rest):
    if VERBOSITY >= level:
        print('server: ', *rest)

def draw_random(databytes, x, y, d, current):
    for p in range(x*y):
        databytes[p*d+1] = ri(0,255)
        databytes[p*d+3] = current

color_offset = 3 # 3=blue, 2=green, 1=red

def draw_lines(databytes, x, y, d, current):
    for j in range(y):
        for i in range(0,x,max(current,1)):
            databytes[(j*x + i)*4+color_offset] = 255

class Wheel:
    def __init__(self, items):
        self.items = items[:]
        self.index = 0

    def current(self):
        return self.items[self.index]

    def forward(self):
        self.index = (self.index + 1) % len(self.items)

    def backward(self):
        self.index = (self.index - 1) % len(self.items)

foregrounds = Wheel([RED, GREEN, BLUE, ORANGE])
backgrounds = Wheel([BLACK, WHITE, YELLOW, ORANGE, GRAY])


class Surface(object):
    def __init__(self, w, h, d):
        self.w = w
        self.h = h
        self.d = d
        self.clear(BLACK)

    def clear(self, color):
        if self.d == 1:
            color = [argbtoi[color]]
        else:
            color = list(color)
        self.data = color * (self.w * self.h)

    def point(self, x, y, color):
        p = (x + y*self.w) * self.d
        if self.d == 1:
            self.data[p] = color
        else:
            self.data[p + 0] = color[0]
            self.data[p + 1] = color[1]
            self.data[p + 2] = color[2]
            self.data[p + 3] = color[3]

    # TODO: make this more efficient
    def plot(self, x, y, scale, color):
        if self.d == 1:
            color = argbtoi[color]
        for dx in range(scale):
            for dy in range(scale):
                self.point(x*scale+dx, y*scale+dy, color)

WIDTH, HEIGHT = 640//4, 480//4 # 320*3, 256*3

SC = 1
SZ = 120


class Life(object):
    def __init__(self, size):
        self.size = size
        self.data = [[0] * self.size for _ in range(self.size)]
        # Stripe every 8:
        for i in range(self.size):
            col = self.data[i]
            for j in range(0, self.size, 8):
                col[j] = 1
        
        for _ in range(200):
            self.data[ri(0,self.size-1)][ri(0,self.size-1)] = 1

    def draw(self, surface):
        #c = (255, 192, 128, 0)
        c = foregrounds.current()
        for x in range(self.size):
            for y in range(self.size):
                if self.data[x][y] != 0:
                    surface.plot(x, y, SC, c)
                    #surface.point(x, y, c)

    def toggle(self, x, y):
            self.data[x][y] = 1 - self.data[x][y]

    def update(self):
        SZ = self.size
        nextdata = [[0] * SZ for _ in range(SZ)]
        for x in range(0,SZ):
            for y in range(0,SZ):
                left, right = (x - 1) % SZ, (x + 1) % SZ
                up, down    = (y - 1) % SZ, (y + 1) % SZ
                neighbors = (self.data[left][y-1] +  self.data[left][y]  + self.data[left][down] +
                             self.data[x   ][y-1] +                        self.data[x  ][down] +
                             self.data[right][y-1] + self.data[right][y] + self.data[right][down] )
                if (self.data[x][y] and neighbors in [2, 3] or
                    self.data[x][y] == 0 and neighbors == 3):
                    nextdata[x][y] = 1
        self.data = nextdata


life = Life(SZ)

class TheRequestHandler(socketserver.BaseRequestHandler):
    """ TCP Request handler """

    def handle(self):
        self.width, self.height = WIDTH, HEIGHT
        self.depth = 1  # in bytes
        while True:
            self.data = self.request.recv(1024).strip()
            if (len(self.data) == 0):
                break
            # logging:
            log(3, "{} sent:".format(self.client_address[0]))
            log(2, self.data)

            self.handle_event(self.data)
            # response:
            image = self.make_image()
            #log(3, "self.request class:", type(self.request))
            #log(3, "dir self.request:", dir(self.request))
            self.request.sendall(image)

    def handle_mousebuttondown(self, ds):
        # MOUSEBUTTONDOWN (34, 41) 1
        x = int(ds[1][1:-1])
        y = int(ds[2][:-1])
        lifex, lifey = x//SC, y//SC
        if lifex < SZ and lifey < SZ:
            life.toggle(lifex, lifey)

    def handle_keydown(self, ds):
        code = int(ds[1])
        if ds[2] == b'f':
            pass
        if code == 32:
            log(1, "space")
            return True
        if code in [UP, DOWN, RIGHT, LEFT]:
            if code == UP:
                backgrounds.forward()
            elif code == DOWN:
                backgrounds.backward()
            elif code == RIGHT:
                foregrounds.forward()
            elif code == LEFT:
                foregrounds.backward()


    def handle_event(self, data):
        global delay_update
        update = False
        ds = data.split()
        if ds[0] == b'MOUSEBUTTONDOWN':
            update = self.handle_mousebuttondown(ds)
        elif ds[0] == b'KEYDOWN':
            update = self.handle_keydown(ds)

        if update:
            if delay_update == 0:
                life.update()
            else:
                delay_update -= 1

    def make_size(self, x, y, d):
        return [ (x//256), (x%256), (y//256), (y%256), d]

    def make_image(self):
        # 256 x 256, grayscale: [ 1, 0, 1, 0, 1]
        size = self.make_size(self.width, self.height, self.depth)
        log(3, size)
        # So we're sending ARGB. Strange.
        s = Surface(self.width, self.height, self.depth)
        s.clear(backgrounds.current())
        life.draw(s)
        return bytearray(size + s.data) # TODO: make size part of Surface

if __name__ == '__main__':
    import sys
    VERBOSITY, HOST, PORT = parse(sys.argv[1:])

    print("HOST: %s  PORT: %d  VERBOSITY: %d" % (HOST, PORT, VERBOSITY))

    tcp_server = socketserver.TCPServer((HOST, PORT), TheRequestHandler)
    tcp_server.serve_forever()
