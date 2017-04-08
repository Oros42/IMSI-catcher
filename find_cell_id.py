#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Oros
# 2016/10/07
# License : CC0 1.0 Universal

"""
This program shows informations about the cell tower like MCC, MNC, LAC and CellId 
"""

from scapy.all import sniff
import json
from optparse import OptionParser

def find_cell(x):
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
	p=str(x)
	if ord(p[0x36]) == 0x01: # Channel Type: BCCH (1)
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
			brand=""
			operator=""
			if mcc in mcc_codes:
				if mnc in mcc_codes[mcc]['MNC']:
					country=mcc_codes[mcc]['c'][0]
					brand=mcc_codes[mcc]['MNC'][mnc][0]
					operator=mcc_codes[mcc]['MNC'][mnc][1]
				else:
					country=mcc_codes[mcc]['c'][0]
					brand="Unknown"
					operator=mcc_codes[mcc]['MNC'][mnc][1]
			print("{:5s} ; {:4s} ; {:5s} ; {:6s} ; {} ; {} ; {}".format(str(mcc), str(mnc), str(lac), str(cell), country.encode('utf-8'), brand.encode('utf-8'), operator.encode('utf-8')))

parser = OptionParser(usage="%prog: [options]")
parser.add_option("-p", "--port", dest="port", default="4729", type="int", help="Port (default : 4729)")
parser.add_option("-i", "--iface", dest="iface", default="lo", help="Interface (default : lo)")
(options, args) = parser.parse_args()

# mcc codes form https://en.wikipedia.org/wiki/Mobile_Network_Code
with open('mcc-mnc/mcc_codes.json', 'r') as file:
	mcc_codes = json.load(file)

print("{:5s} ; {:4s} ; {:5s} ; {:6s} ; {} ; {} ; {}".format("MCC", "MNC", "LAC", "CellId", "Country", "Brand", "Operator"))
sniff(iface=options.iface, filter="port {} and not icmp and udp".format(options.port), prn=find_cell, store=0)
