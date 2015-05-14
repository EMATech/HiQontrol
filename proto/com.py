#!/usr/bin/python
# *- coding: utf-8 -*
__author__ = 'Raphaël Doursenaud'

import logging
import socket

from hiqontrol.hiqnet import hiqnet


try:
    import socketserver
except ImportError:
    # noinspection PyPep8Naming,PyUnresolvedReferences
    import SocketServer as socketserver

SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_MAC = '00-17-24-82-06-53'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

# TODO: add configuration for MY_DEVICE* parameters
MY_DEVICE_NAME = 'HiQontrolCLI'


def init_logging():
    """
    Initialize logging
    """
    l = logging.getLogger(__name__)
    l.setLevel(logging.DEBUG)

    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    ch.setFormatter(formatter)

    l.addHandler(ch)

    l.info('Initialized logging')

    return l


def hello(source_device, destination_device):
    c = hiqnet.Connection()
    source_address = hiqnet.FullyQualifiedAddress(device_address=source_device.hiqnet_address)
    # destination_address = hiqnet.FullyQualifiedAddress(device_address=destination_device)
    destination_address = hiqnet.FullyQualifiedAddress.broadcast_address()  # Broadcast
    message = hiqnet.Message(source=source_address, destination=destination_address)
    message.disco_info(device=source_device)
    c.udpsock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    c.sendto(message)
    c.sendto(message)
    c.sendto(message)
    c.sendto(message)
    c.sendto(message)
    logger.info("Sent disco_info")

    # message = hiqnet.Message(source=source_address, destination=destination_address)
    # message.LocateOnSI_COMPACT_16_SERIAL)
    # c.sendto(message, SI_COMPACT_16_IP)
    # logger.info("Sent locate ON")
    #
    # message = hiqnet.Message(source=source_address, destination=destination_address)
    # message.hello(source_device)
    # c.sendto(message, SI_COMPACT_16_IP)
    # logger.info("Sent hello")

if __name__ == '__main__':
    logger = init_logging()
    logger.info("RUN")
    my_device_address = hiqnet.Device.negotiate_address()
    my_device = hiqnet.Device(MY_DEVICE_NAME, my_device_address)
    logger.debug(my_device.network_info.mac_address)
    logger.debug(my_device.network_info.ip_address)
    logger.debug(my_device.network_info.subnet_mask)
    logger.debug(my_device.network_info.gateway_address)
    my_device.start_server()
    hello(my_device, SI_COMPACT_16_DEVICE_ADDRESS)
    my_device.stop_server()
