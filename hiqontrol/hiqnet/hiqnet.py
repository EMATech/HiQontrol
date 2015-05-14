# -*- coding: utf-8 -*-
from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

import itertools
import struct
import os
import netifaces
import socket
import random
import binascii
import ctypes

from twisted.internet import protocol

c_uint16 = ctypes.c_uint16

IP_PORT = 3804  # IANA declared as IQnet. Go figure.

PROTOCOL_VERSION = b'\x02'

MIN_HEADER_LEN = 25  # bytes

DEFAULT_HOP_COUNTER = b'\x05'

DEFAULT_FLAG_MASK = b'\x01\xff'

SUPPORTED_FLAG_MASK = DEFAULT_FLAG_MASK

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

class DeviceFlagsBits(ctypes.LittleEndianStructure):
    """Bitfields for the device flags."""
    _fields_ = [
        ('reqack', c_uint16, 1),
        ('ack', c_uint16, 1),
        ('info', c_uint16, 1),
        ('error', c_uint16, 1),
        ('res1', c_uint16, 1),
        ('guaranteed', c_uint16, 1),
        ('multipart', c_uint16, 1),
        ('res2', c_uint16, 1),
        ('session', c_uint16, 1),
        ('res3', c_uint16, 1),
        ('res4', c_uint16, 1),
        ('res5', c_uint16, 1),
        ('res6', c_uint16, 1),
        ('res7', c_uint16, 1),
        ('res8', c_uint16, 1),
        ('res9', c_uint16, 1),
    ]


class DeviceFlags(ctypes.Union):
    """Device flags."""
    _fields_ = [
        ('b', DeviceFlagsBits),
        ('asByte', c_uint16),
    ]

    _anonymous_ = 'b'

    def __bytes__(self):
        return struct.pack('!H', self.asByte)

    def __str__(self):
        return self.__bytes__()

    def __add__(self, other):
        return str(self) + other

    def __radd__(self, other):
        return other + str(self)


class Attribute:
    """Member variables of the HiQnet architecture.

    Static are basically constants.
    Instance are variables that are set at device bootup.
    Instance+Dynamic are regular variables that can change during the life of the device.
    """
    # FIXME: Use it?
    type = None
    _data_type = None
    _value = None
    _allowed_types = [
        'Static',
        'Instance',
        'Instance+Dynamic'
    ]

    def __init__(self, atr_type):
        """Build an attribute.

        :param atr_type:  The attribute type
        :type atr_type: str
        :return:
        """
        if atr_type in self._allowed_types:
            self.type = atr_type
            return
        raise ValueError

class Object:
    """HiQnet objects.

    May contain other objects or parameters.
    """


class Parameter:
    """HiQnet parameters.

    Represents the manipulable elements and their attributes.
    """
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
    """IPv4 network informations."""
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
        """Network information from a device.

        :param mac_address: MAC address
        :type mac_address: str
        :param dhcp: Address obtained by DHCP
        :type dhcp: bool
        :param ip_address: IPv4 address
        :type ip_address: str
        :param subnet_mask: IPv4 network mask
        :type subnet_mask: str
        :param gateway_address: IPv4 gateway address
        :type gateway_address: str
        :return:
        """
        self.mac_address = mac_address
        self.dhcp = dhcp
        self.gateway_address = gateway_address
        self.ip_address = ip_address
        self.subnet_mask = subnet_mask

    @classmethod
    def autodetect(cls):
        """Get infos from the interface.

        We assume that interface to the default gateway is the one we want.

        :type cls: NetworkInfo
        :rtype: NetworkInfo
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
                # noinspection PyArgumentList
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
    """Describes a HiQnet virtual device.

    This is the basic container object type.
    """
    class_name = Attribute('Static')
    name_string = Attribute('Instance+Dynamic')
    objects = None
    parameters = None
    attributes = None


class DeviceManager(VirtualDevice):
    """Describes a HiQnet device manager.

    Each device has one and this is always the first virtual device.
    """
    flags = DeviceFlags()
    serial_number = None
    software_version = None

    def __init__(self,
                 name_string,
                 class_name=None,
                 flags=0,
                 serial_number=None,
                 software_version=None):
        """Init an HiQnet device manager.

        :param name_string: The device name. This can be changed by the user
        :type name_string: str
        :param class_name: The device's registered hiqnet type.
        :type class_name: str
        :type flags: bytearray
        :type serial_number:
        :type software_version: str
        """
        if not class_name:
            class_name = name_string
        self.class_name = class_name
        self.name_string = name_string
        self.flags.asByte = flags
        if not serial_number:
            serial_number = name_string
        self.serial_number = serial_number
        self.software_version = software_version


class FullyQualifiedAddress:
    """Fully Qualified HiQnet Address."""
    device_address = None
    vd_address = None
    object_address = None

    def __init__(self,
                 devicevdobject=None,
                 device_address=None,
                 vd_address=b'\x00',
                 object_address=b'\x00\x00\x00',
                 ):
        """Build a Fully Qualified HiQnet Address.

        :param devicevdobject: Full binary address
        :type devicevdobject: bytearray
            16 bits = Device address
            8 bits = VD address
            24 bits = Object address
        :param device_address: Device address
        :type device_address: int between 1 and 65535
        :param vd_address:  Virtual device address
        :type vd_address: bytearray 8 bits
        :param object_address:  Object address
        :type object_address: bytearray 24 bits
        """
        if devicevdobject:
            repr(devicevdobject)
            self.device_address = struct.unpack('!H', devicevdobject[0:2])
            # TODO: make vd_address and object_address int rather than byte arrays
            self.vd_address = devicevdobject[2]
            self.object_address = devicevdobject[3:6]
        else:
            self.device_address = device_address
            # TODO: make vd_address and object_address int rather than byte arrays
            self.vd_address = vd_address
            self.object_address = object_address

    @classmethod
    def broadcast_address(cls):
        """Get the Fully Qualified HiQnet Broadcast Address.

        :type cls: NetworkInfo
        :rtype: NetworkInfo
        """
        return cls(device_address=65535, vd_address=b'\x00', object_address=b'\x00\x00\x00')

    def __bytes__(self):
        """Get the address as bytes"""
        # TODO: make vd_address and object_address int rather than byte arrays
        return struct.pack('!H', self.device_address) + self.vd_address + self.object_address

    def __str__(self):
        """Get the address in a printable format"""
        return self.__bytes__()


class Message:
    """HiQnet message"""
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
    source_address = FullyQualifiedAddress()  # 6 byte (48 bits)
    """
    The Source Address specifies the HiQnet address where the message has come
    from; this is often used by the recipient for sending back reply messages.
    """
    destination_address = FullyQualifiedAddress()  # 6 byte (48 bits)
    """The Destination Address specifies where the message is to be delivered to."""
    message_id = b'\x00\x00'  # 2 bytes
    """
    The Message ID is a unique identifier that indicates the method that the
    destination Device must perform. If there is a payload, it is usually specific to the
    type of method indicated by the Message ID. Product-specific IDs may also exist
    and will be documented appropriately.
    """
    flags = DeviceFlags()  # 2 bytes
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

    def __init__(self, message=None, source=None, destination=None):
        """Initiate an HiQnet message from source to destination.

        :param source: Source of the message
        :type source: FullyQualifiedAddress
        :param destination: destination of the message
        :type destination: FullyQualifiedAddress
        :return:
        """
        if message:
            self.decode_message(message)
        else:
            self.source_address = source
            self.destination_address = destination
            self.sequence_number = struct.pack('!H', next(self.new_sequence_number))

    def decode_message(self, message):
        """Decodes a binary message.

        :param message: The binary message to decode
        """
        self.set_version(struct.unpack('!B', message[0])[0])
        self.set_headerlen(struct.unpack('!B', message[1])[0])
        if len(message) < self.headerlen:
            raise BufferError("Message is smaller than it's header length")
        self.set_messagelen(struct.unpack('!L', message[2:6])[0])
        if len(message) != self.messagelen:
            raise BufferError("Message length header and actual length missmatch")
        self.source_address = FullyQualifiedAddress(devicevdobject=message[6:12])
        self.destination_address = FullyQualifiedAddress(devicevdobject=message[12:18])
        self.message_id = message[18:20]  # TODO: decode
        self.flags.asByte = struct.unpack('!H', message[20:22])[0]
        self.hop_counter = struct.unpack('!B', message[22])[0]
        self.sequence_number = struct.unpack('!H', message[23:25])[0]
        if self.headerlen > 25:
            # Optional Headers are present, check the flags
            raise NotImplementedError
        self.payload = message[self.headerlen:self.messagelen]
        # TODO: decode payload by message type

    def set_version(self, version):
        """Set the version."""
        if not 0 < version <= 2:
            raise ValueError("HiQnet version can only be 1 or 2")
        self.version = version

    def set_headerlen(self, headerlen):
        """Set the header length"""
        if headerlen < MIN_HEADER_LEN:
            raise ValueError("The header can't be smaller than " + MIN_HEADER_LEN)
        self.headerlen = headerlen

    def set_messagelen(self, messagelen):
        if messagelen < self.headerlen or messagelen < MIN_HEADER_LEN:
            raise ValueError("Message can't be smaller than the header")
        self.messagelen = messagelen

    def disco_info(self, device):
        """Build a Discovery Information message.

        :param device: The HiQnet device sending the discovery message
        :type device: Device
        """
        self.message_id = MSG_DISCOINFO
        # Payload
        device_address = struct.pack('!H', self.source_address.device_address)
        cost = b'\x01'
        serial_number_len = struct.pack('!H', 16)
        try:
            serial_number = bytes(device.manager.serial_number.decode('ascii'))
        except AttributeError:
            # We are running Python 3
            # noinspection PyArgumentList
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
        """Build a Request Address message.

        :param req_addr:
        :type req_addr: int
        """
        self.message_id = MSG_REQADDR
        self.payload = struct.pack('!H', req_addr)

    def address_used(self):
        """Build an Address Used message."""
        self.message_id = MSG_ADDRUSED

    def hello(self):
        """Build an hello message.

        Starts a session.

        :return: The session number
        :rtype: int
        """
        self.message_id = MSG_HELLO
        session_number = os.urandom(2)
        flag_mask = SUPPORTED_FLAG_MASK
        self.payload = session_number + flag_mask
        return session_number

    def get_attributes(self):
        """Build a Get Attributes message."""
        self.message_id = MSG_GETATTR

    def get_vd_list(self):
        """"Build a Get VD List message."""
        self.message_id = MSG_GETVDLIST

    def store(self):
        """Build a Store message.

        Stores current state to a preset.
        """
        self.message_id = MSG_STORE

    def recall(self):
        """Build a Recall message.

        Recalls a preset.
        """
        self.message_id = MSG_RECALL

    def locate(self, time, serial_number):
        """Builds a Locate message.

        The receiver makes itself visible. Usually this is done by flashing some LEDs on the front panel.

        :param time: time the leds should flash in ms
                     0x0000 turns off locate led(s)
                     0xffff turns on locate led(s)
        :type time: bytearray
        :param serial_number: The target device's serial number
        :type serial_number: str

        .. seealso:: locate_on(), locate_off()
        """
        self.message_id = MSG_LOCATE
        serial_number_len = struct.pack('!H', len(serial_number))
        self.payload = time + serial_number_len + serial_number

    def locate_on(self, serial_number):
        """Builds a locate message asking for the visual clue to be active

        :param serial_number: The target device's serial number
        :type serial_number: str
        """
        self.locate(b'\xff\xff', serial_number)

    def locate_off(self, serial_number):
        """Builds a locate message asking for the visual clue to be inactive

        :param serial_number: The target device's serial number
        :type serial_number: str
        """
        self.locate(b'\x00\x00', serial_number)

    def _build_optional_headers(self):
        """Builds the optional message headers."""
        # Optional error header
        if self.flags.error:
            error_code = b'\x02'
            error_string = b''
            self.optional_headers += error_code + error_string
        # Optional multi-part header
        if self.flags.multipart:
            start_seq_no = b'\x02'
            bytes_remaining = b'\x00\x00\x00\x00'  # 4 bytes
            self.optional_headers += start_seq_no + bytes_remaining
        # Optional session number header
        if self.flags.session:
            session_number = b'\x00\x00'  # 2 bytes
            self.optional_headers += session_number

    def _compute_headerlen(self):
        """Computes the header length."""
        headerlen = MIN_HEADER_LEN + len(self.optional_headers)
        self.headerlen = struct.pack('!B', headerlen)

    def _compute_messagelen(self):
        """Computes the message length."""
        messagelen = len(self.payload) + struct.unpack('!B', self.headerlen)[0]
        self.messagelen = struct.pack('!I', messagelen)

    def _build_header(self):
        """Builds the message header."""
        self._build_optional_headers()
        self._compute_headerlen()
        self._compute_messagelen()
        self.header = self.version + self.headerlen + self.messagelen \
            + bytes(self.source_address) + bytes(self.destination_address) \
            + self.message_id + self.flags + self.hop_counter + self.sequence_number + self.optional_headers

    def __bytes__(self):
        """Get the message as bytes."""
        self._build_header()
        return self.header + self.payload

    def __str__(self):
        """Get the message in a printable form."""
        return self.__bytes__()

# TODO: Event logs
# TODO: Session

# TODO: Device arrival announce


class Device:
    """Describes a device (aka node)."""
    _hiqnet_address = None
    """:type : int Allowed values: 1 to 65534. 65535 is reserved as the broadcast address"""
    network_info = NetworkInfo.autodetect()
    manager = None
    virtual_devices = None

    def __init__(self, name, hiqnet_address):
        self.manager = DeviceManager(name)
        self.set_hiqnet_address(hiqnet_address)

    def set_hiqnet_address(self, address):
        if 1 > address > 65534:
            raise ValueError
        self._hiqnet_address = address

    @staticmethod
    def negotiate_address():
        """Generates a random HiQnet address to datastore and reuse on the device.

        The address is automatically checked on the network.
        """
        requested_address = random.randrange(1, 65535)
        # connection = Connection()
        # message = Message(source=FullyQualifiedAddress(device_address=0),
        #                        destination=FullyQualifiedAddress.broadcast_address())
        # message.request_address(self, requested_address)
        # connection.sendto('<broadcast>')
        # FIXME: look for address_used reply messages and renegotiate if found
        return requested_address


class Connection:
    """Handles HiQnet IP connection.

    .. warning:: Other connection types such as RS232, RS485 or USB are not handled yet.
    """
    udp_transport = None
    tcp_transport = None

    def __init__(self, udp_transport, tcp_transport):
        """Initiate a HiQnet IP connection over UDP and TCP.

        :param udp_transport:
        :type udp_transport: twisted.internet.interfaces.IUDPTransport
        :param tcp_transport:
        :type tcp_transport: twisted.internet.interfaces.ITCPTransport
        :return:
        """
        self.udp_transport = udp_transport
        self.tcp_transport = tcp_transport

    def sendto(self, message, destination):
        """Send message to the destination.

        :param message: Message to send.
        :type message: Message
        :param destination: Destination IPv4 address
        :type destination: str
        """
        if message.flags.guaranteed:
            # Send TCP message if the Guaranteed flag is set
            self.tcp_transport.write(bytes(message), (destination, IP_PORT))
        else:
            self.udp_transport.write(bytes(message), (destination, IP_PORT))


# noinspection PyClassHasNoInit
class TCPProtocol(protocol.Protocol):
    """HiQnet Twisted TCP protocol."""
    def startProtocol(self):
        """Called after protocol started listening."""
        self.factory.app.tcp_transport = self.transport

    def dataReceived(self, data):
        """Called when data is received.

        :param data: Received binary data
        :type data: bytearray
        """
        # FIXME: debugging output should go into a logger
        print("Received HiQnet TCP data: ")
        print(binascii.hexlify(data))

        # TODO: Process some more :)
        self.factory.app.handle_message(data, None, "HiQnet TCP")


class UDPProtocol(protocol.DatagramProtocol):
    """HiQnet Twisted UDP protocol."""
    def __init__(self, app):
        self.app = app

    def startProtocol(self):
        """Called after protocol started listening."""
        self.transport.setBroadcastAllowed(True)  # Some messages needs to be broadcasted
        self.app.udp_transport = self.transport

    def datagramReceived(self, data, addr):
        """Called when data is received.

        :param data: Receive binary data
        :type data: bytearray
        :param addr: IPv4 address and port of the sender
        :type addr: tuple
        """
        (host, port) = addr

        # FIXME: debugging output should go into a logger
        print("Received HiQnet UDP data: ")
        print(binascii.hexlify(data))
        print("from ", end="")
        print(host, end="")
        print(":", end="")
        print(port)
        message = Message(data)
        print(vars(message))  ## DEBUG

        # TODO: Process some more :)
        self.app.handle_message(data, host, "HiQnet UDP")


class Factory(protocol.Factory):
    """HiQnet Twisted Factory."""

    protocol = TCPProtocol

    def __init__(self, app):
        self.app = app
