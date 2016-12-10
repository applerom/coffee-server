#!/usr/bin/env python

import SocketServer
import EslHandler
import logging
import vars
logging.basicConfig(level=vars.LOG_LEVEL, format='%(name)s: %(message)s', )

class EslSocketServer(SocketServer.TCPServer):
    def __init__(self, server_address, handler_class=EslHandler):
        self.logger = logging.getLogger('EslProxyServer')
        #self.logger.debug('__init__')
        SocketServer.TCPServer.__init__(self, server_address, handler_class)
        return

    def server_activate(self):
        #self.logger.debug('server_activate')
        SocketServer.TCPServer.server_activate(self)
        return

    def serve_forever(self):
        #self.logger.debug('waiting for request')
        #self.logger.info('Handling requests, press <Ctrl-C> to quit')
        while 1:
            self.handle_request()
        return

    def handle_request(self):
        #self.logger.debug('handle_request')
        return SocketServer.TCPServer.handle_request(self)

    def verify_request(self, request, client_address):
        #self.logger.debug('verify_request(%s, %s)', request, client_address)
        return SocketServer.TCPServer.verify_request(self, request, client_address)

    def process_request(self, request, client_address):
        #self.logger.debug('process_request(%s, %s)', request, client_address)
        return SocketServer.TCPServer.process_request(self, request, client_address)

    def server_close(self):
        #self.logger.debug('server_close')
        return SocketServer.TCPServer.server_close(self)

    def finish_request(self, request, client_address):
        #self.logger.debug('finish_request(%s, %s)', request, client_address)
        return SocketServer.TCPServer.finish_request(self, request, client_address)

    def close_request(self, request_address):
        #self.logger.debug('close_request(%s)', request_address)
        return SocketServer.TCPServer.close_request(self, request_address)
        
    #timeout = 2 # only for SocketServer.TCPServer! It does NOT work in RequestHandler.handle() !
    
    def handle_timeout(self):
        #self.logger.debug('handle_timeout')
        return SocketServer.TCPServer.handle_timeout(self)
