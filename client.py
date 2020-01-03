#!/usr/bin/env python3
import pygame
import socket
import time

from parsearguments import parse
from colors import *

# On a Mac, option -> alt and command -> meta
MODIFIERS = [pygame.K_NUMLOCK, pygame.K_CAPSLOCK, pygame.K_SCROLLOCK, pygame.K_RSHIFT, pygame.K_LSHIFT,
             pygame.K_RCTRL, pygame.K_LCTRL, pygame.K_RALT, pygame.K_LALT, pygame.K_RMETA, pygame.K_LMETA,
             pygame.K_LSUPER, pygame.K_RSUPER, pygame.K_MODE]


class Timer:
    def __init__(self):
        self.times = [0.0] * 100
        self.ti = -1
        self.starttime = 0.0

    def stamptime(self):
        t = time.time()
        if self.ti < 0:
            self.ti = 0
            self.starttime = t
        self.times[self.ti] = (t - self.starttime)
        self.ti = (self.ti + 1) % len(self.times)
    
    def printtimes(self):
        print(self.times)

timer = Timer()


def log(level, *rest):
    if VERBOSITY >= level:
        print('client: ', *rest)

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 0, 0
        self.rapid_fire = False

    def ensure_display(self, width, height, color_mode):
        if self._display_surf is None:
            self.size = self.width, self.height = width, height
            self._display_surf = pygame.display.set_mode(self.size, pygame.HWSURFACE | pygame.DOUBLEBUF)
        return self._display_surf

    def on_init(self):
        pygame.init()
        msg = bytes('KEYDOWN 32 0  ', 'ascii')
        self.send_message(msg)
        self._running = True

    def receive_frame(self):
        z = self.receive_all(sock, 5)  # Warning: optimistic!
        log(3, "recv complete: %s" % z)
        timer.stamptime()
        rsize = (z[0]*256 + z[1])*(z[2]*256 + z[3])*z[4]
        data = self.receive_all(sock, rsize)
        timer.stamptime()
        self.display_data(z, data)
        timer.stamptime()
        log(2, "Received: %d %s" % (len(data), data[:100]))

    def send_message(self, msg):
        while True:
            log(3, "sending %s" % msg)
            timer.stamptime()
            sock.send(msg)
            log(3, "awaiting recv...")
            timer.stamptime()
            self.receive_frame()
            if not self.rapid_fire:
                break
            e = pygame.event.poll()
            while e and self.rapid_fire:
                log(2, e, e.type)
                if e.type == pygame.KEYUP and e.key == pygame.K_SPACE and not (e.mod & pygame.KMOD_SHIFT):
                    self.rapid_fire = False
                    break
                e = pygame.event.poll()
            #time.sleep(0.03)

    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
            return
        if event.type not in [pygame.MOUSEMOTION, pygame.ACTIVEEVENT]:
            log(2, event, event.type)
        msg = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            msg = bytes('MOUSEBUTTONDOWN %s %s' % (event.pos, event.button), 'ascii')
        elif event.type == pygame.KEYDOWN and event.key not in MODIFIERS: # unicode, key, mod
            if event.key == pygame.K_ESCAPE:
                self._running = False
                return
            elif event.key == pygame.K_SPACE and (event.mod & pygame.KMOD_SHIFT):
                self.rapid_fire = True
            elif event.key == pygame.K_p:
                timer.printtimes()
            msg = bytes('KEYDOWN %s %s %s' % (event.key, event.mod, event.unicode), 'utf-8')
        if msg is not None:
            log(1, "%s SENT" % msg)
            self.send_message(msg)

    def receive_all(self, sock, rsize):
        r = []
        while len(r) < rsize:
            r += sock.recv(rsize)
        return bytes(r)


    def on_loop(self):
        pass
    def on_render(self):
        pass
    def on_cleanup(self):
        pygame.quit()
 
    def display_data(self, z, data):
        log(2, "z has %d bytes" % len(z))
        log(2, "data has %d bytes" % len(data))
        width = z[0]*256 + z[1]
        height = z[2]*256 + z[3]
        color_mode = z[4]
        log(2, "width: %d  height: %d  color_mode: %d" % (width, height, color_mode))
        buf = self.ensure_display(width, height, color_mode).get_buffer()
        log(2, "buf.length = %d" % buf.length)
        #self._display_surf.fill(pygame.Color(data[0],data[0],data[0]), (0,0,width,height))
        if color_mode == 1:
            data1 = []
            for i in range(len(data)):
                argb = itoargb[data[i]]
                data1 += list(argb)
            data2 = bytes(data1)
            buf.write(data2)
        else:
            buf.write(data)
        self._display_surf.unlock()
        pygame.display.update()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while self._running:
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()
 
if __name__ == '__main__':
    import sys
    vals = {'HOST': "localhost", 'PORT': 9999, 'VERBOSITY': 0}
    vals = parse(sys.argv[1:], vals)
    VERBOSITY, HOST, PORT = vals['VERBOSITY'], vals['HOST'],  vals['PORT']
    print("HOST: %s  PORT: %d  VERBOSITY: %d" % (HOST, PORT, VERBOSITY))

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((HOST, PORT))
    theApp = App()
    theApp.on_execute()


"""Event types:
QUIT              none
ACTIVEEVENT       gain, state

KEYDOWN           unicode, key, mod
KEYUP             key, mod

MOUSEBUTTONDOWN   pos, button
MOUSEBUTTONUP     pos, button
MOUSEMOTION       pos, rel, buttons

JOYAXISMOTION     joy, axis, value
JOYBALLMOTION     joy, ball, rel
JOYHATMOTION      joy, hat, value
JOYBUTTONUP       joy, button
JOYBUTTONDOWN     joy, button

VIDEORESIZE       size, w, h
VIDEOEXPOSE       none

USEREVENT         code
"""
