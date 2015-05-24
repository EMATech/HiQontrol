# -*- coding: utf-8 -*-
"""HiQnet device architecture.

Node (Device)
  \- At least one virtual device (The first is the device manager)
  \- Parameters and/or objects
                        \- Objects contains parameters and/or other objects

Attributes everywhere
    Either STATIC, Instance or Instance+Dynamic

Virtual devices, objects and parameters
    Have a Class Name and a Class ID
"""

from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

from flags import *
from networkinfo import *
from protocol import FullyQualifiedAddress
import random


class Attribute(object):
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
        """
        if atr_type in self._allowed_types:
            self.type = atr_type
            return
        raise ValueError


class Object(object):
    """HiQnet objects.

    May contain other objects or parameters.
    """
    _address = None  # 24 bits


class Parameter(Object):
    """HiQnet parameters.

    Represents the manipulable elements and their attributes.
    """
    _index = None  # 16 bits
    data_type = None  # STATIC FIXME: needs doc
    name_string = ''  # Instance+Dynamic
    minimum_value = None  # Depends on data_type
    maximum_value = None  # Depends on data_type
    control_law = None
    flags = ParameterFlags()


class VirtualDevice(object):
    """Describes a HiQnet virtual device.

    This is the basic container object type.
    """
    _address = None  # 8 bits
    class_name = Attribute('Static')
    name_string = Attribute('Instance+Dynamic')
    objects = None
    parameters = None
    attributes = None


class DeviceManager(VirtualDevice):
    """Describes a HiQnet device manager.

    Each device has one and this is always the first virtual device.
    """
    _address = 0
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


class Device(object):
    """Describes a device (aka node)."""
    _hiqnet_address = None
    """:type : int Allowed values: 1 to 65534. 65535 is reserved as the broadcast address"""
    network_info = None
    manager = None
    virtual_devices = None

    def __init__(self, name, hiqnet_address, network_info=IPNetworkInfo.autodetect()):
        """Build a device.

        :param name: Name of the device
        :type name: str
        :param hiqnet_address: Address of the device
        :type hiqnet_address: int
        :param network_info: Device's network informations
        :type network_info: NetworkInfo
        """
        self.manager = DeviceManager(name)
        self.set_hiqnet_address(hiqnet_address)
        self.network_info = network_info

    def set_hiqnet_address(self, address):
        """Set the device HiQnet address.

        :param address:
        :type address: int
        """
        if 1 > address > 65534:
            raise ValueError
        self._hiqnet_address = address

    @staticmethod
    def negotiate_address():
        """Generates a random HiQnet address to datastore and reuse on the device.

        The address is automatically checked on the network.
        """
        requested_address = random.randrange(1, 65534)
        # connection = Connection()
        # message = Command(source=FullyQualifiedAddress(device_address=0),
        #                          destination=FullyQualifiedAddress.broadcast_address())
        # message.request_address(self, requested_address)
        # connection.sendto('<broadcast>')
        # FIXME: look for address_used reply messages and renegotiate if found
        return requested_address

    def get_address(self):
        """Get the device manager address

        :return: The address of the device manager
        :rtype: FullyQualifiedAddress
        """
        return FullyQualifiedAddress(device_address=self._hiqnet_address)
