import hiqnet
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image

SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

__version__ = '0.0.1'


class HiQontrol(ScreenManager):
    pass


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class MixScreenProto(Screen):
    pass


class Logo(Image):
    pass


class Control():
    locate = False

    def __init__(self):
        pass

    def init(self):
        source_device = hiqnet.DeviceManager()
        c = hiqnet.Connection()
        source_address = hiqnet.FQHiQnetAddress(device_address=source_device.hiqnet_address)
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
    control = Control()

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

if __name__ == '__main__':
    HiQontrolApp().run()
