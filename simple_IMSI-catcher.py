#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Oros
# Contributors : puyoulu, 1kali2kali
# 2017/08/01
# License : CC0 1.0 Universal

"""
This program shows you IMSI numbers of cellphones around you.


/!\ This program was made to understand how GSM network work. Not for bad hacking !


What you need :
1 PC
1 USB DVB-T key (RTL2832U) with antenna (less than 15$) or a OsmocomBB phone or HackRf


Setup :

sudo apt install python-numpy python-scipy python-scapy

sudo add-apt-repository -y ppa:ptrkrysik/gr-gsm
sudo apt update
sudo apt install gr-gsm

If gr-gsm failled to setup. Try this setup : https://github.com/ptrkrysik/gr-gsm/wiki/Installation

Run :

# Open 2 terminals.
# In terminal 1
sudo python simple_IMSI-catcher.py

# In terminal 2
airprobe_rtlsdr.py
# Now, change the frequency and stop it when you have output like :
# 15 06 21 00 01 f0 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b
# 25 06 21 00 05 f4 f8 68 03 26 23 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b
# 49 06 1b 95 cc 02 f8 02 01 9c c8 03 1e 57 a5 01 79 00 00 1c 13 2b 2b
# ...
#
# Now, watch terminal 1 and wait. IMSI numbers should appear :-)
# If nothing appears after 1 min, change the frequency.
#
# Doc : https://fr.wikipedia.org/wiki/Global_System_for_Mobile_Communications
# Example of frequency : 9.288e+08 Bouygues

# You can watch GSM packet with
sudo wireshark -k -Y '!icmp && gsmtap' -i lo


Links :

Setup of Gr-Gsm : http://blog.nikseetharaman.com/gsm-network-characterization-using-software-defined-radio/
Frequency : https://fr.wikipedia.org/wiki/Global_System_for_Mobile_Communications
Scapy : http://secdev.org/projects/scapy/doc/usage.html
IMSI : https://fr.wikipedia.org/wiki/IMSI
Realtek RTL2832U : http://doc.ubuntu-fr.org/rtl2832u and http://doc.ubuntu-fr.org/rtl-sdr
"""

import ctypes
from scapy.all import sniff, UDP
import json
from optparse import OptionParser

imsitracker = None

class tracker:
        # phones
        imsis=[] # [IMSI,...]
        tmsis={} # {TMSI:IMSI,...}
        nb_IMSI=0 # count the number of IMSI

        mcc=""
        mnc=""
        lac=""
        cell=""
        country=""
        brand=""
        operator=""
        
        show_all_tmsi = False
        mcc_codes = None

        def __init__(self):
                self.load_mcc_codes()
                self.track_this_imsi("")

        def track_this_imsi(self, imsi_to_track):
                self.imsi_to_track = imsi_to_track
                self.imsi_to_track_len=len(imsi_to_track)

        # return something like '0xd9605460'
        def str_tmsi(self, tmsi):
                if tmsi != "":
                        new_tmsi="0x"
                        for a in tmsi:
                                c=hex(ord(a))
                                if len(c)==4:
                                        new_tmsi+=str(c[2])+str(c[3])
                                else:
                                        new_tmsi+="0"+str(c[2])
                        return new_tmsi
                else:
                        return ""

        def decode_imsi(self, imsi):
                new_imsi=''
                for a in imsi:
                        c=hex(ord(a))
                        if len(c)==4:
                                new_imsi+=str(c[3])+str(c[2])
                        else:
                                new_imsi+=str(c[2])+"0"

                mcc=new_imsi[1:4]
                mnc=new_imsi[4:6]
                return new_imsi, mcc, mnc

        # return something like
        # '208 20 1752XXXXXX', 'France', 'Bouygues', 'Bouygues Telecom'
        def str_imsi(self, imsi, p=""):
                new_imsi, mcc, mnc = self.decode_imsi(imsi)
                country=""
                brand=""
                operator=""
                if mcc in self.mcc_codes:
                        if mnc in self.mcc_codes[mcc]['MNC']:
                                country=self.mcc_codes[mcc]['c'][0]
                                brand=self.mcc_codes[mcc]['MNC'][mnc][0]
                                operator=self.mcc_codes[mcc]['MNC'][mnc][1]
                                new_imsi=mcc+" "+mnc+" "+new_imsi[6:]
                        elif mnc+new_imsi[6:7] in self.mcc_codes[mcc]['MNC']:
                                mnc+=new_imsi[6:7]
                                country=self.mcc_codes[mcc]['c'][0]
                                brand=self.mcc_codes[mcc]['MNC'][mnc][0]
                                operator=self.mcc_codes[mcc]['MNC'][mnc][1]
                                new_imsi=mcc+" "+mnc+" "+new_imsi[7:]
                        else:
                                country=self.mcc_codes[mcc]['c'][0]
                                brand="Unknown MNC {}".format(mnc)
                                operator="Unknown MNC {}".format(mnc)
                                new_imsi=mcc+" "+mnc+" "+new_imsi[6:]

                try:
                        return new_imsi, country.encode('utf-8'), brand.encode('utf-8'), operator.encode('utf-8')
                except:
                        m=""
                        print("Error", p, new_imsi, country, brand, operator)
                return "", "", "", ""

        def load_mcc_codes(self):
                # mcc codes form https://en.wikipedia.org/wiki/Mobile_Network_Code
                with open('mcc-mnc/mcc_codes.json', 'r') as file:
                        self.mcc_codes = json.load(file)

        def current_cell(self, mcc, mnc, lac, cell):
                brand=""
                operator=""
                countr = ""
                if mcc in self.mcc_codes:
                        if mnc in self.mcc_codes[mcc]['MNC']:
                                country=self.mcc_codes[mcc]['c'][0]
                                brand=self.mcc_codes[mcc]['MNC'][mnc][0]
                                operator=self.mcc_codes[mcc]['MNC'][mnc][1]
                        else:
                                country=self.mcc_codes[mcc]['c'][0]
                                brand="Unknown MNC {}".format(mnc)
                                operator="Unknown MNC {}".format(mnc)
                else:
                        country="Unknown MCC {}".format(mcc)
                        brand="Unknown MNC {}".format(mnc)
                        operator="Unknown MNC {}".format(mnc)
                self.mcc=str(mcc)
                self.mnc=str(mnc)
                self.lac=str(lac)
                self.cell=str(cell)
                self.country=country.encode('utf-8')
                self.brand=brand.encode('utf-8')
                self.operator= operator.encode('utf-8')

        def pfields(self, n, tmsi1, tmsi2, imsi, mcc, mnc, lac, cell, p=None):
                if imsi:
                        imsi, imsicountry, imsibrand, imsioperator = self.str_imsi(imsi, p)
                
                print("{:7s} ; {:10s} ; {:10s} ; {:17s} ; {:12s} ; {:10s} ; {:21s} ; {:4s} ; {:5s} ; {:6s} ; {:6s}".format(str(n), tmsi1, tmsi2, imsi, imsibrand, imsicountry, imsioperator, str(mcc), str(mnc), str(lac), str(cell)))

        def header(self):
                print("{:7s} ; {:10s} ; {:10s} ; {:17s} ; {:12s} ; {:10s} ; {:21s} ; {:4s} ; {:5s} ; {:6s} ; {:6s}".format("Nb IMSI", "TMSI-1", "TMSI-2", "IMSI", "country", "brand", "operator", "MCC", "MNC", "LAC", "CellId"))

        # print "Nb IMSI", "TMSI-1", "TMSI-2", "IMSI", "country", "brand", "operator", "MCC", "MNC", "LAC", "CellId"
        def register_imsi(self, imsi1="", imsi2="", tmsi1="", tmsi2="", p=""):
                do_print=False
                n=''
                if imsi1 and (not imsi_to_track or imsi1[:imsi_to_track_len] == imsi_to_track):
                        if imsi1 not in self.imsis:
                                # new IMSI
                                do_print=True
                                self.imsis.append(imsi1)
                                self.nb_IMSI+=1
                                n=self.nb_IMSI
                        if tmsi1 and (tmsi1 not in self.tmsis or self.tmsis[tmsi1] != imsi1):
                                # new TMSI to an ISMI
                                do_print=True
                                self.tmsis[tmsi1]=imsi1
                        if tmsi2 and (tmsi2 not in self.tmsis or self.tmsis[tmsi2] != imsi1):
                                # new TMSI to an ISMI
                                do_print=True
                                self.tmsis[tmsi2]=imsi1		

                if imsi2 and (not imsi_to_track or imsi2[:imsi_to_track_len] == imsi_to_track):
                        if imsi2 not in self.imsis:
                                # new IMSI
                                do_print=True
                                self.imsis.append(imsi2)
                                self.nb_IMSI+=1
                                n=self.nb_IMSI
                        if tmsi1 and (tmsi1 not in self.tmsis or self.tmsis[tmsi1] != imsi2):
                                # new TMSI to an ISMI
                                do_print=True
                                self.tmsis[tmsi1]=imsi2
                        if tmsi2 and (tmsi2 not in self.tmsis or self.tmsis[tmsi2] != imsi2):
                                # new TMSI to an ISMI
                                do_print=True
                                self.tmsis[tmsi2]=imsi2

                if not imsi1 and not imsi2 and tmsi1 and tmsi2:
                        if tmsi2 in self.tmsis:
                                # switch the TMSI
                                do_print=True
                                imsi1=self.tmsis[tmsi2]
                                self.tmsis[tmsi1]=imsi1
                                del self.tmsis[tmsi2]

                if do_print:
                        if imsi1:
                                self.pfields(str(n), self.str_tmsi(tmsi1), self.str_tmsi(tmsi2), imsi1, str(self.mcc), str(self.mnc), str(self.lac), str(self.cell), p)
                        if imsi2:
                                self.pfields(str(n), self.str_tmsi(tmsi1), self.str_tmsi(tmsi2), imsi2, str(self.mcc), str(self.mnc), str(self.lac), str(self.cell), p)

                if not imsi1 and not imsi2 and self.show_all_tmsi:
                        do_print=False
                        if tmsi1 and tmsi1 not in self.tmsis:
                                do_print=True
                                self.tmsis[tmsi1]=""
                        if tmsi1 and tmsi1 not in self.tmsis:
                                do_print=True
                                self.tmsis[tmsi2]=""
                        if do_print:
                                self.pfields(str(n), self.str_tmsi(tmsi1), self.str_tmsi(tmsi2), None, str(self.mcc), str(self.mnc), str(self.lac), str(self.cell), p)

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
def find_cell(gsm, x, t = None):
	# find_cell() update all following variables
	global mcc
	global mnc
	global lac
	global cell
	global country
	global brand
	global operator

	"""
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

	Message Type: System Information Type 3
		                                        c
	0030                                       1b

	Cell CI: 0x619d (24989)
		                                           d  e
	0030                                          61 9d

	Location Area Identification (LAI) - 208/20/412
	Mobile Country Code (MCC): France (208)	0x02f8
	Mobile Network Code (MNC): Bouygues Telecom (20) 0xf802
	Location Area Code (LAC): 0x019c (412)
			0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
	0030                                                02 
	0040   f8 02 01 9c
	"""
	if gsm.sub_type == 0x01: # Channel Type == BCCH (0)
		p=str(x)
		if ord(p[0x3c]) == 0x1b: # Message Type: System Information Type 3
			# FIXME
			m=hex(ord(p[0x3f]))
			if len(m)<4:
				mcc=m[2]+'0'
			else:
				mcc=m[3]+m[2]
			mcc+=str(ord(p[0x40]) & 0x0f)

			# FIXME not works with mnc like 005 or 490
			m=hex(ord(p[0x41]))
			if len(m)<4:
				mnc=m[2]+'0'
			else:
				mnc=m[3]+m[2]

			lac=ord(p[0x42])*256+ord(p[0x43])
			cell=ord(p[0x3d])*256+ord(p[0x3e])
                        t.current_cell(mcc, mnc, lac, cell)

def find_imsi(x, t=None):
	if t is None:
		t = imsitracker

	# Create object representing gsmtap header in UDP payload
	udpdata = str(x[UDP].payload)
	gsm = gsmtap_hdr.from_buffer_copy(udpdata)
	#print gsm

	if gsm.sub_type == 0x1: # Channel Type == BCCH (0)
		# Update global cell info if found in package
		# FIXME : when you change the frequency, this informations is
		# not immediately updated.  So you could have wrong values when
		# printing IMSI :-/
		find_cell(gsm, x, t=t)
	else: # Channel Type != BCCH (0)
		p=str(x)
		tmsi1=""
		tmsi2=""
		imsi1=""
		imsi2=""
		if ord(p[0x3c]) == 0x21: # Message Type: Paging Request Type 1
			if ord(p[0x3e]) == 0x08 and (ord(p[0x3f]) & 0x1) == 0x1: # Channel 1: TCH/F (Full rate) (2)
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
				imsi1=p[0x3f:][:8]
				# ord(p[0x3a]) == 0x59 = l2 pseudo length value: 22
				if ord(p[0x3a]) == 0x59 and ord(p[0x48]) == 0x08 and (ord(p[0x49]) & 0x1) == 0x1: # Channel 2: TCH/F (Full rate) (2)
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
					imsi2=p[0x49:][:8]
				elif ord(p[0x3a]) == 0x59 and ord(p[0x48]) == 0x08 and (ord(p[0x49]) & 0x1) == 0x1: # Channel 2: TCH/F (Full rate) (2)
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
					tmsi1=p[0x4a:][:4]

				t.register_imsi(imsi1, imsi2, tmsi1, tmsi2, p)

			elif ord(p[0x45]) == 0x08 and (ord(p[0x46]) & 0x1) == 0x1: # Channel 2: TCH/F (Full rate) (2)
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
				tmsi1=p[0x40:][:4]
				imsi2=p[0x46:][:8]
				t.register_imsi(imsi1, imsi2, tmsi1, tmsi2, p)

			elif ord(p[0x3e]) == 0x05 and (ord(p[0x3f]) & 0x07) == 4: # Mobile Identity - Mobile Identity 1 - TMSI/P-TMSI 
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
				tmsi1=p[0x40:][:4]
				if ord(p[0x45]) == 0x05 and (ord(p[0x46]) & 0x07) == 4: # Mobile Identity - Mobile Identity 2 - TMSI/P-TMSI 
					tmsi2=p[0x47:][:4]
				else:
					tmsi2=""

				t.register_imsi(imsi1, imsi2, tmsi1, tmsi2, p)

		elif ord(p[0x3c]) == 0x22: # Message Type: Paging Request Type 2
			if ord(p[0x47]) == 0x08 and (ord(p[0x48]) & 0x1) == 0x1: # Mobile Identity 3 Type: IMSI (1)
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
				tmsi1=p[0x3e:][:4]
				tmsi2=p[0x42:][:4]
				imsi2=p[0x48:][:8]
				t.register_imsi(imsi1, imsi2, tmsi1, tmsi2, p)


if __name__ == '__main__':
	imsitracker = tracker()
	parser = OptionParser(usage="%prog: [options]")
	parser.add_option("-a", "--alltmsi", action="store_true", dest="show_all_tmsi", help="Show TMSI who haven't got IMSI (default  : false)")
	parser.add_option("-i", "--iface", dest="iface", default="lo", help="Interface (default : lo)")
	parser.add_option("-m", "--imsi", dest="imsi", default="", type="string", help='IMSI to track (default : None, Example: 123456789101112 or "123 45 6789101112")')
	parser.add_option("-p", "--port", dest="port", default="4729", type="int", help="Port (default : 4729)")
	(options, args) = parser.parse_args()

	imsitracker.show_all_tmsi=options.show_all_tmsi
	imsi_to_track=""
	if options.imsi:
		imsi="9"+options.imsi.replace(" ", "")
		if imsi_to_track_len%2 == 0 and imsi_to_track_len > 0 and imsi_to_track_len <17:
			for i in range(0, imsi_to_track_len-1, 2):
				imsi_to_track+=chr(int(imsi[i+1])*16+int(imsi[i]))
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
	imsitracker.header()
	sniff(iface=options.iface, filter="port {} and not icmp and udp".format(options.port), prn=find_imsi, store=0)
