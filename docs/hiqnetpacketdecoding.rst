HiQnet Packet Decoding
======================

::

    [Header]
    02      Version
    1b      Header length (27)
    00      Message length MSB
    00
    00
    2f      Message length LSB (47)
    f7      Source address MSB
    f2
    00
    00
    00
    00      Source address LSB
    06      Destination address MSB
    53
    00
    00
    00
    00      Destination address LSB
    01      Message ID MSB
    29      Message ID LSB (locate)
    01      Flags MSB
    20      Flags LSB (0000 0001 0010 0000) [Session + Guaranteed]
    04      Hop
    00      Seq num MSB
    14      Seq num LSB
    6e      Sess num MSB
    04      Sess num LSB
    [Payload]
    ff      locate MSB
    ff      locate LSB (Always on)
    00
    10
    53
    69
    43
    6f
    6d
    70
    61
    63
    74
    00
    00
    00
    00
    00
    00
    00

