#!/usr/bin/env python3

import socketserver
import random
ri = random.randint

current = 128
color_offset = 3 # 3=blue, 2=green, 1=red
YELLOW = [255,255,255,0]
WHITE =  [0,255,255,255]
BLACK =  [0,0,0,0]
GRAY  =  [0,128,128,128]
ORANGE = [0, 255, 192, 128]
RED    = [0, 255, 0, 0]
GREEN  = [0, 0, 255, 0]
BLUE   = [0, 0, 0, 255]

foregrounds = [RED, GREEN, BLUE, ORANGE]
backgrounds = [BLACK, WHITE, YELLOW, ORANGE, GRAY]
fgi = 0
bgi = 0

UP, DOWN, RIGHT, LEFT = 273, 274, 275, 276

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
        self.w = w
        self.h = h
        self.d = d
        self.clear([0,0,0,0])

    def clear(self, color):
        self.data = color * (self.w * self.h)

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

SC = 12
SZ=480//SC  

def draw_life(s, current):
    #c = (255, 192, 128, 0)
    c = foregrounds[fgi]
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
    for x in range(0,SZ):
        for y in range(0,SZ):
            left, right = (x - 1) % SZ, (x + 1) % SZ
            up, down    = (y - 1) % SZ, (y + 1) % SZ
            neighbors = (life[left][y-1] +  life[left][y]  + life[left][down] +
                         life[x   ][y-1] +                   life[x  ][down] +
                         life[right][y-1] + life[right][y] + life[right][down] )
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
        global life
        x = int(ds[1][1:-1])
        y = int(ds[2][:-1])
        lifex = x//SC
        lifey = y//SC
        if lifex < SZ and lifey < SZ:
            life[lifex][lifey] = 1 - life[lifex][lifey]
        #global current
        #if x < self.width/3:
        #    current -= 16
        #elif x > 2*self.width/3:
        #    current += 16
        #elif y < self.height/3:
        #    global color_offset
        #    color_offset = (color_offset % 3) + 1
        #current = current % 256

    def handle_keydown(self, ds):
        global bgi, fgi
        code = int(ds[1])
        if ds[2] == b'f':
            pass
        if code == 32:
            log(1, "space")
            return True
        if code in [UP, DOWN, RIGHT, LEFT]:
            if code == UP:
                bgi = (bgi+1) % len(backgrounds)
            elif code == DOWN:
                bgi = (bgi-1) % len(backgrounds)
            elif code == RIGHT:
                fgi = (fgi+1) % len(foregrounds)
            elif code == LEFT:
                fgi = (fgi-1) % len(foregrounds)

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
                update_life()
            else:
                delay_update -= 1

    def make_image(self):
        # 256 x 256, grayscale: [ 1, 0, 1, 0, 1]
        x,y,d = self.width, self.height, self.depth
        size = [ (x//256), (x%256), (y//256), (y%256), d]
        log(3, size)
        # So we're sending ARGB. Strange.
        s = Surface(x, y, d)
        s.clear(backgrounds[bgi])
        draw_life(s, current)
        log(4, "current is now ", current)
        return bytearray(size + s.data) # TODO: make size part of Surface

if __name__ == '__main__':
    HOST, PORT = "localhost", 9999
    VERBOSITY = 2
    tcp_server = socketserver.TCPServer((HOST, PORT), TheRequestHandler)
    tcp_server.serve_forever()
