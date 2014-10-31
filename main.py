import hiqnet
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.widget import Widget

SI_COMPACT_16_IP = '192.168.1.6'
SI_COMPACT_16_DEVICE_ADDRESS = 1619  # 0x653
SI_COMPACT_16_SERIAL = b'\x53\x69\x43\x6f\x6d\x70\x61\x63\x74\x00\x00\x00\x00\x00\x00\x00'  # SiCompact

class HiQontrol(ScreenManager):
    pass


class MainScreen(Screen):
    pass


class SettingsScreen(Screen):
    pass


class HiQontrolApp(App):
    locate = False

    def build(self):
        return HiQontrol()

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


if __name__ == '__main__':
    HiQontrolApp().run()
