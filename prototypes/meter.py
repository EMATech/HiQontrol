#!/usr/bin/python
# *- coding: utf-8 -*
"""Prototype UDP packet sniffer for soundcraft VU meter protocol."""

from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

import socket
import sys
import binascii

IPV4 = ''
PORT = 3333


def main(argv):
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
    s.bind((IPV4, PORT))

    while True:
        packet, address = s.recvfrom(65536)
        parse_packet(packet)


# noinspection PyArgumentList
def parse_packet(packet):
    print("Packet size: ", end="")
    print(sys.getsizeof(packet))
    print("Packet content: ", end="")
    print(binascii.hexlify(packet))

if __name__ == "__main__":
    main(sys.argv)
