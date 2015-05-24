# -*- coding: utf-8 -*-
"""HiQnet protocol library."""

from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

import itertools
import os
import socket
import binascii

from flags import *
from networkinfo import *

PROTOCOL_VERSION = 2
PROTOCOL_MIN_VERSION = 1
PROTOCOL_MAX_VERSION = 3

MIN_HEADER_LEN = 25  # bytes

DEFAULT_HOP_COUNTER = 5

DEFAULT_FLAG_MASK = b'\x01\xff'

SUPPORTED_FLAG_MASK = DEFAULT_FLAG_MASK

DEFAULT_KEEPALIVE = 10000  # ms


class Message(object):
    """HiQnet messages handling."""

    MESSAGES = {
        'DISCOINFO': b'\x00\x00',
        'RESERVED0': b'\x00\x01',
        'GETNETINFO': b'\x00\x02',
        'RESERVED1': b'\x00\x03',
        'REQADDR': b'\x00\x04',
        'ADDRUSED': b'\x00\x05',
        'SETADDR': b'\x00\x06',
        'GOODBYE': b'\x00\x07',
        'HELLO': b'\x00\x08',
        'MULTPARMSET': b'\x01\x00',
        'MULTOBJPARMSET': b'\x01\x01',
        'PARMSETPCT': b'\x01\x02',
        'MULTPARMGET': b'\x01\x03',
        'GETATTR': b'\x01\x0d',
        'SETATTR': b'\x01\x0e',
        'MULTPARMSUB': b'\x01\x0f',
        'PARMSUBPCT': b'\x01\x11',
        'MULTPARMUNSUB': b'\x01\x12',
        'PARMSUBALL': b'\x01\x13',
        'PARMUNSUBALL': b'\x01\x14',
        'SUBEVTLOGMSGS': b'\x01\x15',
        'GETVDLIST': b'\x01\x1a',
        'STORE': b'\x01\x24',
        'RECALL': b'\x01\x25',
        'LOCATE': b'\x01\x29',
        'UNSUBEVTLOGMSGS': b'\x01\x2b',
        'REQEVTLOG': b'\x01\x2c',
        b'\x00\x00': 'DISCOINFO',
        b'\x00\x01': 'RESERVED0',
        b'\x00\x02': 'GETNETINFO',
        b'\x00\x03': 'RESERVED1',
        b'\x00\x04': 'REQADDR',
        b'\x00\x05': 'ADDRUSED',
        b'\x00\x06': 'SETADDR',
        b'\x00\x07': 'GOODBYE',
        b'\x00\x08': 'HELLO',
        b'\x01\x00': 'MULTPARMSET',
        b'\x01\x01': 'MULTOBJPARMSET',
        b'\x01\x02': 'PARMSETPCT',
        b'\x01\x03': 'MULTPARMGET',
        b'\x01\x0d': 'GETATTR',
        b'\x01\x0e': 'SETATTR',
        b'\x01\x0f': 'MULTPARMSUB',
        b'\x01\x11': 'PARMSUBPCT',
        b'\x01\x12': 'MULTPARMUNSUB',
        b'\x01\x13': 'PARMSUBALL',
        b'\x01\x14': 'PARMUNSUBALL',
        b'\x01\x15': 'SUBEVTLOGMSGS',
        b'\x01\x1a': 'GETVDLIST',
        b'\x01\x24': 'STORE',
        b'\x01\x25': 'RECALL',
        b'\x01\x29': 'LOCATE',
        b'\x01\x2b': 'UNSUBEVTLOGMSGS',
        b'\x01\x2c': 'REQEVTLOG',
    }

    identifier = None
    name = None

    def __init__(self, identifier=None, name=None):
        """Build a message.

        :param identifier: The message ID
        :type identifier: bytearray
        :param name: The message name
        :type name: str
        """
        if identifier and name:
            raise ValueError("You must no supply both a identifier and name.")

        if identifier:
            if identifier in self.MESSAGES:
                self.identifier = identifier
                self.name = self.MESSAGES[identifier]
            else:
                raise ValueError("Unknown message ID.")

        if name:
            if name in self.MESSAGES:
                self.name = name
                self.identifier = self.MESSAGES[name]
            else:
                raise ValueError("Unknown message name.")

    def __str__(self):
        return self.identifier

    def __repr__(self):
        return self.name


class FullyQualifiedAddress(object):
    """Fully Qualified HiQnet Address."""
    device_address = None
    vd_address = None
    object_address = None

    def __init__(self,
                 device_address=None,
                 vd_address=b'\x00',
                 object_address=b'\x00\x00\x00',
                 devicevdobject=None,
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
            self.device_address = struct.unpack('!H', devicevdobject[0:2])[0]
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

        :type cls: FullyQualifiedAddress
        :rtype: FullyQualifiedAddress
        """
        # noinspection PyCallingNonCallable
        return cls(device_address=65535, vd_address=b'\x00', object_address=b'\x00\x00\x00')

    def __bytes__(self):
        """Get the address as bytes."""
        # TODO: make vd_address and object_address int rather than byte arrays
        return struct.pack('!H', self.device_address) + self.vd_address + self.object_address

    def __str__(self):
        """Get the address in a printable format."""
        return self.__bytes__()

    def __repr__(self):
        return str(self.device_address) + '.' + \
            "%d" % struct.unpack('!B', self.vd_address) + \
            '.' + "%d.%d.%d" % struct.unpack('!BBB', self.object_address)


class Command(object):
    """HiQnet command."""
    # Placeholder, will be filled later
    header = b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'

    version = PROTOCOL_VERSION  # 1 byte
    """
    The Version Number indicates the revision number of the entire protocol; it is not
    used for differentiating between revisions of individual commands. HiQnet is
    currently at revision 2. Devices that communicate with HiQnet version 1.0
    include the dbx ZonePro family. All others use version 2.0.
    It also seems that a version 3.0 is in the works for IEEE AVB integration.

    :type: int
    """
    headerlen = MIN_HEADER_LEN  # 1 byte
    """
    The Header Length is the size in bytes of the entire command header, including any
    additional headers such as 'Error' or 'Multi-part'.

    :type: int
    """
    commandlen = 0  # 4 bytes
    """
    The command length is the size in bytes of the entire command - from the
    ‘Version’ field through to the last byte of the payload.

    :type: int
    """
    source_address = FullyQualifiedAddress()  # 6 byte (48 bits)
    """
    The Source Address specifies the HiQnet address where the command has come
    from; this is often used by the recipient for sending back reply commands.
    """
    destination_address = FullyQualifiedAddress()  # 6 byte (48 bits)
    """The Destination Address specifies where the command is to be delivered to."""
    message = Message(identifier=b'\x00\x00')  # 2 bytes
    """
    The Message ID is a unique identifier that indicates the method that the
    destination Device must perform. If there is a payload, it is usually specific to the
    type of method indicated by the Message ID. Product-specific IDs may also exist
    and will be documented appropriately.
    """
    flags = DeviceFlags()  # 2 bytes
    """
    The Flags denote what kinds of options are active when set to ‘1’.

    They are allocated in the following manner:

    +----------+-------------------+
    | Bit 15-9 | Bit 8             |
    +==========+===================+
    | Reserved | Session number    |
    |          |(Header extension) |
    +----------+-------------------+

    +----------+--------------------+------------+----------+
    | Bit 7    | Bit 6              | Bit 5      | Bit 4    |
    +==========+====================+============+==========+
    | Reserved | Multi-part message | Guaranteed | Reserved |
    |          |(Header extension)  |            |          |
    +----------+--------------------+------------+----------+

    +--------------------+-------------+-----------------+-------------------------+
    | Bit 3              | Bit 2       | Bit 1           | Bit 0                   |
    +====================+=============+=================+=========================+
    | Error              | Information | Acknowledgement | Request Acknowledgement |
    | (Header extension) |             |                 |                         |
    +--------------------+-------------+-----------------+-------------------------+

    Bit 5 must be set for any applications using TCP/IP only on the network
    interface. This will ensure that any commands are sent guaranteed (TCP rather
    than UDP).
    """
    hop_counter = DEFAULT_HOP_COUNTER  # 1 byte
    """
    The Hop Count denotes the number of network hops that a command has traversed
    and is used to stop broadcast loops. This field should generally be defaulted to
    0x05.

    :type: int
    """
    new_sequence_number = itertools.count()
    sequence_number = 0  # 2 bytes
    """
    The Sequence number is used to uniquely identify each HiQnet command leaving a
    Device. This is primarily used for diagnostic purposes. The sequence number
    starts at 0 on power-up and increments for each successive command the Routing
    Layer sends to the Packet Layer. The Sequence Number rolls over at the top of its
    range.

    :type: int
    """

    optional_headers = b''  # Placeholder, may not be filled

    # TODO: optional headers object?
    error_code = 0
    error_string = ''
    start_seq_no = 0
    bytes_remaining = 0
    session_number = 0

    payload = b''  # Placeholder, filled later, depends on the message

    def __init__(self, source=None, destination=None, command=None):
        """Initiate an HiQnet command from source to destination.

        :param source: Source of the command
        :type source: FullyQualifiedAddress
        :param destination: destination of the command
        :type destination: FullyQualifiedAddress
        :return:
        """
        if command:
            self.decode(command=command)
        else:
            self.source_address = source
            self.destination_address = destination  # TODO: use broadcast if not provided
            self.sequence_number = next(self.new_sequence_number)

    def decode(self, command):
        """Decodes a binary command.

        :param command: The binary command to decode
        """
        print("Real command length: ", len(command))
        if len(command) < MIN_HEADER_LEN:
            raise BufferError("Command too short")
        self.set_version(struct.unpack('!B', command[0])[0])
        self.set_headerlen(struct.unpack('!B', command[1])[0])
        if len(command) < self.headerlen:
            raise BufferError("Command is smaller than it's header length")
        self.set_commandlen(struct.unpack('!L', command[2:6])[0])
        if len(command) != self.commandlen:
            raise BufferError("Command length header and actual length missmatch")
        self.source_address = FullyQualifiedAddress(devicevdobject=command[6:12])
        self.destination_address = FullyQualifiedAddress(devicevdobject=command[12:18])
        self.message = Message(identifier=command[18:20])
        self.flags.asByte = struct.unpack('!H', command[20:22])[0]
        print("Flags: ", repr(self.flags))
        self.hop_counter = struct.unpack('!B', command[22])[0]
        self.sequence_number = struct.unpack('!H', command[23:25])[0]
        if self.headerlen > MIN_HEADER_LEN:
            index = MIN_HEADER_LEN
            # Optional Headers are present, check the flags
            if self.flags.error:
                self.error_code = struct.unpack('!B', command[index])[0]
                index += 1
                self.error_string = struct.unpack('s', command[index])[0]  # FIXME: detect string end
                index += len(self.error_string)
                raise NotImplementedError
            if self.flags.multipart:
                self.start_seq_no = struct.unpack('!B', command[index])[0]
                index += 1
                self.bytes_remaining = struct.unpack('!L', command[index])[0]
                index += 4
                raise NotImplementedError
            if self.flags.session:
                self.session_number = struct.unpack('!H', command[index:index + 2])[0]
                index += 2
                print(self.session_number)  # DEBUG
        self.payload = command[self.headerlen:self.commandlen]

        # TODO: decode payload by message type
        if self.message.name == 'DISCOINFO':
            self.decode_discoinfo()

    def decode_discoinfo(self):
        """Decode discovery information command payload.

        Payload:
        - HiQnet Device
        - Cost
        - Serial Number
        - Max Message size
        - Keep alive period
        - NetwordID
        - NetworkInfo
        """
        # Message type
        if self.flags.b.info:
            print("DiscoInfo(I)")
        else:
            print("DiscoInfo(Q)")

        index = 0

        size = 2
        print("Device address: ", end='')
        print(struct.unpack('!H', self.payload[index:index + size])[0])
        index += size

        print("Cost: ", end='')
        print(struct.unpack('!B', self.payload[index])[0])
        index += 1

        # TODO: extract this algo as the "BLOCK" type
        size = 2
        data_len = struct.unpack('!H', self.payload[index:index + size])[0]
        index += size
        size = data_len
        print("Serial number: ", end='')
        serial_number = ''
        while size:
            serial_number += struct.unpack('!s', self.payload[index])[0]
            index += 1
            size -= 1
        print(serial_number)

        size = 4
        print("Max message size: ", end='')
        print(struct.unpack('!L', self.payload[index:index + size])[0])
        index += size

        size = 2
        print("Keep alive period: ", end='')
        print(struct.unpack('!H', self.payload[index:index + size])[0])
        index += size

        print("NetworkID: ", end='')
        network_id = struct.unpack('!B', self.payload[index])[0]
        print(network_id)
        index += 1

        print("NetworkInfo: ", end='')
        if network_id == NetworkInfo.NET_ID_TCP_IP:
            # TCP/IP
            size = 6
            mac_address = "%02x:%02x:%02x:%02x:%02x:%02x" % struct.unpack("!BBBBBB", self.payload[index:index + size])
            index += size

            dhcp = bool(struct.unpack("B", self.payload[index])[0])
            index += 1

            size = 4
            ip_address = "%d.%d.%d.%d" % struct.unpack('!BBBB', self.payload[index:index + size])
            index += size

            size = 4
            subnet_mask = "%d.%d.%d.%d" % struct.unpack('!BBBB', self.payload[index:index + size])
            index += size

            size = 4
            gateway_address = "%d.%d.%d.%d" % struct.unpack('!BBBB', self.payload[index:index + size])
            index += size

            network_info = IPNetworkInfo(mac_address=mac_address, dhcp=dhcp,
                                         ip_address=ip_address, subnet_mask=subnet_mask,
                                         gateway_address=gateway_address)

            print(vars(network_info))  # DEBUG

        elif network_id == NetworkInfo.NET_ID_RS232:
            network_info = RS232NetworkInfo
            raise NotImplementedError

        else:
            raise NotImplementedError

    def set_version(self, version):
        """Set the version.

        :param version: Version number.
        :type version: int
        """
        if not PROTOCOL_MIN_VERSION <= version <= PROTOCOL_MAX_VERSION:
            raise ValueError("This HiQnet version is unknown.")
        self.version = version

    def set_headerlen(self, headerlen):
        """Set the header length.

        :param headerlen: Header length
        :type headerlen: int
        """
        if headerlen < MIN_HEADER_LEN:
            raise ValueError("The header can't be smaller than " + str(MIN_HEADER_LEN))
        self.headerlen = headerlen

    def set_commandlen(self, commandlen):
        """ Set the command length

        :param commandlen: Command lenght
        :type commandlen: int
        """
        if commandlen < self.headerlen or commandlen < MIN_HEADER_LEN:
            raise ValueError("Command can't be smaller than the header")
        self.commandlen = commandlen

    def disco_info(self, device, disco_type='Q'):
        """Build a Discovery Information command.

        :param device: The HiQnet device sending the discovery command
        :type device: Device
        """
        if disco_type == 'I':
            self.flags.info = 1
        else:
            self.flags.info = 0
        self.message = Message(name='DISCOINFO')
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
        network_id = struct.pack('!B', device.network_info.network_id)
        mac_address = binascii.unhexlify(device.network_info.mac_address.replace(':', ''))
        dhcp = struct.pack('!B', device.network_info.dhcp)
        ip_address = socket.inet_aton(device.network_info.ip_address)
        subnet_mask = socket.inet_aton(device.network_info.subnet_mask)
        gateway_address = socket.inet_aton(device.network_info.gateway_address)
        self.payload = device_address + cost + serial_number_len + serial_number \
            + max_message_size + keep_alive_period + network_id \
            + mac_address + dhcp + ip_address + subnet_mask + gateway_address

    def request_address(self, req_addr):
        """Build a Request Address command.

        :param req_addr:
        :type req_addr: int
        """
        self.message = Message(name='REQADDR')
        self.payload = struct.pack('!H', req_addr)

    def address_used(self):
        """Build an Address Used command."""
        self.message = Message(name='ADDRUSED')

    def hello(self):
        """Build an hello command.

        Starts a session.

        :return: The session number
        :rtype: int
        """
        self.message = Message(name='HELLO')
        session_number = os.urandom(2)
        flag_mask = SUPPORTED_FLAG_MASK
        self.payload = session_number + flag_mask
        return session_number

    def get_attributes(self):
        """Build a Get Attributes command."""
        self.message = Message(name='GETATTR')
        raise NotImplementedError

    def get_vd_list(self, workgroup=''):
        """Build a Get VD List command."""
        self.message = Message(name='GETVDLIST')
        self.payload = workgroup
        # raise NotImplementedError

    def store(self):
        """Build a Store command.

        Stores current state to a preset.
        """
        self.message = Message(name='STORE')
        raise NotImplementedError

    def recall(self):
        """Build a Recall command.

        Recalls a preset.
        """
        self.message = Message(name='RECALL')
        raise NotImplementedError

    def locate(self, time, serial_number):
        """Builds a Locate command.

        The receiver makes itself visible. Usually this is done by flashing some LEDs on the front panel.

        :param time: time the leds should flash in ms
                     0x0000 turns off locate led(s)
                     0xffff turns on locate led(s)
        :type time: bytearray
        :param serial_number: The target device's serial number
        :type serial_number: str

        .. seealso:: :py:func:`locate_on`, :py:func:`locate_off`
        """
        self.message = Message(name='LOCATE')
        serial_number_len = struct.pack('!H', len(serial_number))
        self.payload = time + serial_number_len + serial_number

    def locate_on(self, serial_number):
        """Builds a locate command asking for the visual clue to be active.

        :param serial_number: The target device's serial number
        :type serial_number: str
        """
        self.locate(b'\xff\xff', serial_number)

    def locate_off(self, serial_number):
        """Builds a locate command asking for the visual clue to be inactive.

        :param serial_number: The target device's serial number
        :type serial_number: str
        """
        self.locate(b'\x00\x00', serial_number)

    def _build_optional_headers(self):
        """Builds the optional command headers."""
        # Optional error header
        if self.flags.error:
            error_code = b'\x02'
            error_string = b''
            self.optional_headers += error_code + error_string
            raise NotImplementedError
        # Optional multi-part header
        if self.flags.multipart:
            start_seq_no = b'\x02'
            bytes_remaining = b'\x00\x00\x00\x00'  # 4 bytes
            self.optional_headers += start_seq_no + bytes_remaining
            raise NotImplementedError
        # Optional session number header
        if self.flags.session:
            session_number = b'\x00\x00'  # 2 bytes
            self.optional_headers += session_number
            raise NotImplementedError

    def _compute_headerlen(self):
        """Computes the header length."""
        self.headerlen = MIN_HEADER_LEN + len(self.optional_headers)

    def _compute_commandlen(self):
        """Computes the command length."""
        self.commandlen = len(self.payload) + self.headerlen

    def _build_header(self):
        """Builds the command header."""
        self._build_optional_headers()
        self._compute_headerlen()
        self._compute_commandlen()
        self.header = struct.pack('!B', self.version) \
            + struct.pack('!B', self.headerlen) \
            + struct.pack('!L', self.commandlen) \
            + bytes(self.source_address) + bytes(self.destination_address) \
            + bytes(self.message) \
            + bytes(self.flags) \
            + struct.pack('!B', self.hop_counter) \
            + struct.pack('!H', self.sequence_number) \
            + bytes(self.optional_headers)

    def __bytes__(self):
        """Get the command as bytes."""
        self._build_header()
        return self.header + self.payload

    def __str__(self):
        """Get the command in a printable form."""
        return self.__bytes__()

    def __repr__(self):
        return vars(self)

# TODO: Event logs
# TODO: Session

# TODO: Device arrival announce
