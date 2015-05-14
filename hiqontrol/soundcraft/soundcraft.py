# -*- coding: utf-8 -*-

__author__ = 'Raphaël Doursenaud'

import binascii
from twisted.internet import protocol

VUMETER_IP_PORT = 3333


class VuMeterUDPPRotocol(protocol.DatagramProtocol):
    def __init__(self, app):
        self.app = app

    def datagramReceived(self, data, addr):
        (host, port) = addr
        print("Received VU meter UDP data: ")
        print(binascii.hexlify(data))
        print("from: ")
        print(host)
        print("on port:")
        print(port)

        # TODO: Process some more :)
        self.app.handle_message(data, host, "Soundcraft UDP")
