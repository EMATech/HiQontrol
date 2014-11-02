import hiqnet
import re
from random import randrange
from kivy.app import App
from kivy.logger import Logger
from kivy.storage.jsonstore import JsonStore
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.textinput import TextInput

# FIXME: this should not be hardcoded but autodetected
SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

APPNAME = 'HiQontrol'

class HiQontrol(ScreenManager):
    pass


class HomeScreen(Screen):
    pass


class MixScreenProto(Screen):
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

    def init(self):
        c = hiqnet.Connection()
        source_address = hiqnet.FQHiQnetAddress(device_address=self.source_device.hiqnet_address)
        destination_address = hiqnet.FQHiQnetAddress(SI_COMPACT_16_DEVICE_ADDRESS)
        message = hiqnet.HiQnetMessage(source=source_address, destination=destination_address)
        return c, message

    def locateToggle(self):
        c, message = self.init()
        if not self.locate:
            message.LocateOn(SI_COMPACT_16_SERIAL)
            self.locate = True
        else:
            message.LocateOff(SI_COMPACT_16_SERIAL)
            self.locate = False
        c.sendto(message, SI_COMPACT_16_IP)


class HiQontrolApp(App):
    __version__ = '0.0.2'
    datastore = JsonStore('settings.json')
    try:
        device = hiqnet.Device(datastore.get('device_name')['value'], datastore.get('device_address')['value'])
    except KeyError:
        Logger.warning(APPNAME + ': Settings not found, will use sane defaults')
        device_name = APPNAME
        # FIXME: address should be negotiated
        device_address = randrange(1, 65535)
        device = hiqnet.Device(device_name, device_address)
        datastore.put('device_name', value=device_name)
        datastore.put('device_address', value=device_address)
    control = None

    def on_start(self):
        """
        Initialize device and network communications
        """
        self.device.startServer()
        self.control = Control(self.device)

    def on_pause(self):
        """
        Enable pause mode

        Note: stopping the server here to restart it on_resume seems the obvious thing to do but it does not work.
              Don't do it! All you'll get is an address already in use error.
        """
        return True

    def on_resume(self):
        pass

    def on_stop(self):
        self.device.stopServer()

    def build(self):
        self.title = APPNAME
        self.icon = 'assets/icon.png'
        return HiQontrol()

    def storeUpdate(self):
        Logger.info("Store updated, reloading device")
        self.device.stopServer()
        self.device = hiqnet.Device(self.datastore.get('device_name')['value'],
                                    self.datastore.get('device_address')['value'])
        self.control = self.control = Control(self.device)

    def locateToggle(self):
        self.control.locateToggle()

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

if __name__ == '__main__':
    HiQontrolApp().run()
