#!/usr/bin/env python3

from common.tracker import Tracker
from common.gsmtaphdr import GsmtapHdr
from optparse import OptionParser
import socket

imsitracker = None

# return mcc mnc, lac, cell, country, brand, operator
def find_cell(gsm, udpdata, t=None):
    # find_cell() update all following variables
    global mcc
    global mnc
    global lac
    global cell
    global country
    global brand
    global operator

    if gsm.sub_type == 0x01:  # Channel Type == BCCH (0)
        p = bytearray(udpdata)
        if p[0x12] == 0x1b:  # (0x12 + 0x2a = 0x3c) Message Type: System Information Type 3
            # FIXME
            m = hex(p[0x15])
            if len(m) < 4:
                mcc = m[2] + '0'
            else:
                mcc = m[3] + m[2]
            mcc += str(p[0x16] & 0x0f)

            # FIXME not works with mnc like 005 or 490
            m = hex(p[0x17])
            if len(m) < 4:
                mnc = m[2] + '0'
            else:
                mnc = m[3] + m[2]

            lac = p[0x18] * 256 + p[0x19]
            cell = p[0x13] * 256 + p[0x14]
            t.current_cell(mcc, mnc, lac, cell)


def find_imsi(udpdata, t=None):
    if t is None:
        t = imsitracker

    # Create object representing gsmtap header in UDP payload
    gsm = GsmtapHdr.from_buffer_copy(udpdata)

    if gsm.sub_type == 0x1:  # Channel Type == BCCH (0)
        # Update global cell info if found in package
        # FIXME : when you change the frequency, this informations is
        # not immediately updated.  So you could have wrong values when
        # printing IMSI :-/
        find_cell(gsm, udpdata, t=t)
    else:  # Channel Type != BCCH (0)
        p = bytearray(udpdata)
        tmsi1 = ""
        tmsi2 = ""
        imsi1 = ""
        imsi2 = ""
        if p[0x12] == 0x21:  # Message Type: Paging Request Type 1
            if p[0x14] == 0x08 and (p[0x15] & 0x1) == 0x1:  # Channel 1: TCH/F (Full rate) (2)
                # Mobile Identity 1 Type: IMSI (1)
                """
                        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
                0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
                0010   00 43 1c d4 40 00 40 11 1f d4 7f 00 00 01 7f 00
                0020   00 01 c2 e4 12 79 00 2f fe 42 02 04 01 00 00 00
                0030   c9 00 00 16 21 26 02 00 07 00 31 06 21 00 08 XX
                0040   XX XX XX XX XX XX XX 2b 2b 2b 2b 2b 2b 2b 2b 2b
                0050   2b
                XX XX XX XX XX XX XX XX = IMSI
                """
                imsi1 = p[0x15:][:8]
                # p[0x10] == 0x59 = l2 pseudo length value: 22
                if p[0x10] == 0x59 and p[0x1E] == 0x08 and (p[0x1F] & 0x1) == 0x1:  # Channel 2: TCH/F (Full rate) (2)
                    # Mobile Identity 2 Type: IMSI (1)
                    """
                        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
                0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
                0010   00 43 90 95 40 00 40 11 ac 12 7f 00 00 01 7f 00
                0020   00 01 b4 1c 12 79 00 2f fe 42 02 04 01 00 00 00
                0030   c8 00 00 16 51 c6 02 00 08 00 59 06 21 00 08 YY
                0040   YY YY YY YY YY YY YY 17 08 XX XX XX XX XX XX XX
                0050   XX
                YY YY YY YY YY YY YY YY = IMSI 1
                XX XX XX XX XX XX XX XX = IMSI 2
                    """
                    imsi2 = p[0x1F:][:8]
                elif p[0x10] == 0x4d and p[0x1E] == 0x05 and p[0x1F] == 0xf4:  # Channel 2: TCH/F (Full rate) (2)
                    # Mobile Identity - Mobile Identity 2 - IMSI
                    """
                        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
                0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
                0010   00 43 f6 92 40 00 40 11 46 15 7f 00 00 01 7f 00
                0020   00 01 ab c1 12 79 00 2f fe 42 02 04 01 00 00 00
                0030   d8 00 00 23 3e be 02 00 05 00 4d 06 21 a0 08 YY
                0040   YY YY YY YY YY YY YY 17 05 f4 XX XX XX XX 2b 2b
                0050   2b
                YY YY YY YY YY YY YY YY = IMSI 1
                XX XX XX XX = TMSI
                    """
                    tmsi1 = p[0x20:][:4]

                t.register_imsi(gsm.arfcn, gsm.signal_dbm, imsi1, imsi2, tmsi1, tmsi2)

            elif p[0x1B] == 0x08 and (p[0x1C] & 0x1) == 0x1:  # Channel 2: TCH/F (Full rate) (2)
                # Mobile Identity 2 Type: IMSI (1)
                """
                        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
                0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
                0010   00 43 57 8e 40 00 40 11 e5 19 7f 00 00 01 7f 00
                0020   00 01 99 d4 12 79 00 2f fe 42 02 04 01 00 00 00
                0030   c7 00 00 11 05 99 02 00 03 00 4d 06 21 00 05 f4
                0040   yy yy yy yy 17 08 XX XX XX XX XX XX XX XX 2b 2b
                0050   2b
                yy yy yy yy = TMSI/P-TMSI - Mobile Identity 1
                XX XX XX XX XX XX XX XX = IMSI
                """
                tmsi1 = p[0x16:][:4]
                imsi2 = p[0x1C:][:8]
                t.register_imsi(gsm.arfcn, gsm.signal_dbm, imsi1, imsi2, tmsi1, tmsi2)

            elif p[0x14] == 0x05 and (p[0x15] & 0x07) == 4:  # Mobile Identity - Mobile Identity 1 - TMSI/P-TMSI
                """
                        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
                0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
                0010   00 43 b3 f7 40 00 40 11 88 b0 7f 00 00 01 7f 00
                0020   00 01 ce 50 12 79 00 2f fe 42 02 04 01 00 03 fd
                0030   d1 00 00 1b 03 5e 05 00 00 00 41 06 21 00 05 f4
                0040   XX XX XX XX 17 05 f4 YY YY YY YY 2b 2b 2b 2b 2b
                0050   2b
                XX XX XX XX = TMSI/P-TMSI - Mobile Identity 1
                YY YY YY YY = TMSI/P-TMSI - Mobile Identity 2
                """
                tmsi1 = p[0x16:][:4]
                if p[0x1B] == 0x05 and (p[0x1C] & 0x07) == 4:  # Mobile Identity - Mobile Identity 2 - TMSI/P-TMSI
                    tmsi2 = p[0x1D:][:4]
                else:
                    tmsi2 = ""

                t.register_imsi(gsm.arfcn, gsm.signal_dbm, imsi1, imsi2, tmsi1, tmsi2)

        elif p[0x12] == 0x22:  # Message Type: Paging Request Type 2
            if p[0x1D] == 0x08 and (p[0x1E] & 0x1) == 0x1:  # Mobile Identity 3 Type: IMSI (1)
                """
                        0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
                0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
                0010   00 43 1c a6 40 00 40 11 20 02 7f 00 00 01 7f 00
                0020   00 01 c2 e4 12 79 00 2f fe 42 02 04 01 00 00 00
                0030   c9 00 00 16 20 e3 02 00 04 00 55 06 22 00 yy yy
                0040   yy yy zz zz zz 4e 17 08 XX XX XX XX XX XX XX XX
                0050   8b
                yy yy yy yy = TMSI/P-TMSI - Mobile Identity 1
                zz zz zz zz = TMSI/P-TMSI - Mobile Identity 2
                XX XX XX XX XX XX XX XX = IMSI
                """
                tmsi1 = p[0x14:][:4]
                tmsi2 = p[0x18:][:4]
                imsi2 = p[0x1E:][:8]
                t.register_imsi(gsm.arfcn, gsm.signal_dbm, imsi1, imsi2, tmsi1, tmsi2)


def udpserver(port, prn):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_address = ('localhost', port)
    sock.bind(server_address)
    while True:
        udpdata, address = sock.recvfrom(4096)
        if prn:
            prn(udpdata)


def find_imsi_from_pkt(p):
    udpdata = bytes(p[UDP].payload)
    find_imsi(udpdata)


if __name__ == "__main__":
    imsitracker = Tracker()
    parser = OptionParser(usage="%prog: [options]")
    parser.add_option("-i", "--iface", dest="iface", default="lo", help="Interface (default : lo)")
    parser.add_option("-p", "--port", dest="port", default="4729", type="int", help="Port (default : 4729)")
    parser.add_option("-s", "--sniff", action="store_true", dest="sniff", help="sniff on interface instead of listening on port (require root/suid access)")
    (options, args) = parser.parse_args()
    if options.sniff:
        from scapy.all import sniff, UDP
        imsitracker.header()
        sniff(iface=options.iface, filter=f"port {options.port} and not icmp and udp", prn=find_imsi_from_pkt, store=0)
    else:
        imsitracker.header()
        udpserver(port=options.port, prn=find_imsi)
