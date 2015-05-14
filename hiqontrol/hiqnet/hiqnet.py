# -*- coding: utf-8 -*-

__author__ = 'Raphaël Doursenaud'

import itertools
import struct
import os
import netifaces
import socket
import random
import binascii

from twisted.internet import protocol

IP_PORT = 3804  # IANA declared as IQnet. Go figure.

PROTOCOL_VERSION = b'\x02'

MIN_HEADER_LEN = 25  # bytes

DEFAULT_HOP_COUNTER = b'\x05'

DEFAULT_FLAG_MASK = b'\x01\xff'

DEFAULT_KEEPALIVE = 10000  # ms

ETHERNET_NETWORK_ID = b'\x01'

FLAG_REQACK     = b'\x00\x01'
FLAG_ACK        = b'\x00\x02'
FLAG_INFO       = b'\x00\x04'
FLAG_ERROR      = b'\x00\x08'
FLAG_GUAR       = b'\x00\x20'
FLAG_MULTIPART  = b'\x00\x40'
FLAG_SESSION    = b'\x01\x00'

MSG_DISCOINFO            = b'\x00\x00'
MSG_RESERVED0            = b'\x00\x01'
MSG_GETNETINFO           = b'\x00\x02'
MSG_RESERVED1            = b'\x00\x03'
MSG_REQADDR              = b'\x00\x04'
MSG_ADDRUSED             = b'\x00\x05'
MSG_SETADDR              = b'\x00\x06'
MSG_GOODBYE              = b'\x00\x07'
MSG_HELLO                = b'\x00\x08'
MSG_MULTPARMSET          = b'\x01\x00'
MSG_MULTOBJPARMSET       = b'\x01\x01'
MSG_PARMSETPCT           = b'\x01\x02'
MSG_MULTPARMGET          = b'\x01\x03'
MSG_GETATTR              = b'\x01\x0d'
MSG_SETATTR              = b'\x01\x0e'  # Reverse engineered. Not part of the official spec.
MSG_MULTPARMSUB          = b'\x01\x0f'
MSG_PARMSUBPCT           = b'\x01\x11'
MSG_MULTPARMUNSUB        = b'\x01\x12'
MSG_PARMSUBALL           = b'\x01\x13'
MSG_PARMUNSUBALL         = b'\x01\x14'
MSG_SUBEVTLOGMSGS        = b'\x01\x15'
MSG_GETVDLIST            = b'\x01\x1a'
MSG_STORE                = b'\x01\x24'
MSG_RECALL               = b'\x01\x25'
MSG_LOCATE               = b'\x01\x29'
MSG_UNSUBEVTLOGMSGS      = b'\x01\x2b'
MSG_REQEVTLOG            = b'\x01\x2c'

# HiQnet structure
# Node (Device)
#  \- At least one virtual device (The first is the device manager)
#     \- Parameters and/or objects
#                              \- Objects contains parameters and/or other objects
#
# Attributes everywhere
#   Either STATIC, Instance or Instance+Dynamic
#
# Virtual devices, objects and parameters
#   Have a Class Name and a Class ID


class Attribute:
    # FIXME: Use it?
    type = None
    allowed_types = [
        'STATIC',
        'Instance',
        'Instance+Dynamic'
    ]

    def __init__(self, atr_type):
        if atr_type in self.allowed_types:
            self.type = atr_type
            return
        raise ValueError


class Parameter:
    data_type = None  # STATIC FIXME: needs doc
    name_string = ''  # Instance+Dynamic
    minimum_value = None  # Depends on data_type
    maximum_value = None  # Depends on data_type
    control_law = None
    flags = 0
    """
    Bits 0, 2, and 3 are reserved. Bit 1 is the Sensor Attribute.
        0 = Non-Sensor
        1 = Sensor
    """


class NetworkInfo:
    """
    IPv4 Network informations
    """
    mac_address = None
    dhcp = True
    ip_address = None
    subnet_mask = None
    gateway = None

    def __init__(self,
                 mac_address,
                 dhcp,
                 ip_address,
                 subnet_mask,
                 gateway_address='0.0.0.0'):
        self.mac_address = mac_address
        self.dhcp = dhcp
        self.gateway_address = gateway_address
        self.ip_address = ip_address
        self.subnet_mask = subnet_mask

    @classmethod
    def autodetect(cls):
        """
        Get infos from the interface

        We assume that interface to the default gateway is the one we want
        """
        # FIXME: this may fail
        iface = netifaces.gateways()['default'][netifaces.AF_INET][1]
        addrs = netifaces.ifaddresses(iface)
        mac_address = addrs[netifaces.AF_LINK][0]['addr']
        try:
            mac_address.decode('ascii')
        except UnicodeDecodeError:
            # We got Garbage (Android bug?), let's default to something sane
            mac_address = '00:00:00:00:00:00'
        except AttributeError:
            # We are running Python 3
            try:
                bytes(mac_address, 'ascii')
            except UnicodeDecodeError:
                # We got Garbage (Android bug?), let's default to something sane
                mac_address = '00:00:00:00:00:00'
        ip_address = addrs[netifaces.AF_INET][0]['addr']
        subnet_mask = addrs[netifaces.AF_INET][0]['netmask']
        gateway_address = netifaces.gateways()['default'][netifaces.AF_INET][0]
        # Seems impossible to know. Let's say it is.
        dhcp = True
        return cls(mac_address, dhcp, ip_address, subnet_mask, gateway_address)


class VirtualDevice:
    """
    Describes a HiQnet virtual device

    This is the basic container object type
    """
    class_name = None  # STATIC
    name_string = None  # Instance+Dynamic


class DeviceManager(VirtualDevice):
    """
    Describes a HiQnet device manager

    Each device has one and this is always the first virtual device
    """
    flags = DEFAULT_FLAG_MASK
    serial_number = None
    software_version = None

    def __init__(self,
                 name_string,
                 class_name=None,
                 flags=DEFAULT_FLAG_MASK,
                 serial_number=None,
                 software_version=None):
        """
        class_name:
            The device's registered hiqnet type.
        name_string
            The device name. This can be changed by the user
        """
        if not class_name:
            class_name = name_string
        self.class_name = class_name
        self.name_string = name_string
        self.flags = flags
        if not serial_number:
            serial_number = name_string
        self.serial_number = serial_number
        self.software_version = software_version


class FQHiQnetAddress:
    """
    Fully Qualified HiQnet Address
    """
    def __init__(self,
                 device_address=0,
                 vd_address=b'\x00',  # 8 bits
                 object_address=b'\x00\x00\x00',  # 24 bits
                 ):
        self.device_address = device_address
        # TODO: make vd_address and object_address int rather than byte arrays
        self.vd_address = vd_address
        self.object_address = object_address

    @classmethod
    def broadcast_address(cls):
        return cls(device_address=65535, vd_address=b'\x00', object_address=b'\x00\x00\x00')

    def __bytes__(self):
        return struct.pack('!H', self.device_address) + self.vd_address + self.object_address

    def __str__(self):
        return self.__bytes__()


class HiQnetMessage:
    """
    HiQnet message
    """
    # Placeholder, will be filled later
    header = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    version = PROTOCOL_VERSION  # 1 byte
    """
    The Version Number indicates the revision number of the entire protocol; it is not
    used for differentiating between revisions of individual messages. HiQnet is
    currently at revision 2. Devices that communicate with HiQnet version 1.0
    include the dbx ZonePro family. All others use version 2.0.
    """
    headerlen = struct.pack('!B', MIN_HEADER_LEN)  # 1 byte
    """
    The Header Length is the size in bytes of the entire message header, including any
    additional headers such as 'Error' or 'Multi-part'.
    """
    messagelen = b'\x00\x00\x00\x00'  # 4 bytes
    """
    The Message Length is the size in bytes of the entire message - from the
    ‘Version’ field through to the last byte of the payload.
    """
    source_address = FQHiQnetAddress()  # 6 byte (48 bits)
    """
    The Source Address specifies the HiQnet address where the message has come
    from; this is often used by the recipient for sending back reply messages.
    """
    destination_address = FQHiQnetAddress()  # 6 byte (48 bits)
    """The Destination Address specifies where the message is to be delivered to."""
    message_id = b'\x00\x00'  # 2 bytes
    """
    The Message ID is a unique identifier that indicates the method that the
    destination Device must perform. If there is a payload, it is usually specific to the
    type of method indicated by the Message ID. Product-specific IDs may also exist
    and will be documented appropriately.
    """
    flags = b'\x00\x00'  # 2 bytes
    """
    The Flags denote what kinds of options are active when set to ‘1’ and are
    allocated in the following manner:
    +----------+-------------------+----------+--------------------+------------+----------+--------------------+
    | Bit 15-9 | Bit 8             | Bit 7    | Bit 6              | Bit 5      | Bit 4    | Bit 3              |
    +----------+-------------------+----------+--------------------+------------+----------+--------------------+
    | Reserved | Session number    | Reserved | Multi-part message | Guaranteed | Reserved | Error              |
    |          |(Header extension) |          |(Header extension)  |            |          | (Header extension) |
    +----------+--+----------------++---------+---------------+----+------------+----------+--------------------+
    | Bit 2       | Bit 1           | Bit 0                   |
    +-------------+-----------------+-------------------------+
    | Information | Acknowledgement | Request Acknowledgement |
    +-------------+-----------------+-------------------------+
    Bit 5 must be set for any applications using TCP/IP only on the network
    interface. This will ensure that any messages are sent guaranteed (TCP rather
    than UDP).
    """
    hop_counter = DEFAULT_HOP_COUNTER  # 1 byte
    """
    The Hop Count denotes the number of network hops that a message has traversed
    and is used to stop broadcast loops. This field should generally be defaulted to
    0x05.
    """
    new_sequence_number = itertools.count()
    sequence_number = b'\x00\x00'  # 2 bytes
    """
    The Sequence number is used to uniquely identify each HiQnet message leaving a
    Device. This is primarily used for diagnostic purposes. The sequence number
    starts at 0 on power-up and increments for each successive message the Routing
    Layer sends to the Packet Layer. The Sequence Number rolls over at the top of its
    range.
    """

    optional_headers = b''  # Placeholder, may not be filled

    payload = b''  # Placeholder, filled later, depends on the message

    def __init__(self, source, destination):
        self.source_address = source
        self.destination_address = destination
        self.sequence_number = struct.pack('!H', next(self.new_sequence_number))

    def disco_info(self, device):
        self.message_id = MSG_DISCOINFO
        # Payload
        device_address = struct.pack('!H', self.source_address.device_address)
        cost = b'\x01'
        serial_number_len = struct.pack('!H', 16)
        try:
            serial_number = bytes(device.manager.serial_number.decode('ascii'))
        except AttributeError:
            # We are running Python 3
            serial_number = bytes(device.manager.serial_number, 'ascii')
        serial_number = struct.pack('!16s', serial_number)  # May use utf-16-be == UCS-2
        max_message_size = struct.pack('!I', 65535)  # FIXME: should really be the server's buffer size
        keep_alive_period = struct.pack('!H', DEFAULT_KEEPALIVE)
        network_id = ETHERNET_NETWORK_ID
        mac_address = binascii.unhexlify(device.network_info.mac_address.replace(':', ''))
        dhcp = struct.pack('!B', device.network_info.dhcp)
        ip_address = socket.inet_aton(device.network_info.ip_address)
        subnet_mask = socket.inet_aton(device.network_info.subnet_mask)
        gateway_address = socket.inet_aton(device.network_info.gateway_address)
        self.payload = device_address + cost + serial_number_len + serial_number \
            + max_message_size + keep_alive_period + network_id \
            + mac_address + dhcp + ip_address + subnet_mask + gateway_address

    def request_address(self, req_addr):
        self.message_id = MSG_REQADDR
        self.payload = struct.pack('!H', req_addr)

    def address_used(self):
        self.message_id = MSG_ADDRUSED

    def hello(self):
        self.message_id = MSG_HELLO
        session_number = os.urandom(2)
        flag_mask = DEFAULT_FLAG_MASK
        self.payload = session_number + flag_mask
        return session_number

    def get_attributes(self):
        self.message_id = MSG_GETATTR

    def get_vd_list(self):
        self.message_id = MSG_GETVDLIST

    def store(self):
        self.message_id = MSG_STORE

    def recall(self):
        self.message_id = MSG_RECALL

    def locate(self, time, serial_number):
        """
        :param time: time the leds should flash in ms
                     0x0000 turns off locate led(s)
                     0xffff turns on locate led(s)
        :return: void
        """
        self.message_id = MSG_LOCATE
        serial_number_len = struct.pack('!H', len(serial_number))
        self.payload = time + serial_number_len + serial_number

    def locate_on(self, serial_number):
        self.locate(b'\xff\xff', serial_number)

    def locate_off(self, serial_number):
        self.locate(b'\x00\x00', serial_number)

    def _build_optional_headers(self):
        # Optional error header
        if struct.unpack('!H', self.flags)[0] & struct.unpack('!H', FLAG_ERROR)[0]:
            error_code = b'\x02'
            error_string = b''
            self.optional_headers += error_code + error_string
        # Optional multi-part header
        if struct.unpack('!H', self.flags)[0] & struct.unpack('!H', FLAG_MULTIPART)[0]:
            start_seq_no = b'\x02'
            bytes_remaining = b'\x00\x00\x00\x00'  # 4 bytes
            self.optional_headers += start_seq_no + bytes_remaining
        # Optional session number header
        if struct.unpack('!H', self.flags)[0] & struct.unpack('!H', FLAG_SESSION)[0]:
            session_number = b'\x00\x00'  # 2 bytes
            self.optional_headers += session_number

    def _compute_headerlen(self):
        headerlen = MIN_HEADER_LEN + len(self.optional_headers)
        self.headerlen = struct.pack('!B', headerlen)

    def _compute_messagelen(self):
        messagelen = len(self.payload) + struct.unpack('!B', self.headerlen)[0]
        self.messagelen = struct.pack('!I', messagelen)

    def _build_header(self):
        self._build_optional_headers()
        self._compute_headerlen()
        self._compute_messagelen()
        self.header = self.version + self.headerlen + self.messagelen \
            + bytes(self.source_address) + bytes(self.destination_address) \
            + self.message_id + self.flags + self.hop_counter + self.sequence_number + self.optional_headers

    def __bytes__(self):
        self._build_header()
        return self.header + self.payload

    def __str__(self):
        return self.__bytes__()

# TODO: Event logs
# TODO: Session

# TODO: Device arrival announce


class Device:
    """
    Describes a device or node
    """
    hiqnet_address = None
    network_info = NetworkInfo.autodetect()
    manager = None

    def __init__(self, name, hiqnet_address):
        self.manager = DeviceManager(name)
        self.hiqnet_address = hiqnet_address

    @staticmethod
    def negotiate_address():
        """
        Generates a random HiQnet address to datastore and reuse on the device

        The address is automatically checked on the network
        """
        requested_address = random.randrange(1, 65535)
        # connection = Connection()
        # message = HiQnetMessage(source=FQHiQnetAddress(device_address=0),
        #                        destination=FQHiQnetAddress.broadcast_address())
        # message.request_address(self, requested_address)
        # connection.sendto('<broadcast>')
        # FIXME: look for address_used reply messages and renegotiate if found
        return requested_address


class Connection:
    udp_transport = None
    tcp_transport = None

    def __init__(self, udp_transport, tcp_transport):
        self.udp_transport = udp_transport
        self.tcp_transport = tcp_transport

    def sendto(self, message, destination):
        if struct.unpack('!H', message.flags)[0] & struct.unpack('!H', FLAG_GUAR)[0]:
            # Send TCP message if the Guaranteed flag is set
            self.tcp_transport.write(bytes(message), (destination, IP_PORT))
        else:
            self.udp_transport.write(bytes(message), (destination, IP_PORT))


class HiQnetTCPProtocol(protocol.Protocol):
    def startProtocol(self):
        """
        Called after protocol started listening
        :return:
        """
        self.factory.app.tcp_transport = self.transport

    def dataReceived(self, data):
        print("Received TCP data: ")
        print(binascii.hexlify(data))

        # TODO: Process some more :)
        self.factory.app.handle_message(data, None, "HiQnet TCP")


class HiQnetUDPProtocol(protocol.DatagramProtocol):
    def __init__(self, app):
        self.app = app

    def startProtocol(self):
        """
        Called after protocol started listening
        :return:
        """
        self.transport.setBroadcastAllowed(True)  # Some messages needs to be broadcasted
        self.app.udp_transport = self.transport

    def datagramReceived(self, data, addr):
        (host, port) = addr
        print("Received UDP data: ")
        print(binascii.hexlify(data))
        print("from: ")
        print(host)
        print("on port:")
        print(port)

        # TODO: Process some more :)
        self.app.handle_message(data, host, "HiQnet UDP")


class HiQnetFactory(protocol.Factory):
    protocol = HiQnetTCPProtocol

    def __init__(self, app):
        self.app = app
