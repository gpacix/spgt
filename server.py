#!/usr/bin/env python3

import socketserver

class TheRequestHandler(socketserver.BaseRequestHandler):
    """ TCP Request handler """

    def handle(self):
        self.data = self.request.recv(1024).strip()
        print("{} sent:".format(self.client_address[0]))
        print(self.data)
        self.request.sendall("ACK from TCP server".encode())

if __name__ == '__main__':
    HOST, PORT = "localhost", 9999
    tcp_server = socketserver.TCPServer((HOST, PORT), TheRequestHandler)
    tcp_server.serve_forever()

