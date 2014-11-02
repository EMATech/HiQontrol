#!/usr/bin/python
#*- coding: utf-8 -*
__author__ = 'Raphaël Doursenaud'

import hiqnet
import logging
import threading
import socket
try:
    import socketserver
except ImportError:
    import SocketServer as socketserver

SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_MAC = '00-17-24-82-06-53'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

# TODO: add configuration for MY_DEVICE* parameters
MY_DEVICE_NAME = 'HiQontrolCLI'
# FIXME: this should be assigned automatically
MY_DEVICE_ADDRESS = 2376

def init_logging():
    """
    Initialize logging
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch.setFormatter(formatter)

    logger.addHandler(ch)

    logger.info('Initialized logging')

    return logger


def server(my_device):
    socketserver.UDPServer.allow_reuse_address = True
    socketserver.TCPServer.allow_reuse_address = True

    udpserver = socketserver.ThreadingUDPServer(('255.255.255.255', hiqnet.IP_PORT), hiqnet.UDPHandler)
    # FIXME: derive address from device
    tcpserver = socketserver.ThreadingTCPServer((my_device.network_info.ip_address, hiqnet.IP_PORT), hiqnet.TCPHandler)

    # TODO: receive meter messages
    #meterserver = socketserver.ThreadingUDPServer((my_device.network_info.ip_address, '3333'), meterHandler)

    udpthread = threading.Thread(target=udpserver.serve_forever)
    tcpthread = threading.Thread(target=tcpserver.serve_forever)

    try:
        udpthread.start()
        tcpthread.start()
        logger.info("Servers started")
        logger.info("UDP: " + udpthread.name)
        logger.info("TCP: " + tcpthread.name)
    except (KeyboardInterrupt, SystemExit):
        udpserver.shutdown()
        tcpserver.shutdown()


def hello(source_device, destination_device):
    c = hiqnet.Connection()
    source_address = hiqnet.FQHiQnetAddress(device_address=source_device.hiqnet_address)
    destination_address = hiqnet.FQHiQnetAddress(device_address=destination_device)
    message = hiqnet.HiQnetMessage(source=source_address, destination=hiqnet.FQHiQnetAddress.broadcastAddress())
    message.DiscoInfo(device=source_device)
    c.udpsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    c.sendto(message, '<broadcast>')
    c.sendto(message, '<broadcast>')
    c.sendto(message, '<broadcast>')
    c.sendto(message, '<broadcast>')
    c.sendto(message, '<broadcast>')
    logger.info("Sent DiscoInfo")

    #message = hiqnet.HiQnetMessage(source=source_address, destination=destination_address)
    #message.LocateOnSI_COMPACT_16_SERIAL)
    #c.sendto(message, SI_COMPACT_16_IP)
    #logger.info("Sent Locate ON")

    #message = hiqnet.HiQnetMessage(source=source_address, destination=destination_address)
    #message.Hello(source_device)
    #c.sendto(message, SI_COMPACT_16_IP)
    #logger.info("Sent Hello")

if __name__ == '__main__':
    logger = init_logging()
    logger.info("RUN")
    my_device = hiqnet.Device(MY_DEVICE_NAME, MY_DEVICE_ADDRESS)
    logger.debug(my_device.network_info.mac_address)
    logger.debug(my_device.network_info.ip_address)
    logger.debug(my_device.network_info.subnet_mask)
    logger.debug(my_device.network_info.gateway_address)
    server(my_device)
    hello(my_device, SI_COMPACT_16_DEVICE_ADDRESS)
