#!/usr/bin/python

__author__ = 'Raphaël Doursenaud'

import hiqnet
import logging
import threading
import socket
import socketserver

SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_MAC = '00-17-24-82-06-53'
SI_COMPACT_16_DEVICE_ADDRESS = '1619'  # 0x653
SI_COMPACT_16_SERIAL = '5369436f6d7061637400000000000000'  # Hex encoded (SiCompact)

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


def server():
    socketserver.UDPServer.allow_reuse_address = True
    socketserver.TCPServer.allow_reuse_address = True

    udpserver = socketserver.ThreadingUDPServer(('localhost', hiqnet.IP_PORT), hiqnet.UDPHandler)
    tcpserver = socketserver.ThreadingTCPServer(('localhost', hiqnet.IP_PORT), hiqnet.TCPHandler)

    udpthread = threading.Thread(target=udpserver.serve_forever)
    tcpthread = threading.Thread(target=tcpserver.serve_forever)

    try:
        udpthread.start()
        tcpthread.start()
        logging.info("Servers started")
        logging.info("UDP:", udpthread.name)
        logging.info("TCP:", tcpthread.name)
    except KeyboardInterrupt:
        udpserver.shutdown()
        tcpserver.shutdown()


def hello(source_device, destination_device):
    c = hiqnet.Connection()
    source_address = hiqnet.FQHiQnetAddress(device_address=source_device.hiqnet_address)
    destination_address = hiqnet.FQHiQnetAddress(device_address=destination_device)
    message = hiqnet.HiQnetMessage(source=source_address)
    message.DiscoInfo(device=source_device)
    # TODO: write a send method that will infer the INFO flag and choose UDP or TCP accordingly
    c.udpsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    c.udpsock.sendto(bytes(message), ('<broadcast>', hiqnet.IP_PORT))
    logger.info("Sent DiscoInfo")
    #message.Hello(source_device)
    #c.udpsock.sendto(bytes(message), (SI_COMPACT_16_IP, hiqnet.IP_PORT))
    #logger.info("Sent Hello")

if __name__ == '__main__':
    logger = init_logging()
    logger.info("RUN")
    my_device = hiqnet.DeviceManager()
    logger.debug(my_device.class_name)
    logger.debug(my_device.name_string)
    logger.debug(my_device.serial_number)
    logger.debug(my_device.software_version)
    logger.debug(my_device.mac_address)
    logger.debug(my_device.ip_address)
    logger.debug(my_device.subnet_mask)
    logger.debug(my_device.gateway_address)
    hello(my_device, SI_COMPACT_16_DEVICE_ADDRESS)


