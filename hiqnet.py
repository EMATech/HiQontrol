__author__ = 'Raphaël Doursenaud'

SI_COMPACT_16_MAC = '00-17-24-82-06-53'
SI_COMPACT_16_DEVICE_ID = '1619'  # 0x653
HIQNET_IP_PORT = 3804

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


class VirtualDevice:
    class_name = ''  # STATIC
    name_string = ''  # Instance+Dynamic


class DeviceManager(VirtualDevice):
    flags = 0
    serial_number = 0
    software_version = ''


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


class HiQnetAddress:
    device_address = None  # 16 bits
    vd_address = None  # 8 bits
    object_address = None  # 24 bits
    parameter_index = None  # 16 bits


class HiQnetMessage:
    version = 0x02  # Default, 2 bytes
    """
    The Version Number indicates the revision number of the entire protocol; it is not
    used for differentiating between revisions of individual messages. HiQnet is
    currently at revision 2. Devices that communicate with HiQnet version 1.0
    include the dbx ZonePro family. All others use version 2.0.
    """
    header = None  # 2 bytes
    """
    The Header Length is the size in bytes of the entire message header, including any
    additional headers such as 'Error' or 'Multi-part'.
    """
    message_length = None  # 8 bytes
    """
    The Message Length is the size in bytes of the entire message - from the
    ‘Version’ field through to the last byte of the payload.
    """
    source_address = HiQnetAddress  # 6 byte (48 bits)
    """
    The Source Address specifies the HiQnet address where the message has come
    from; this is often used by the recipient for sending back reply messages.
    """
    destination_address = HiQnetAddress  # 6 byte (48 bits)
    """The Destination Address specifies where the message is to be delivered to."""
    message_id = None  # 4 bytes
    """
    The Message ID is a unique identifier that indicates the method that the
    destination Device must perform. If there is a payload, it is usually specific to the
    type of method indicated by the Message ID. Product-specific IDs may also exist
    and will be documented appropriately.
    """
    flags = 0x0000  # 4 bytes
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
    hop_counter = 0x01  # 2 bytes
    """
    The Hop Count denotes the number of network hops that a message has traversed
    and is used to stop broadcast loops. This field should generally be defaulted to
    0x05.
    """
    sequence_number = 0x0001  # 4 bytes
    """
    The Sequence number is used to uniquely identify each HiQnet message leaving a
    Device. This is primarily used for diagnostic purposes. The sequence number
    starts at 0 on power-up and increments for each successive message the Routing
    Layer sends to the Packet Layer. The Sequence Number rolls over at the top of its
    range.
    """
    # Optional error header
    # flags = 0x0008
    error_code = 0x02
    error_string = ''
    # Optional multi-part header
    # flags = 0x0040
    start_seq_no = 0x02
    bytes_remaining = None  # 8 bytes
    # Optional session number header
    # flags = 0x0100
    session_number = None  # 4 bytes

    payload = None

    def setDestinationAddress(self, address):
        self.destination_address = address

    def setSourceAddress(self, address):
        self.source_address = address

    def getAttributes(self):
        self.message_id = 0x010d

    def getVDList(self):
        self.message_id = 0x011a

    def store(self):
        self.message_id = 0x0124

    def recall(self):
        self.message_id = 0x0125

    def locate(self, time):
        """
        :param time: time the leds should flash in ms
                     0x0000 turns off locate led(s)
                     0xffff turns on locate led(s)
        :return: void
        """
        self.message_id = 0x0129
        self.payload = time

# TODO: Event logs
# TODO: Session

