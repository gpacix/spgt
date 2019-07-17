#!/usr/bin/env python3
import pygame
import socket
import time

from parsearguments import parse

BLUE=pygame.Color(0,0,255)
ESC=27

def log(level, *rest):
    if VERBOSITY >= level:
        print('client: ', *rest)

class App:
    def __init__(self):
        self._running = True
        self._display_surf = None
        self.size = self.width, self.height = 640, 480
 
    def on_init(self):
        pygame.init()
        self._display_surf = pygame.display.set_mode(self.size, pygame.DOUBLEBUF) # pygame.HWSURFACE | 
        self._running = True
 
    def on_event(self, event):
        if event.type == pygame.QUIT:
            self._running = False
            return
        if event.type != pygame.MOUSEMOTION:
            log(1, event, event.type)
        msg = None
        if event.type == pygame.MOUSEBUTTONDOWN:
            msg = bytes('MOUSEBUTTONDOWN %s %s' % (event.pos, event.button), 'ascii')
        elif event.type == pygame.KEYDOWN: # unicode, key, mod
            if event.key == ESC:
                self._running = False
                return
            msg = bytes('KEYDOWN %s %s %s' % (event.key, event.mod, event.unicode), 'utf-8')
        if msg is not None:
            s.send(msg)
            z = s.recv(5)  # Warning: optimistic!
            rsize = (z[0]*256 + z[1])*(z[2]*256 + z[3])*z[4]
            data = self.receive_all(s, rsize)
            self.display_data(z, data)
            log(2, "Received: %d %s" % (len(data), data[:100]))
            

    def receive_all(self, s, rsize):
        r = []
        while len(r) < rsize:
            r += s.recv(rsize)
        return bytes(r)


    def on_loop(self):
        pass
    def on_render(self):
        pass
    def on_cleanup(self):
        pygame.quit()
 
    def display_data(self, z, data):
        log(2, "z has %d bytes" % len(z))
        width = z[0]*256 + z[1]
        height = z[2]*256 + z[3]
        color_mode = z[4]
        log(1, "width: %d  height: %d  color_mode: %d" % (width, height, color_mode))
        buf = self._display_surf.get_buffer()
        #self._display_surf.fill(pygame.Color(data[0],data[0],data[0]), (0,0,width,height))
        buf.write(data)
        self._display_surf.unlock()
        pygame.display.update()

    def on_execute(self):
        if self.on_init() == False:
            self._running = False
 
        while( self._running ):
            for event in pygame.event.get():
                self.on_event(event)
            self.on_loop()
            self.on_render()
        self.on_cleanup()
 
if __name__ == '__main__':
    import sys
    VERBOSITY, HOST, PORT = parse(sys.argv[1:])
    print("HOST: %s  PORT: %d  VERBOSITY: %d" % (HOST, PORT, VERBOSITY))

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))
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
