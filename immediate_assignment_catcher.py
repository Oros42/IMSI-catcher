#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Oros
# 2016/10/06
# License : CC0 1.0 Universal

"""
Display SDCCH, Subchannel, Timeslot, HoppingChannel, ARFCN
"""
from scapy.all import sniff
from optparse import OptionParser

def find_assignment(x):
	"""

	0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
	0010   00 43 b1 be 40 00 40 11 8a e9 7f 00 00 01 7f 00
	0020   00 01 b9 11 12 79 00 2f fe 42 02 04 01 00 00 00
	0030   e6 00 00 08 d4 7a 02 00 06 00 2d 06 3f 10 0e 03
	0040   df 7b a3 71 01 00 ce 01 81 59 d7 2b 2b 2b 2b 2b
	0050   2b

	Dedicated mode or TBF
	0000   10
		0001 .... = Dedicated mode or TBF: This message assigns an uplink TBF or is the second message of two in a two-message assignment of an uplink or downlink TBF (1)
	Packet Channel Description
	0000   0e 03 df
		0000 1... = Channel Type: 1
		.... .110 = Timeslot: 6
		000. .... = Training Sequence: 0
		.... .0.. = Spare: 0x00
		.... ..11  1101 1111 = Single channel ARFCN: 991



	Dedicated mode or TBF
	0000   30
		0011 .... = Dedicated mode or TBF: This message assigns a downlink TBF to the mobile station identified in the IA Rest Octets IE (3)



	GSMTAP	81	(CCCH) (RR) Immediate Assignment 
	0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
	0010   00 43 07 02 40 00 40 11 35 a6 7f 00 00 01 7f 00
	0020   00 01 b7 29 12 79 00 2f fe 42 02 04 01 00 00 00
	0030   e6 00 00 16 ab ce 02 00 07 00 2d 06 3f 03 41 c0
	0040   09 00 03 b1 01 00 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b
	0050   2b

	
	0x3e = 0x41
	0100 0... = SDCCH/8 + SACCH/C8 or CBCH (SDCCH/8): 8
	Subchannel: 0
	.... .001 = Timeslot: 1

	0x3f = 0xc0
	110. .... = Training Sequence: 6
	...0 .... = Hopping Channel: No
	..00 .... = Spare: 0x00

	0x40 = 0x09
	Single channel ARFCN: 9


			0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f

	0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
	0010   00 43 c8 7f 40 00 40 11 74 28 7f 00 00 01 7f 00
	0020   00 01 9c c8 12 79 00 2f fe 42 02 04 01 00 00 00
	0030   e4 00 00 09 0a e7 02 00 08 00 2d 06 3f 00 41 03
	0040   df 92 f4 2a 01 00 2b 2b 2b 2b 2b 2b 2b 2b 2b 2b
	0050   2b

	Dedicated mode or TBF
	0000   00
		0000 .... = Dedicated mode or TBF: This message assigns a dedicated mode resource (0)
	Channel Description
	0000   41 03 df
		0100 0... = SDCCH/8 + SACCH/C8 or CBCH (SDCCH/8): 8
		Subchannel: 0
		.... .001 = Timeslot: 1
		000. .... = Training Sequence: 0
		...0 .... = Hopping Channel: No
		..00 .... = Spare: 0x00
		Single channel ARFCN: 991

	79
	0111 1... = SDCCH/8 + SACCH/C8 or CBCH (SDCCH/8): 15
	Subchannel: 7
	.... .001 = Timeslot: 1


	ARFCN calcul :
	https://en.wikipedia.org/wiki/ARFCN
	http://www.telecomabc.com/a/arfcn.html
	http://niviuk.free.fr/gsm_band.php

	"""
	p=str(x)
	if ord(p[0x36]) != 0x1: # Channel Type != BCCH (0)
		if ord(p[0x3c]) == 0x3f: # Message Type: Immediate Assignment
			if ord(p[0x3d]) >> 4 == 0: # 0000 .... = Dedicated mode or TBF: This message assigns a dedicated mode resource (0)
				sdcch=ord(p[0x3e]) >> 3 # 0100 0... = SDCCH/8 + SACCH/C8 or CBCH (SDCCH/8): 8
				subchannel=ord(p[0x3e])
				timeslot=ord(p[0x3e]) & 0x07 # .... .001 = Timeslot: 1
				hopping_channel="yes" if (ord(p[0x3f]) >> 4) & 1 == 1 else "no" # ...0 .... = Hopping Channel: No
				arfcn=(ord(p[0x3f]) & 0x03)*256 + ord(p[0x40]) # .... ..11  1101 1111 = Single channel ARFCN: 991
				print("{}\t; {}\t\t; {}\t\t; {}\t\t\t; {}".format(sdcch, subchannel, timeslot, hopping_channel, arfcn))
			else:
				# Dedicated mode or TBF: This message assigns an uplink TBF or is the second message of two in a two-message assignment of an uplink or downlink TBF (1)
				sdcch="-"
				subchannel="-"
				timeslot=ord(p[0x3e]) & 0x07 # .... .001 = Timeslot: 1
				hopping_channel="-"
				arfcn=(ord(p[0x3f]) & 0x03)*256 + ord(p[0x40]) # .... ..11  1101 1111 = Single channel ARFCN: 991
				print("{}\t; {}\t\t; {}\t\t; {}\t\t\t; {}".format(sdcch, subchannel, timeslot, hopping_channel, arfcn))
				pass

			
parser = OptionParser(usage="%prog: [options]")
parser.add_option("-i", "--iface", dest="iface", default="lo", help="Interface (default : lo)")
parser.add_option("-p", "--port", dest="port", default="4729", type="int", help="Port (default : 4729)")
(options, args) = parser.parse_args()

print("SDCCH\t; Subchannel\t; Timeslot\t; HoppingChannel\t; ARFCN")
sniff(iface=options.iface, filter="port {} and not icmp and udp".format(options.port), prn=find_assignment, store=0)