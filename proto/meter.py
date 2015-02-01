import socket
import sys

IPV4 = ''
PORT = 3333


def main(argv):
    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
    s.bind((IPV4, PORT))

    while True:
        packet, address = s.recvfrom(65536)
        parse_packet(packet)


# noinspection PyArgumentList
def parse_packet(packet):
    print(sys.getsizeof(packet))
    print(packet)

if __name__ == "__main__":
    main(sys.argv)
