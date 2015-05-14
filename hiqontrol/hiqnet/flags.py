# -*- coding: utf-8 -*-

__author__ = 'Raphaël Doursenaud'

import ctypes
import struct

c_uint16 = ctypes.c_uint16

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

    def __str__(self):
        """String representation.

        Useful for debugging purposes
        """
        string = ''
        for name, type, len in self._fields_:
            string += name + ":" + str(getattr(self, name)) + " "
        return string


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


class ParameterFlagsBits(ctypes.LittleEndianStructure):
    """Bitfields for the parameters flags.

    Bits 0, 2, and 3 are reserved. Bit 1 is the Sensor Attribute.
        0 = Non-Sensor
        1 = Sensor
    """
    _fields_ = [
        ('res1', c_uint16, 1),
        ('sensor', c_uint16, 1),
        ('res2', c_uint16, 1),
        ('res3', c_uint16, 1),
    ]

    def __str__(self):
        """String representation.

        Useful for debugging purposes
        """
        string = ''
        for name, type, len in self._fields_:
            string += name + ":" + str(getattr(self, name)) + " "
        return string


class ParameterFlags(ctypes.Union):
    """Parameter flags."""
    _fields_ = [
        ('b', ParameterFlagsBits),
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
