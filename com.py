__author__ = 'Raphaël Doursenaud'

import socket
import sys
import hiqnet

SI_COMPACT_16_IP = '192.168.1.6'

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = (SI_COMPACT_16_IP, hiqnet.HIQNET_IP_PORT)

sock.bind(server_address)

message = hiqnet.HiQnetMessage()

message.locate('0xfff')

sock.sendall(message)
