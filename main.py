import hiqnet
import re
from kivy.app import App
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.adapters.dictadapter import DictAdapter
from kivy.properties import ObjectProperty
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput
from kivy.uix.listview import CompositeListItem, ListItemButton, ListItemLabel

# FIXME: this should not be hardcoded but autodetected
SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

APPNAME = 'HiQontrol'


class ListLocateButton(ListItemButton):
    def __init__(self, **kwargs):
        self.hiqnet_address = kwargs['hiqnet_address']
        self.ip_address = kwargs['ip_address']
        self.serial_number = kwargs['serial_number']
        super(ListLocateButton, self).__init__(**kwargs)


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


class Control():
    locate = False
    source_device = None

    def __init__(self, source_device):
        self.source_device = source_device

    def init(self, hiqnet_dest):
        c = hiqnet.Connection()
        source_address = hiqnet.FQHiQnetAddress(device_address=self.source_device.hiqnet_address)
        destination_address = hiqnet.FQHiQnetAddress(hiqnet_dest)
        message = hiqnet.HiQnetMessage(source=source_address, destination=destination_address)
        return c, message

    def locateToggle(self, hiqnet_dest, ip_dest, serial_dest):
        c, message = self.init(hiqnet_dest)
        if not self.locate:
            message.LocateOn(serial_dest)
            self.locate = True
        else:
            message.LocateOff(serial_dest)
            self.locate = False
        c.sendto(message, ip_dest)


class HiQontrol(ScreenManager):
    list = ObjectProperty()


class HiQontrolApp(App):
    __version__ = '0.0.2'
    datastore = JsonStore('settings.json')
    store_needs_update = False
    try:
        device = hiqnet.Device(datastore.get('device_name')['value'], datastore.get('device_address')['value'])
    except KeyError:
        Logger.warning(APPNAME + ': Settings not found, will use sane defaults')
        device_name = APPNAME
        device_address = hiqnet.Device.negotiateAddress()
        device = hiqnet.Device(device_name, device_address)
        datastore.put('device_name', value=device_name)
        datastore.put('device_address', value=device_address)
    control = None

    def build(self):
        self.title = APPNAME
        self.icon = 'assets/icon.png'
        return HiQontrol(list=self.populate())

    def on_start(self):
        """
        Initialize device and network communications
        """
        self.device.startServer()
        self.control = Control(self.device)

    def on_pause(self):
        """
        Enable pause mode
        """
        self.device.stopServer()
        return True

    def on_resume(self):
        self.device.startServer()
        pass

    def on_stop(self):
        self.device.stopServer()

    def storeNeedsUpdate(self):
        self.store_needs_update = True

    def storeUpdate(self, name, address):
        if self.store_needs_update:
            Logger.info(APPNAME + ": Updating store")
            self.datastore.put('device_name', value=name)
            self.datastore.put('device_address', value=int(address))
            Logger.info(APPNAME + ": Store updated, reloading device")
            self.device.stopServer()
            self.device = hiqnet.Device(self.datastore.get('device_name')['value'],
                                        self.datastore.get('device_address')['value'])
            self.device.startServer()
            self.control = Control(self.device)
            self.store_needs_update = False

    def getHiQnetAddress(self):
        # FIXME: placeholder
        return str(SI_COMPACT_16_DEVICE_ADDRESS)

    def getIPAddress(self):
        # FIXME: placeholder
        return SI_COMPACT_16_IP

    def getLocalName(self):
        return self.device.manager.name_string

    def getLocalHiQNetAddress(self):
        return str(self.device.hiqnet_address)

    def getLocalMACAddress(self):
        return self.device.network_info.mac_address

    def getLocalDHCPStatus(self):
        return self.device.network_info.dhcp

    def getLocalIPAddress(self):
        return self.device.network_info.ip_address

    def getLocalSubnetMask(self):
        return self.device.network_info.subnet_mask

    def getLocalGateway(self):
        return self.device.network_info.gateway_address

    def locateToggle(self, hiqnet_dest, ip_dest, serial_dest):
        self.control.locateToggle(hiqnet_dest, ip_dest, serial_dest)

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
                 'height': 25,
                 'cls_dicts': [{'cls': ListItemLabel,
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


if __name__ == '__main__':
    HiQontrolApp().run()
