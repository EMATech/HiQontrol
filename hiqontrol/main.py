# -*- coding: utf-8 -*-

__author__ = 'Raphaël Doursenaud'

import re
import binascii

from kivy.app import App

from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.adapters.dictadapter import DictAdapter
from kivy.properties import ObjectProperty
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.textinput import TextInput
from kivy.uix.listview import CompositeListItem, ListItemButton
from kivy.support import install_twisted_reactor

from hiqnet import hiqnet
from soundcraft import soundcraft

install_twisted_reactor()
from twisted.internet import reactor

# FIXME: this should not be hardcoded but autodetected
SI_COMPACT_16_IP = '192.168.1.53'
SI_COMPACT_16_DEVICE_ADDRESS = 27904  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

APPNAME = 'HiQontrol'


class ListLocateButton(ListItemButton):
    blinking = False

    def __init__(self, **kwargs):
        self.hiqnet_address = kwargs['hiqnet_address']
        self.ip_address = kwargs['ip_address']
        self.serial_number = kwargs['serial_number']
        super(ListLocateButton, self).__init__(**kwargs)

    def toggle_blinking(self):
        if self.blinking:
            self.blink_stop()
        else:
            self.blink_start()

    def blink_start(self):
        self.background_color = [1, 0, 0, 1]
        Clock.schedule_interval(self.change_color, .5)
        self.blinking = True

    def blink_stop(self):
        Clock.unschedule(self.change_color)
        self.blinking = False

    # noinspection PyUnusedLocal
    def change_color(self, *args):
        self.background_color = [
            int(not bool(self.background_color[0])),
            self.background_color[1],
            self.background_color[2],
            self.background_color[3],
        ]


class ListInfoButton(ListItemButton):
    pass


class ListMixButton(ListItemButton):
    pass


class HiQNetAddressInput(TextInput):
    # FIXME: don't allow value of 0 or over 65535
    pat = re.compile('[^0-9]]')

    def insert_text(self, substring, from_undo=False):
        pat = self.pat
        s = re.sub(pat, '', substring)
        return super(HiQNetAddressInput, self).insert_text(s, from_undo=from_undo)


class Control:
    locate = False
    source_device = None
    udp_transport = None
    tcp_transport = None

    def __init__(self, source_device, udp_transport, tcp_transport):
        self.source_device = source_device
        self.udp_transport = udp_transport
        self.tcp_transport = tcp_transport

    def init(self, hiqnet_dest):
        c = hiqnet.Connection(self.udp_transport, self.tcp_transport)
        source_address = hiqnet.FullyQualifiedAddress(device_address=self.source_device._hiqnet_address)
        destination_address = hiqnet.FullyQualifiedAddress(device_address=hiqnet_dest)
        message = hiqnet.Message(source=source_address, destination=destination_address)
        return c, message

    def locate_toggle(self, hiqnet_dest, ip_dest, serial_dest):
        c, message = self.init(hiqnet_dest)
        if not self.locate:
            message.locate_on(serial_dest)
            self.locate = True
        else:
            message.locate_off(serial_dest)
            self.locate = False
        c.sendto(message, ip_dest)


class HiQontrol(ScreenManager):
    list = ObjectProperty()


class HiQontrolApp(App):
    __version__ = '0.0.3'
    datastore = JsonStore('settings.json')
    store_needs_update = False
    device = None
    try:
        device = hiqnet.Device(datastore.get('device_name')['value'], datastore.get('device_address')['value'])
    except KeyError:
        Logger.warning(APPNAME + ': Settings not found, will use sane defaults')
        device_name = APPNAME
        device_address = hiqnet.Device.negotiate_address()
        device = hiqnet.Device(device_name, device_address)
        datastore.put('device_name', value=device_name)
        datastore.put('device_address', value=device_address)
    control = None
    screen = None
    udp_transport = None
    tcp_transport = None

    def build(self):
        reactor.listenTCP(hiqnet.IP_PORT, hiqnet.Factory(self))
        reactor.listenUDP(hiqnet.IP_PORT, hiqnet.UDPProtocol(self))
        reactor.listenUDP(soundcraft.VUMETER_IP_PORT, soundcraft.VuMeterUDPPRotocol(self))
        self.title = APPNAME
        self.icon = 'assets/icon.png'
        self.screen = HiQontrol(list=self.populate())
        return self.screen

    def on_start(self):
        """
        Initialize device and network communications
        """
        self.control = Control(self.device, self.udp_transport, self.tcp_transport)

    def on_pause(self):
        """
        Enable pause mode
        """
        return True

    def store_needs_udate(self):
        self.store_needs_update = True

    def store_update(self, name, address):
        if self.store_needs_update:
            Logger.info(APPNAME + ": Updating store")
            self.datastore.put('device_name', value=name)
            self.datastore.put('device_address', value=int(address))
            Logger.info(APPNAME + ": Store updated, reloading device")
            self.device = hiqnet.Device(self.datastore.get('device_name')['value'],
                                        self.datastore.get('device_address')['value'])
            self.control = Control(self.device, self.udp_transport, self.tcp_transport)
            self.store_needs_update = False

    def get_model(self):
        # FIXME: placeholder
        return "Si Compact 16"

    def get_name(self):
        # FIXME: placeholder
        return "Si Compact 16"

    def get_hiqnet_address(self):
        # FIXME: placeholder
        return str(SI_COMPACT_16_DEVICE_ADDRESS)

    def get_ip_address(self):
        # FIXME: placeholder
        return SI_COMPACT_16_IP

    def get_local_name(self):
        return self.device.manager.name_string

    def get_local_hiqnet_address(self):
        return str(self.device._hiqnet_address)

    def get_local_mac_address(self):
        return self.device.network_info.mac_address

    def get_local_dhcp_status(self):
        return self.device.network_info.dhcp

    def get_local_ip_address(self):
        return self.device.network_info.ip_address

    def get_local_subnet_mask(self):
        return self.device.network_info.subnet_mask

    def get_local_gateway(self):
        return self.device.network_info.gateway_address

    def locate_toggle(self, hiqnet_dest, ip_dest, serial_dest):
        self.control.locate_toggle(hiqnet_dest, ip_dest, serial_dest)

    def populate(self):
        # FIXME: This should be dynamically detected from the network or manually added/removed
        item_strings = ['0', '1']
        integers_dict = {
            '0': {'text': 'Si Compact 16', 'ip_address': SI_COMPACT_16_IP,
                  'hiqnet_address': SI_COMPACT_16_DEVICE_ADDRESS,
                  'is_selected': False},
            '1': {'text': 'Lool', 'ip_address': '192.168.1.3', 'hiqnet_address': 9999, 'is_selected': False}}

        args_converter = \
            lambda row_index, rec: \
            {'text': rec['text'],
             'size_hint_y': None,
             'height': 50,
             'cls_dicts': [{'cls': ListItemButton,
                            'kwargs': {'text': rec['text'],
                                       'is_representing_cls': True}},
                           {'cls': ListInfoButton,
                            'kwargs': {'text': 'i',  # TODO: replace by a nice icon
                                       'size_hint_x': None}},
                           {'cls': ListLocateButton,
                            'kwargs': {'text': 'L',  # TODO: replace by a nice icon
                                       'size_hint_x': None,
                                       'hiqnet_address': rec['hiqnet_address'],
                                       'ip_address': rec['ip_address'],
                                       'serial_number': SI_COMPACT_16_SERIAL}},  # FIXME
                           {'cls': ListMixButton,
                            'kwargs': {'text': '>',  # TODO: replace by a nice icon
                                       'size_hint_x': None}}]}

        dict_adapter = DictAdapter(sorted_keys=item_strings,
                                   data=integers_dict,
                                   args_converter=args_converter,
                                   selection_mode='single',
                                   allow_empty_selection=False,
                                   cls=CompositeListItem)

        return dict_adapter

    def handle_message(self, data, host, protocol):
        """
        Handle messages received thru twisted servers

        Only display it on screen for debugging right now

        :param data:
        :return:
        """
        self.screen.debug.text = protocol + '(' + str(host) + ')' + binascii.hexlify(data)

if __name__ == '__main__':
    HiQontrolApp().run()
