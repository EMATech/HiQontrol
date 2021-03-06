HiQnet Protocol Decoding
========================

::

    Soundcraft Si C16
      32    canaux de mixage
      8     Bus Mix Mono
      6(12) Mix Bus Stéréo
      4(8)  Matrix Bus Stéréo
      4(8)  FX Bus Stéréo
      1(2)  Main Stereo output
      1     Main Mono output
      1(2)  Monitor Stereo output

    HiQnet (Harman iqnet)
    Port: 3804

    locate time 0x1000 produces a 3-4 s flash burst
    any other value seem infinite

    Device Manager Attributes
        0: [Si Compact 16] Class Name
        1: [Si Compact 16] Name
        2: Flags
        3: Serial Number
        4: [V2.0] Version

    Virtual Devices Attributes
        0: Class Name
        1: Name

    Parameter Attributes
        0:
        1:
        2:
        3:
        4:
        5:

    Console VDs:
    1.0.0.1 Mix busses master
      PID 1: ON Mix 1
      [...]
      PID 14: ON Mix 14
      PID 15: ON Mtx 1
      [...]
      PID 18: ON Mtx 4
      PID 19: Fader Mix 1
      [...]
      PID 32: Fader Mix 14
      PID 33: Fader Mtx 1
      [...]
      PID 36: Fader Mtx 4

    1.0.0.2 ????
    1.0.0.3 Main busses master
      PID 1: ON L&R
      PID 2: ON Mono
      PID 3: Fader L&R
      PID 4: Fader Mono
    1.0.0.4 Mix 1 sends
      Cf Master sends
    1.0.0.5 Mix 2 sends
    1.0.0.6 Mix 3 sends
    1.0.0.7 Mix 4 sends
    1.0.0.8 Mix 5 sends
    1.0.0.9 Mix 6 sends
    1.0.0.10 Mix 7 sends
    1.0.0.11 Mix 8 sends
    1.0.0.12 Mix 9 sends
    1.0.0.13 Mix 10 sends
    1.0.0.14 Mix 11 sends
    1.0.0.15 Mix 12 sends
    1.0.0.16 Mix 13 sends
    1.0.0.17 Mix 14 sends
    1.0.0.19 Matrix 1 sends
      PID 1: ON Mix 1
      [...]
      PID 14: ON Mix 14
      PID 15: ON L
      PID 16: ON R
      PID 17: ON Mono
      PID 18: Fader Mix 1
      [...]
      PID 31: Fader Mix 14
      PID 32: Fader L
      PID 33: Fader R
      PID 34: Fader Mono
    1.0.0.19 Matrix 2 sends
    1.0.0.20 Matrix 3 sends
    1.0.0.21 Matrix 4 sends
    1.0.0.22 Master sends
      PID 1: ON CH1
        LONG 0 or 1
      [...]
      PID 36: ON ST4
      PID 37: Fader CH1
        LONG signed 0dB = 0x00000000 -inf (-138dB!?) = 0xffffdd80 +10dB = 0x00000280
      [...]
      PID 72: Fader ST4

    1.0.0.23 Mix 1 GEQ
      PID 1: ON 31 Hz
      PID 28: ON 16kHz
      PID 29: Fader 31 Hz
        LONG signed -12dB = 0xfffffd00 0dB = 0x00000000 +12dB = 0x00000300
    1.0.0.24 Mix 2 GEQ
    1.0.0.25 Mix 3 GEQ
    1.0.0.26 Mix 4 GEQ
    1.0.0.27 Mix 5 GEQ
    1.0.0.28 Mix 6 GEQ
    1.0.0.29 Mix 7 GEQ
    1.0.0.30 Mix 8 GEQ
    1.0.0.31 Mix 9 GEQ
    1.0.0.32 Mix 10 GEQ
    1.0.0.33 Mix 11 GEQ
    1.0.0.34 Mix 12 GEQ
    1.0.0.35 Mix 13 GEQ
    1.0.0.36 Mix 14 GEQ
    1.0.0.37 Matrix 1 GEQ
    1.0.0.38 Matrix 2 GEQ
    1.0.0.39 Matrix 3 GEQ
    1.0.0.40 Matrix 4 GEQ
    1.0.0.41 Master L+R GEQ
    1.0.0.42 Master Mono GEQ
    1.0.0.43 ????
    1.0.0.44 Channels names
      PID 1: CH1
      [...]
      PID 36: ST4
    1.0.0.45 Mix busses names
      PID 1: Mix1
      [...]
      PID 18: Mtx4
    1.0.0.46 Main busses names
      PID 1: L
      PID 2: R
      PID 3: Mono
    1.0.0.47 ????
    1.0.0.48 CH1 Params
      PID 1: Gate On
      PID 2: Gate Threshold
      PID 3: Gate attack
      PID 4: Gate Release
      PID 5: Gate Depth
      PID 6: Gate HP Filter
      PID 7: Gate LP Filter
      PID 8: Comp On
      PID 9: Comp Threshold
      PID 10: Comp Attack
      PID 11: Comp Release
      PID 12: Comp Ratio
      PID 13: Comp Gain
      PID 14: EQ In
      PID 15: LF Freq
      PID 16: LF Gain

      PID 19: Lo Mid Freq
      PID 20: Lo Mid Gain
      PID 21: Lo Mid Q
      PID 22: Hi Mid Freq
      PID 23: Hi Mid Gain
      PID 24: Hi Mid Q
      PID 25: HF Freq
      PID 26: HF Gain

      PID 29: Delay
      PID 30: Phase
      PID 31: HPF On
      PID 32: HP Filter freq
      PID 33: Pan
        L = 0x00000000 C = 0x0000002d R = 0x00000059
      PID 34: L&R Assign
      PID 35: Mono Assign

      PID 38: ? (Sent when Assign changes [PID 34 or 35])
      PID 39: Gain
         LONG signed -5dB = 0xfffffec0 0dB = 0x00000000 58dB = 0x00000e80
      PID 40: +48V

    1.0.0.49 CH2 Params
    1.0.0.50 CH3 Params
    1.0.0.51 CH4 Params
    1.0.0.52 CH5 Params
    1.0.0.53 CH6 Params
    1.0.0.54 CH7 Params
    1.0.0.55 CH8 Params
    1.0.0.56 CH9 Params
    1.0.0.57 CH10 Params
    1.0.0.58 CH11 Params
    1.0.0.59 CH12 Params
    1.0.0.60 CH13 Params
    1.0.0.61 CH14 Params
    1.0.0.62 CH15 Params
    1.0.0.63 CH16 Params
    1.0.0.64 CH17 Params
    1.0.0.65 CH18 Params
    1.0.0.66 CH19 Params
    1.0.0.67 CH20 Params
    1.0.0.68 CH21 Params
    1.0.0.69 CH22 Params
    1.0.0.70 CH23 Params
    1.0.0.71 CH24 Params
    1.0.0.72 CH25 Params
    1.0.0.73 CH26 Params
    1.0.0.74 CH27 Params
    1.0.0.75 CH28 Params
    1.0.0.76 CH29 Params
    1.0.0.77 CH30 Params
    1.0.0.78 CH31 Params
    1.0.0.79 CH32 Params
    1.0.0.80 ST1 Params
      PID 1: Gate On
      PID 2: Gate Threshold
      PID 3: Gate attack
      PID 4: Gate Release
      PID 5: Gate Depth
      PID 6: Gate HP Filter
      PID 7: Gate LP Filter
      PID 8: Comp On
      PID 9: Comp Threshold
      PID 10: Comp Attack
      PID 11: Comp Release
      PID 12: Comp Ratio
      PID 13: Comp Gain
      PID 14: EQ In
      PID 15: LF Freq
      PID 16: LF Gain

      PID 19: Lo Mid Freq
      PID 20: Lo Mid Gain
      PID 21: Lo Mid Q
      PID 22: Hi Mid Freq
      PID 23: Hi Mid Gain
      PID 24: Hi Mid Q
      PID 25: HF Freq
      PID 26: HF Gain

      PID 29: Delay
      PID 30: Phase
      PID 31: HPF On
      PID 32: HP Filter freq
      PID 33: Pan
        L = 0x00000000 C = 0x0000002d R = 0x00000059
      PID 34: L&R Assign
      PID 35: Mono Assign

      PID 38: ? (Sent when Assign changes [PID 34 or 35])
      PID 39: Trim
    1.0.0.81 ST2 Params
    1.0.0.82 ST3 Params
    1.0.0.83 ST4 Params
    1.0.0.84 Mix 1 Params
      PID 1: Comp On
      PID 2: Comp Threshold
      PID 3: Comp Attack
      PID 4: Comp Release
      PID 5: Comp Ratio
      PID 6: Comp Gain
      PID 7: EQ On
      PID 8: LF Freq
      PID 9: LF Gain

      PID 12: Lo Mid Freq
      PID 13: Lo Mid Gain
      PID 14: Lo Mid Q
      PID 15: Hi Mid Freq
      PID 16: Hi Mid Gain
      PID 17: Hi Mid Q
      PID 18: HF Freq
      PID 19: HF Gain

      PID 22: Delay
      PID 23: Phase
      PID 24: HPF On
      PID 25: HP Filter Freq
      PID 26: Pan
      PID 27: L&R Assign
      PID 28: Mono Assign

      PID 31: ? (Sent when Assign changes [PID 34 or 35])
    [...]
    1.0.0.97 Mix 14 Params
    1.0.0.98 Matrix 1 Params
      PID 1: Comp On
      PID 2: Comp Threshold
      PID 3: Comp Attack
      PID 4: Comp Release
      PID 5: Comp Ratio
      PID 6: Comp Gain
      PID 7: EQ On
      PID 8: LF Freq
      PID 9: LF Gain

      PID 12: Lo Mid Freq
      PID 13: Lo Mid Gain
      PID 14: Lo Mid Q
      PID 15: Hi Mid Freq
      PID 16: Hi Mid Gain
      PID 17: Hi Mid Q
      PID 18: HF Freq
      PID 19: HF Gain

      PID 22: Delay
    [...]
    1.0.0.101 Matrix 4 Params
    1.0.0.102 L&R Params
      PID 1: Comp On
      PID 2: Comp Threshold
      PID 3: Comp Attack
      PID 4: Comp Release
      PID 5: Comp Ratio
      PID 6: Comp Gain
      PID 7: EQ On
      PID 8: LF Freq
      PID 9: LF Gain

      PID 12: Lo Mid Freq
      PID 13: Lo Mid Gain
      PID 14: Lo Mid Q
      PID 15: Hi Mid Freq
      PID 16: Hi Mid Gain
      PID 17: Hi Mid Q
      PID 18: HF Freq
      PID 19: HF Gain

      PID 22: Delay

      PID 25: Balance
    1.0.0.103 Mono Params
      Cf Matrix params
    1.0.0.104 FX1 sends
      Cf Master sends
    1.0.0.105 FX2 sends
    1.0.0.106 FX3 sends
    1.0.0.107 FX4 sends




    Meters: UDP 3333 ?
      Payload 624o
      1 of 2 in VLAN 1
      AA BB CC DD
      AA BB -> VU value ?
      CC -> Comp gain reduction ?
      DD = 0x09 -> No gate
      DD = 0x01 -> Gate close
      DD = 0x04 -> Gate open
      DD = 0x0c -> Gate hold ????

      Groupes de 4 octects

      16 premiers = 16 CH
      16 suivants : voir meter_packet_decode.txt

      2 derniers -> Monitor

      VU ()
        32+4*2+8+6*2+4*2+2+1 = 71
      Gate (Bool ou tristate)
        32+4 = 36
      Comp
        32+4+8+6+4+2 = 56

