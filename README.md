HiQontrol
=========

An attempt at building a free, open source, multi-platform ViSi Remote alternative

Status
======

Work In Progress, [Proof of Concept](https://github.com/EMATech/HiQontrol/releases/tag/v0.0.1) available for Android

TODO
====

- Autodetect compatible HiQnet devices on the network and list them properly (Disco)
- VU-Meter messages parsing and page
- Graphic EQs
- Volumes
- Channel properties
    - Gain
    - Gate
    - Comp
    - EQ
    - Pan
- Sends
    - Bus
    - Mtx
    - FX

Dependencies
============

- Python 2 (Python 3 Kivy does not support Twisted ATM)
- [Kivy](kivy.org)
- Netifaces
- Twisted

License
=======
Copyright (C) 2014–2015 Raphaël Doursenaud <rdoursenaud@free.fr>

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
