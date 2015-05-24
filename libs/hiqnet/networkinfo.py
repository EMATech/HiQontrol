# -*- coding: utf-8 -*-
"""HiQnet device network informations."""

from __future__ import print_function

__author__ = 'Raphaël Doursenaud'

import netifaces


class NetworkInfo(object):
    """Network informations."""
    NET_ID_TCP_IP = 1
    NET_ID_RS232 = 4

    network_id = None
    """
    - 1: TCP/IP
    - 2: reserved
    - 3: reserved
    - 4: RS232
    """

    def __init__(self, network_id=NET_ID_TCP_IP):
        self.network_id = network_id


class RS232NetworkInfo(NetworkInfo):
    """RS232 network informations.

    TODO: RS232 Network info
    com_id    1 byte
    baud_rate 4 bytes
    parity    1 byte
      0 - None
      1 - Odd
      2 - Even
      3 - Mark
      4 - Space
    stop_bits 1 byte
      0 - 1 bit
      1 - 1.5 bits
      2 - 2 bits
    data_bits 1 byte
      4-9
    flow_control  1_byte
      0 - None
      1 - Hardware
      2 - XON/OFF
    """

    def __init__(self):
        super(RS232NetworkInfo, self).__init__(network_id=self.NET_ID_RS232)
        raise NotImplementedError


class IPNetworkInfo(NetworkInfo):
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
        """
        super(IPNetworkInfo, self).__init__(network_id=self.NET_ID_TCP_IP)
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
        # noinspection PyCallingNonCallable
        return cls(mac_address, dhcp, ip_address, subnet_mask, gateway_address)
