# -*- coding: utf-8 -*-
"""HiQnet IP communication."""

from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

import binascii
from twisted.internet import protocol

from protocol import Message

PORT = 3804  # IANA declared as IQnet. Go figure.


class Connection:
    """Handles HiQnet IP connection.

    .. warning:: Other connection types such as RS232, RS485 or USB are not handled yet.
    """
    udp_transport = None
    tcp_transport = None

    def __init__(self, udp_transport, tcp_transport):
        """Initiate a HiQnet IP connection over UDP and TCP.

        :param udp_transport: Twisted UDP transport
        :type udp_transport: twisted.internet.interfaces.IUDPTransport
        :param tcp_transport: Twisted TCP transport
        :type tcp_transport: twisted.internet.interfaces.ITCPTransport
        :return:
        """
        self.udp_transport = udp_transport
        self.tcp_transport = tcp_transport

    def sendto(self, message, destination='<broadcast>'):
        """Send message to the destination.

        :param message: Message to send
        :type message: Message
        :param destination: Destination IPv4 address or '<broadcast>'
        :type destination: str
        """
        if message.flags.guaranteed:
            # Send TCP message if the Guaranteed flag is set
            # noinspection PyArgumentList
            self.tcp_transport.write(bytes(message), (destination, PORT))
        else:
            # noinspection PyArgumentList
            self.udp_transport.write(bytes(message), (destination, PORT))
        print("=>")  # DEBUG
        print(vars(message))  # DEBUG


# noinspection PyClassHasNoInit
class TCPProtocol(protocol.Protocol):
    """HiQnet Twisted TCP protocol."""

    name = "HiQnetTCP"

    def startProtocol(self):
        """Called after protocol started listening."""
        self.factory.app.tcp_transport = self.transport

    def dataReceived(self, data):
        """Called when data is received.

        :param data: Received binary data
        :type data: bytearray
        """
        # FIXME: debugging output should go into a logger
        print("<=")
        print(self.name + " data:")
        print(binascii.hexlify(data))
        message = Message(message=data)
        print(vars(message))  # DEBUG

        # TODO: Process some more :)
        self.factory.app.handle_message(message, None, self.name)


class UDPProtocol(protocol.DatagramProtocol):
    """HiQnet Twisted UDP protocol."""

    name = "HiQnetUDP"

    def __init__(self, app):
        self.app = app

    def startProtocol(self):
        """Called after protocol started listening."""
        self.transport.setBroadcastAllowed(True)  # Some messages needs to be broadcasted
        self.app.udp_transport = self.transport

    def datagramReceived(self, data, addr):
        """Called when data is received.

        :param data: Received binary data
        :type data: bytearray
        :param addr: IPv4 address and port of the sender
        :type addr: tuple
        """
        (host, port) = addr

        # FIXME: debugging output should go into a logger
        print("<=")
        print(self.name + "data:")
        print(binascii.hexlify(data))
        print("from ", end="")
        print(host, end="")
        print(":", end="")
        print(port)
        message = Message(message=data)
        print(vars(message))  # DEBUG

        # TODO: Process some more :)
        self.app.handle_message(message, host, self.name)


class Factory(protocol.Factory):
    """HiQnet Twisted Factory."""

    protocol = TCPProtocol

    def __init__(self, app):
        self.app = app
