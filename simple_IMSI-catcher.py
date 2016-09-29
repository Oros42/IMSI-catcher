#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Oros
# Contributor : puyoulu
# 2016/09/29
# License : CC0 1.0 Universal

"""
This program shows you IMSI numbers of cellphones around you.


/!\ This program was made to understand how GSM network work. Not for bad hacking !


What you need :
1 PC
1 USB DVB-T key (RTL2832U) with antenna (less than 15$)


Setup :

sudo add-apt-repository -y ppa:ptrkrysik/gr-gsm
sudo apt update
sudo apt install gr-gsm python-numpy python-scipy python-scapy

Run :

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

from scapy.all import sniff
import json

imsis=[]
cpt=1
def show_imsi(imsi, p):
	global imsis
	global cpt
	new_imsi=''
	for a in imsi:
		c=hex(ord(a))
		if len(c)==4:
			new_imsi+=str(c[3])+str(c[2])
		else:
			new_imsi+=str(c[2])+"0"
	
	if new_imsi not in imsis:
		imsis.append(new_imsi)
		mcc=new_imsi[1:4]
		mnc=new_imsi[4:6]
		m=""
		if mcc in mcc_codes:
			if mnc in mcc_codes[mcc]['MNC']:
				# m=" : "+country+", "+brand+" - "+operator
				m=" ; "+mcc_codes[mcc]['c'][0]+" ; "+mcc_codes[mcc]['MNC'][mnc][0]+" ; "+mcc_codes[mcc]['MNC'][mnc][1]
				new_imsi=mcc+" "+mnc+" "+new_imsi[6:]
			elif mnc+"0" in mcc_codes[mcc]['MNC']:
				mnc+="0"
				# m=" : "+country+", "+brand+" - "+operator
				m=" ; "+mcc_codes[mcc]['c'][0]+" ; "+mcc_codes[mcc]['MNC'][mnc][0]+" ; "+mcc_codes[mcc]['MNC'][mnc][1]
				new_imsi=mcc+" "+mnc+" "+new_imsi[7:]
		else:
			print("Error : ",p)
		print(str(cpt)+" ; "+new_imsi+m)
		cpt+=1

def find_imsi(x):
	p=str(x)
	if ord(p[0x36]) == 0x2:
		if ord(p[0x3c]) == 0x21: # Message Type: Paging Request Type 1
			if ord(p[0x3e]) == 0x08 and (ord(p[0x3f]) & 0x1) == 0x1: # Channel 1: TCH/F (Full rate) (2)
				# Mobile Identity 1 Type: IMSI (1)
				"""
				0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
				0010   00 43 1c d4 40 00 40 11 1f d4 7f 00 00 01 7f 00
				0020   00 01 c2 e4 12 79 00 2f fe 42 02 04 01 00 00 00
				0030   c9 00 00 16 21 26 02 00 07 00 31 06 21 00 08 XX
				0040   XX XX XX XX XX XX XX 2b 2b 2b 2b 2b 2b 2b 2b 2b
				0050   2b
				XX XX XX XX XX XX XX XX = IMSI
				"""
				show_imsi(p[0x3f:][:8], p)

				# ord(p[0x3a]) == 0x59 = l2 pseudo length value: 22
				if ord(p[0x3a]) == 0x59 and ord(p[0x48]) == 0x08 and (ord(p[0x49]) & 0x1) == 0x1: # Channel 2: TCH/F (Full rate) (2)
					# Mobile Identity 2 Type: IMSI (1)
					"""
				0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
				0010   00 43 90 95 40 00 40 11 ac 12 7f 00 00 01 7f 00
				0020   00 01 b4 1c 12 79 00 2f fe 42 02 04 01 00 00 00
				0030   c8 00 00 16 51 c6 02 00 08 00 59 06 21 00 08 YY
				0040   YY YY YY YY YY YY YY 17 08 XX XX XX XX XX XX XX
				0050   XX
				YY YY YY YY YY YY YY YY = IMSI 1
				XX XX XX XX XX XX XX XX = IMSI 2
					"""
					show_imsi(p[0x49:][:8], p)

			elif ord(p[0x45]) == 0x08 and (ord(p[0x46]) & 0x1) == 0x1: # Channel 2: TCH/F (Full rate) (2)
				# Mobile Identity 2 Type: IMSI (1)
				"""
				0000   00 00 00 00 00 00 00 00 00 00 00 00 08 00 45 00
				0010   00 43 57 8e 40 00 40 11 e5 19 7f 00 00 01 7f 00
				0020   00 01 99 d4 12 79 00 2f fe 42 02 04 01 00 00 00
				0030   c7 00 00 11 05 99 02 00 03 00 4d 06 21 00 05 f4
				0040   yy yy yy yy 17 08 XX XX XX XX XX XX XX XX 2b 2b
				0050   2b
				yy yy yy yy = TMSI/P-TMSI - Mobile Identity 1
				XX XX XX XX XX XX XX XX = IMSI
				"""
				show_imsi(p[0x46:][:8], p)


		elif ord(p[0x3c]) == 0x22: # Message Type: Paging Request Type 2
			if ord(p[0x47]) == 0x08 and (ord(p[0x48]) & 0x1) == 0x1: # Mobile Identity 3 Type: IMSI (1)
				"""
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
				show_imsi(p[0x48:][:8], p)

# mcc codes form https://en.wikipedia.org/wiki/Mobile_Network_Code
with open('mcc-mnc/mcc_codes.json') as file:    
	mcc_codes = json.load(file)

print("cpt ; IMSI ; country ; brand ; operator")
sniff(iface="lo", filter="port 4729 and not icmp and udp", prn=find_imsi, store=0)
