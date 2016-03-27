#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Oros
# 2015/06/03
# License : CC0 1.0 Universal

"""
This program shows you IMSI numbers of cellphones around you.


/!\ This program was made to understand how GSM network work. Not for bad hacking !


What you need :
1 PC with more than 3Go of RAM to compile gr-gsm
1 USB DVB-T key (RTL2832U) with antenna (less than 15$)


Setup :

cd /tmp
sudo apt-get install git python-scapy python-pip
sudo pip install PyBOMBS
sudo pybombs prefix init /usr/local -a default_prx
sudo pybombs config default_prefix default_prx
sudo pybombs recipes add gr-recipes git+https://github.com/gnuradio/gr-recipes.git
sudo pybombs recipes add gr-etcetera git+https://github.com/gnuradio/gr-etcetera.git
sudo pybombs install gr-gsm
sudo ldconfig

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

imsis=[]

def show_imsi(imsi):
	global imsis
	new_imsi=''
	for a in imsi:
		c=hex(ord(a))
		if len(c)==4:
			new_imsi+=str(c[3])+str(c[2])
		else:
			new_imsi+=str(c[2])+"0"
	new_imsi=new_imsi[1:4]+" "+new_imsi[4:6]+" "+new_imsi[6:8]+" "+new_imsi[8:]
	if new_imsi not in imsis:
		imsis.append(new_imsi)
		print(new_imsi)

def find_imsi(x):
	p=str(x)
	if p[58:][:2] != '\x01+':
		# if not (CCCH) (SS)
		# GSM CCCH
		l2_pseudo_len=p[58]
		if p[80] != '\x2b' and p[80] != '\x00' and p[80] != '\x4b' and p[80] != '\xc0':
			if l2_pseudo_len=='\x55' and p[71:][:2] == '\x08\x29':
				# if IMSI
				show_imsi(p[72:][:8])
			elif l2_pseudo_len=='\x59' and p[62:][:2] == '\x08\x29':
				# if IMSI
				show_imsi(p[63:][:8])
				if p[72:][:2] == '\x08\x29':
					# if IMSI 2
					show_imsi(p[73:][:8])

sniff(iface="lo", filter="port 4729 and not icmp and udp", prn=find_imsi, store=0)
