# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

import binascii
from hiqnet import hiqnet

VUMETER_IP_PORT = 3333


class VuMeterUDPPRotocol(hiqnet.UDPProtocol):
    """Soundcraft VU Meter Twisted UDP protocol."""

    def datagramReceived(self, data, addr):
        """Called when data is received.

        :param data: Receive binary data
        :type data: bytearray
        :param addr: IPv4 address and port of the sender
        :type addr: tuple
        """
        (host, port) = addr

        # FIXME: debugging output should go into a logger
        print("Received VU meter UDP data: ")
        print(binascii.hexlify(data))
        print("from ", end="")
        print(host, end="")
        print(":", end="")
        print(port)

        # TODO: Process some more :)
        self.app.handle_message(data, host, "Soundcraft UDP")
