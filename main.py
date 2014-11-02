import hiqnet
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image

# FIXME: this should not be hardcoded but autodetected
SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

# TODO: add configuration for MY_DEVICE* parameters
MY_DEVICE_NAME = 'HiQontrol'
# FIXME: this should be assigned automatically
MY_DEVICE_ADDRESS = 2376


class HiQontrol(ScreenManager):
    pass


class HomeScreen(Screen):
    pass


class MixScreenProto(Screen):
    pass


class Control():
    locate = False

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
    device = hiqnet.Device(MY_DEVICE_NAME, MY_DEVICE_ADDRESS)
    control = Control(device)

    def build(self):
        self.title = 'HiQontrol'
        self.icon = 'assets/icon.png'
        return HiQontrol()

    def locateToggle(self):
        self.control.locateToggle()

    def getHiQnetAddress(self):
        # FIXME: placeholder
        return '1629'

    def getIPAddress(self):
        # FIXME: placeholder
        return '192.168.1.6'

    def getLocalName(self):
        return self.device.device_manager.name_string

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
