#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Oros
# Contributors :
#  purwowd
#  puyoulu
#  1kali2kali
#  petterreinholdtsen
#  nicoeg
#  dspinellis
#  fdl <Frederic.Lehobey@proxience.com>
# 2020-08-15
# License : CC0 1.0 Universal

"""
This program shows you IMSI numbers of cellphones around you.


/! This program was made to understand how GSM network work. Not for bad hacking !
"""

import ctypes
import json
from optparse import OptionParser
import datetime
import io
import socket

imsitracker = None


class tracker:
    imsistate = {}
    # phones
    imsis = []  # [IMSI,...]
    tmsis = {}  # {TMSI:IMSI,...}
    nb_IMSI = 0  # count the number of IMSI

    mcc = ""
    mnc = ""
    lac = ""
    cell = ""
    country = ""
    brand = ""
    operator = ""

    # in minutes
    purgeTimer = 10  # default 10 min

    show_all_tmsi = False
    mcc_codes = None
    sqlite_con = None
    mysql_con = None
    mysql_cur = None
    textfilePath = None
    output_function = None

    def __init__(self):
        self.load_mcc_codes()
        self.track_this_imsi("")
        self.output_function = self.output

    def set_output_function(self, new_output_function):
        # New output function need this field :
        # cpt, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell, timestamp, packet=None
        self.output_function = new_output_function

    def track_this_imsi(self, imsi_to_track):
        self.imsi_to_track = imsi_to_track
        self.imsi_to_track_len = len(imsi_to_track)

    # return something like '0xd9605460'
    def str_tmsi(self, tmsi):
        if tmsi != "":
            new_tmsi = "0x"
            for a in tmsi:
                c = hex(a)
                if len(c) == 4:
                    new_tmsi += str(c[2]) + str(c[3])
                else:
                    new_tmsi += "0" + str(c[2])
            return new_tmsi
        else:
            return ""

    def decode_imsi(self, imsi):
        new_imsi = ''
        for a in imsi:
            c = hex(a)
            if len(c) == 4:
                new_imsi += str(c[3]) + str(c[2])
            else:
                new_imsi += str(c[2]) + "0"

        mcc = new_imsi[1:4]
        mnc = new_imsi[4:6]
        return new_imsi, mcc, mnc

    # return something like
    # '208 20 1752XXXXXX', 'France', 'Bouygues', 'Bouygues Telecom'
    def str_imsi(self, imsi, packet=""):
        new_imsi, mcc, mnc = self.decode_imsi(imsi)
        country = ""
        brand = ""
        operator = ""
        if mcc in self.mcc_codes:
            if mnc in self.mcc_codes[mcc]:
                brand, operator, country, _ = self.mcc_codes[mcc][mnc]
                new_imsi = mcc + " " + mnc + " " + new_imsi[6:]
            elif mnc + new_imsi[6:7] in self.mcc_codes[mcc]:
                mnc += new_imsi[6:7]
                brand, operator, country, _ = self.mcc_codes[mcc][mnc]
                new_imsi = mcc + " " + mnc + " " + new_imsi[7:]
        else:
            country = "Unknown MCC {}".format(mcc)
            brand = "Unknown MNC {}".format(mnc)
            operator = "Unknown MNC {}".format(mnc)
            new_imsi = mcc + " " + mnc + " " + new_imsi[6:]

        try:
            return new_imsi, country, brand, operator
        except Exception:
            # m = ""
            print("Error", packet, new_imsi, country, brand, operator)
        return "", "", "", ""

    def load_mcc_codes(self):
        # mcc codes form https://en.wikipedia.org/wiki/Mobile_Network_Code
        with io.open('mcc-mnc/mcc_codes.json', 'r', encoding='utf8') as file:
            self.mcc_codes = json.load(file)

    def current_cell(self, mcc, mnc, lac, cell):
        brand = ""
        operator = ""
        country = ""
        if mcc in self.mcc_codes and mnc in self.mcc_codes[mcc]:
            brand, operator, country, _ = self.mcc_codes[mcc][mnc]
        else:
            country = "Unknown MCC {}".format(mcc)
            brand = "Unknown MNC {}".format(mnc)
            operator = "Unknown MNC {}".format(mnc)
        self.mcc = str(mcc)
        self.mnc = str(mnc)
        self.lac = str(lac)
        self.cell = str(cell)
        self.country = country
        self.brand = brand
        self.operator = operator

    def sqlite_file(self, filename):
        import sqlite3  # Avoid pulling in sqlite3 when not saving
        print("Saving to SQLite database in %s" % filename)
        self.sqlite_con = sqlite3.connect(filename)
        # FIXME Figure out proper SQL type for each attribute
        self.sqlite_con.execute("CREATE TABLE IF NOT EXISTS observations(stamp datetime, tmsi1 text, tmsi2 text, imsi text, imsicountry text, imsibrand text, imsioperator text, mcc integer, mnc integer, lac integer, cell integer);")

    def text_file(self, filename):
        txt = open(filename, "w")
        txt.write("stamp, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell\n")
        txt.close()
        self.textfilePath = filename

    def mysql_file(self):
        import os.path
        if os.path.isfile('.env'):
            import MySQLdb as mdb
            from decouple import config
            self.mysql_con = mdb.connect(config("MYSQL_HOST"), config("MYSQL_USER"), config("MYSQL_PASSWORD"), config("MYSQL_DB"))
            self.mysql_cur = self.mysql_con.cursor()
            # Check MySQL connection
            if self.mysql_cur:
                print("mysql connection is success :)")
            else:
                print("mysql connection is failed!")
                exit()
        else:
            print("create file .env first")
            exit()

    def output(self, cpt, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell, now, packet=None):
        print("{:7s} ; {:10s} ; {:10s} ; {:17s} ; {:12s} ; {:10s} ; {:21s} ; {:4s} ; {:5s} ; {:6s} ; {:6s} ; {:s}".format(str(cpt), tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, str(mcc), str(mnc), str(lac), str(cell), now.isoformat()))

    def pfields(self, cpt, tmsi1, tmsi2, imsi, mcc, mnc, lac, cell, packet=None):
        imsicountry = ""
        imsibrand = ""
        imsioperator = ""
        if imsi:
            imsi, imsicountry, imsibrand, imsioperator = self.str_imsi(imsi, packet)
        else:
            imsi = ""
        now = datetime.datetime.now()
        self.output_function(cpt, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell, now, packet)

        if self.textfilePath:
            now = datetime.datetime.now()
            txt = open(self.textfilePath, "a")
            txt.write(str(now) + ", " + tmsi1 + ", " + tmsi2 + ", " + imsi + ", " + imsicountry + ", " + imsibrand + ", " + imsioperator + ", " + mcc + ", " + mnc + ", " + lac + ", " + cell + "\n")
            txt.close()

        if tmsi1 == "":
            tmsi1 = None
        if tmsi2 == "":
            tmsi2 = None

        if self.sqlite_con:
            self.sqlite_con.execute(
                u"INSERT INTO observations (stamp, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell) " + "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);",
                (now, tmsi1, tmsi2, imsi, imsicountry, imsibrand, imsioperator, mcc, mnc, lac, cell)
            )
            self.sqlite_con.commit()

        if self.mysql_cur:
            print("saving data to db...")
            # Example query
            query = ("INSERT INTO `imsi` (`tmsi1`, `tmsi2`, `imsi`,`mcc`, `mnc`, `lac`, `cell_id`, `stamp`, `deviceid`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)")
            arg = (tmsi1, tmsi2, imsi, mcc, mnc, lac, cell, now, "rtl")
            self.mysql_cur.execute(query, arg)
            self.mysql_con.commit()

    def header(self):
        print("{:7s} ; {:10s} ; {:10s} ; {:17s} ; {:12s} ; {:10s} ; {:21s} ; {:4s} ; {:5s} ; {:6s} ; {:6s} ; {:s}".format("Nb IMSI", "TMSI-1", "TMSI-2", "IMSI", "country", "brand", "operator", "MCC", "MNC", "LAC", "CellId", "Timestamp"))

    def register_imsi(self, arfcn, imsi1="", imsi2="", tmsi1="", tmsi2="", p=""):
        do_print = False
        n = ''
        tmsi1 = self.str_tmsi(tmsi1)
        tmsi2 = self.str_tmsi(tmsi2)
        if imsi1:
            self.imsi_seen(imsi1, arfcn)
        if imsi2:
            self.imsi_seen(imsi2, arfcn)
        if imsi1 and (not self.imsi_to_track or imsi1[:self.imsi_to_track_len] == self.imsi_to_track):
            if imsi1 not in self.imsis:
                # new IMSI
                do_print = True
                self.imsis.append(imsi1)
                self.nb_IMSI += 1
                n = self.nb_IMSI
            if self.tmsis and tmsi1 and (tmsi1 not in self.tmsis or self.tmsis[tmsi1] != imsi1):
                # new TMSI to an ISMI
                do_print = True
                self.tmsis[tmsi1] = imsi1
            if self.tmsis and tmsi2 and (tmsi2 not in self.tmsis or self.tmsis[tmsi2] != imsi1):
                # new TMSI to an ISMI
                do_print = True
                self.tmsis[tmsi2] = imsi1

        if imsi2 and (not self.imsi_to_track or imsi2[:self.imsi_to_track_len] == self.imsi_to_track):
            if imsi2 not in self.imsis:
                # new IMSI
                do_print = True
                self.imsis.append(imsi2)
                self.nb_IMSI += 1
                n = self.nb_IMSI
            if self.tmsis and tmsi1 and (tmsi1 not in self.tmsis or self.tmsis[tmsi1] != imsi2):
                # new TMSI to an ISMI
                do_print = True
                self.tmsis[tmsi1] = imsi2
            if self.tmsis and tmsi2 and (tmsi2 not in self.tmsis or self.tmsis[tmsi2] != imsi2):
                # new TMSI to an ISMI
                do_print = True
                self.tmsis[tmsi2] = imsi2

                # Unreachable or rarely reached branch? Add unit-test.
        if not imsi1 and not imsi2 and tmsi1 and tmsi2:
            if self.tmsis and tmsi2 in self.tmsis:
                # switch the TMSI
                do_print = True
                imsi1 = self.tmsis[tmsi2]
                self.tmsis[tmsi1] = imsi1
                del self.tmsis[tmsi2]

        if do_print:
            if imsi1:
                self.pfields(str(n), tmsi1, tmsi2, imsi1, str(self.mcc), str(self.mnc), str(self.lac), str(self.cell), p)
            if imsi2:
                self.pfields(str(n), tmsi1, tmsi2, imsi2, str(self.mcc), str(self.mnc), str(self.lac), str(self.cell), p)

        if not imsi1 and not imsi2:
            # Register IMSI as seen if a TMSI believed to
            # belong to the IMSI is seen.
            if self.tmsis and tmsi1 and tmsi1 in self.tmsis and "" != self.tmsis[tmsi1]:
                self.imsi_seen(self.tmsis[tmsi1], arfcn)
            if self.show_all_tmsi:
                do_print = False
                if tmsi1 and tmsi1 not in self.tmsis:
                    do_print = True
                    self.tmsis[tmsi1] = ""
                if tmsi1 and tmsi1 not in self.tmsis:
                    do_print = True
                    self.tmsis[tmsi2] = ""
                if do_print:
                    self.pfields(str(n), tmsi1, tmsi2, None, str(self.mcc), str(self.mnc), str(self.lac), str(self.cell), p)

    def imsi_seen(self, imsi, arfcn):
        now = datetime.datetime.utcnow().replace(microsecond=0)
        imsi, mcc, mnc = self.decode_imsi(imsi)
        if imsi in self.imsistate:
            self.imsistate[imsi]["lastseen"] = now
        else:
            self.imsistate[imsi] = {
                "firstseen": now,
                "lastseen": now,
                "imsi": imsi,
                "arfcn": arfcn,
            }
        self.imsi_purge_old()

    def imsi_purge_old(self):
        now = datetime.datetime.utcnow().replace(microsecond=0)
        maxage = datetime.timedelta(minutes=self.purgeTimer)
        limit = now - maxage
        remove = [imsi for imsi in self.imsistate if limit > self.imsistate[imsi]["lastseen"]]
        for k in remove:
            del self.imsistate[k]
        # keys = self.imsistate.keys()
        # for imsi in keys:
        # 	if limit > self.imsistate[imsi]["lastseen"]:
        # 		del self.imsistate[imsi]
        # 		keys = self.imsistate.keys()


class gsmtap_hdr(ctypes.BigEndianStructure):
    _pack_ = 1
    # Based on gsmtap_hdr structure in <grgsm/gsmtap.h> from gr-gsm
    _fields_ = [
        ("version", ctypes.c_ubyte),
        ("hdr_len", ctypes.c_ubyte),
        ("type", ctypes.c_ubyte),
        ("timeslot", ctypes.c_ubyte),
        ("arfcn", ctypes.c_uint16),
        ("signal_dbm", ctypes.c_ubyte),
        ("snr_db", ctypes.c_ubyte),
        ("frame_number", ctypes.c_uint32),
        ("sub_type", ctypes.c_ubyte),
        ("antenna_nr", ctypes.c_ubyte),
        ("sub_slot", ctypes.c_ubyte),
        ("res", ctypes.c_ubyte),
    ]

    def __repr__(self):
        return "%s(version=%d, hdr_len=%d, type=%d, timeslot=%d, arfcn=%d, signal_dbm=%d, snr_db=%d, frame_number=%d, sub_type=%d, antenna_nr=%d, sub_slot=%d, res=%d)" % (
            self.__class__, self.version, self.hdr_len, self.type,
            self.timeslot, self.arfcn, self.signal_dbm, self.snr_db,
            self.frame_number, self.sub_type, self.antenna_nr, self.sub_slot,
            self.res,
        )


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

    """
    Dump of a packet from wireshark

    /! there are an offset of 0x2a
    0x12 (from the code) + 0x2a (offset) == 0x3c (in documentation's dump)

            0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
    0010   00 43 9a 6b 40 00 40 11 a2 3c 7f 00 00 01 7f 00
    0020   00 01 ed d1 12 79 00 2f fe 42 02 04 01 00 00 00
    0030   cc 00 00 07 9b 2c 01 00 00 00 49 06 1b 61 9d 02
    0040   f8 02 01 9c c8 03 1e 53 a5 07 79 00 00 80 01 40
    0050   db

    Channel Type: BCCH (1)
                            6
    0030                     01

    0x36 - 0x2a = position p[0x0c]


    Message Type: System Information Type 3
                                                c
    0030                                       1b

    0x3c - 0x2a = position p[0x12]

    Cell CI: 0x619d (24989)
                                                d  e
    0030                                          61 9d

    0x3d - 0x2a = position p[0x13]
    0x3e - 0x2a = position p[0x14]

    Location Area Identification (LAI) - 208/20/412
    Mobile Country Code (MCC): France (208)	0x02f8
    Mobile Network Code (MNC): Bouygues Telecom (20) 0xf802
    Location Area Code (LAC): 0x019c (412)
            0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    0030                                                02
    0040   f8 02 01 9c
    """
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
    gsm = gsmtap_hdr.from_buffer_copy(udpdata)

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

                t.register_imsi(gsm.arfcn, imsi1, imsi2, tmsi1, tmsi2, p)

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
                t.register_imsi(gsm.arfcn, imsi1, imsi2, tmsi1, tmsi2, p)

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

                t.register_imsi(gsm.arfcn, imsi1, imsi2, tmsi1, tmsi2, p)

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
                t.register_imsi(gsm.arfcn, imsi1, imsi2, tmsi1, tmsi2, p)


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
    imsitracker = tracker()
    parser = OptionParser(usage="%prog: [options]")
    parser.add_option("-a", "--alltmsi", action="store_true", dest="show_all_tmsi", help="Show TMSI who haven't got IMSI (default  : false)")
    parser.add_option("-i", "--iface", dest="iface", default="lo", help="Interface (default : lo)")
    parser.add_option("-m", "--imsi", dest="imsi", default="", type="string", help='IMSI to track (default : None, Example: 123456789101112 or "123 45 6789101112")')
    parser.add_option("-p", "--port", dest="port", default="4729", type="int", help="Port (default : 4729)")
    parser.add_option("-s", "--sniff", action="store_true", dest="sniff", help="sniff on interface instead of listening on port (require root/suid access)")
    parser.add_option("-w", "--sqlite", dest="sqlite", default=None, type="string", help="Save observed IMSI values to specified SQLite file")
    parser.add_option("-t", "--txt", dest="txt", default=None, type="string", help="Save observed IMSI values to specified TXT file")
    parser.add_option("-z", "--mysql", action="store_true", dest="mysql", help="Save observed IMSI values to specified MYSQL DB (copy .env.dist to .env and edit it)")
    (options, args) = parser.parse_args()

    if options.sqlite:
        imsitracker.sqlite_file(options.sqlite)

    if options.txt:
        imsitracker.text_file(options.txt)

    if options.mysql:
        imsitracker.mysql_file()

    imsitracker.show_all_tmsi = options.show_all_tmsi
    imsi_to_track = ""
    if options.imsi:
        imsi = "9" + options.imsi.replace(" ", "")
        imsi_to_track_len = len(imsi)
        if imsi_to_track_len % 2 == 0 and imsi_to_track_len > 0 and imsi_to_track_len < 17:
            for i in range(0, imsi_to_track_len - 1, 2):
                imsi_to_track += chr(int(imsi[i + 1]) * 16 + int(imsi[i]))
            imsi_to_track_len = len(imsi_to_track)
        else:
            print("Wrong size for the IMSI to track!")
            print("Valid sizes :")
            print("123456789101112")
            print("1234567891011")
            print("12345678910")
            print("123456789")
            print("1234567")
            print("12345")
            print("123")
            exit(1)
    imsitracker.track_this_imsi(imsi_to_track)
    if options.sniff:
        from scapy.all import sniff, UDP
        imsitracker.header()
        sniff(iface=options.iface, filter="port {} and not icmp and udp".format(options.port), prn=find_imsi_from_pkt, store=0)
    else:
        imsitracker.header()
        udpserver(port=options.port, prn=find_imsi)
