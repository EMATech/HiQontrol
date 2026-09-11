"""Binary protocol tests for HiQnet feedback subscriptions (issue #13)."""

import os
import struct
import sys
import types
import unittest


ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HIQNET = os.path.join(ROOT, 'hiqontrol', 'hiqnet')
sys.path.insert(0, HIQNET)

# protocol.py only needs the names during DiscoInfo decoding/building.  Keep
# these unit tests independent of a host network interface and netifaces.
networkinfo = types.ModuleType('networkinfo')
networkinfo.NetworkInfo = type('NetworkInfo', (), {'NET_ID_TCP_IP': 1, 'NET_ID_RS232': 4})
networkinfo.IPNetworkInfo = type('IPNetworkInfo', (), {})
networkinfo.RS232NetworkInfo = type('RS232NetworkInfo', (), {})
sys.modules.setdefault('networkinfo', networkinfo)

import protocol  # noqa: E402


def address(device, vd=0, object_address=0):
    return protocol.FullyQualifiedAddress(
        device_address=device,
        vd_address=struct.pack('!B', vd),
        object_address=struct.pack('!I', object_address)[1:],
    )


class FeedbackProtocolTests(unittest.TestCase):
    def command(self):
        return protocol.Command(source=address(100), destination=address(1619, 1, 48))

    def test_hello_is_guaranteed_and_carries_a_nonzero_session(self):
        command = self.command()
        session = command.hello(session_number=0x1234)
        encoded = bytes(command)

        self.assertEqual(session, 0x1234)
        self.assertEqual(encoded[18:20], b'\x00\x08')
        self.assertEqual(struct.unpack('!H', encoded[20:22])[0], 0x0020)
        self.assertEqual(encoded[25:], b'\x12\x34\x01\xff')

    def test_hello_info_echoes_remote_session_in_header(self):
        command = self.command()
        command.hello_info(0x2345, local_session_number=0x3456)
        encoded = bytes(command)

        self.assertEqual(encoded[1], 27)
        self.assertEqual(struct.unpack('!H', encoded[20:22])[0], 0x0124)
        self.assertEqual(encoded[25:27], b'\x23\x45')
        self.assertEqual(encoded[27:], b'\x34\x56\x01\xff')

    def test_multi_parameter_subscription_matches_documented_layout(self):
        command = self.command()
        subscriber = address(100, 1, 9)
        command.multi_param_subscribe([
            (7, subscriber, 70, 100),
            (8, subscriber, 80, 250),
        ])
        encoded = bytes(command)

        self.assertEqual(encoded[18:20], b'\x01\x0f')
        payload = encoded[25:]
        self.assertEqual(struct.unpack('!H', payload[:2])[0], 2)
        self.assertEqual(len(payload), 34)
        self.assertEqual(payload[2:4], b'\x00\x07')
        self.assertEqual(payload[4], 0)
        self.assertEqual(payload[5:11], bytes(subscriber))
        self.assertEqual(payload[11:13], b'\x00\x46')
        self.assertEqual(payload[13:16], b'\x00\x00\x00')
        self.assertEqual(payload[16:18], b'\x00\x64')
        self.assertEqual(payload[18:20], b'\x00\x08')
        self.assertEqual(payload[32:34], b'\x00\xfa')

    def test_command_flags_do_not_leak_between_messages(self):
        hello = self.command()
        hello.hello(session_number=1)
        plain = self.command()
        plain.get_vd_list()

        self.assertEqual(struct.unpack('!H', bytes(hello)[20:22])[0], 0x0020)
        self.assertEqual(struct.unpack('!H', bytes(plain)[20:22])[0], 0)


if __name__ == '__main__':
    unittest.main()
