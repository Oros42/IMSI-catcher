#!/usr/bin/python
# -*- coding: utf-8 -*-
# Author: Oros
# 2016/09/27
# License : CC0 1.0 Universal

# This scipt update mcc_codes.json from this page https://en.wikipedia.org/wiki/Mobile_Network_Code

# setup :
# sudo apt-get install python-bs4
# 	https://www.crummy.com/software/BeautifulSoup/bs4/doc/
# run :
# python update_codes.py

try:
	from bs4 import BeautifulSoup
except ImportError:
	print("Need BeautifulSoup.\nsudo apt-get install python-bs4")
	import sys
	sys.exit()

import urllib2
import json

webpage = urllib2.urlopen('https://en.wikipedia.org/wiki/Mobile_Network_Code')
soup = BeautifulSoup(webpage,'html.parser')
mcc_codes={}
"""
mcc_codes={
	...
	'208':{ # MCC
		'c':['France', 'FR'],
		'MNC':{
			# 'MNC':[Brand, Operator],
			'01':['Orange', 'Orange S.A.'],
			'02':['Orange', 'Orange S.A.'],
			'03':['MobiquiThings', 'MobiquiThings'],
			...
		}
	},
	...
}
"""
for t in soup.find_all("table", class_="wikitable"):
	try:
		if not 'MCC' in t.text:
			continue
		h3=t.find_previous_sibling("h3")
		if not h3 or ' - ' not in h3.text or '[edit]' not in h3.text:
			continue
		h3=h3.text.split(' - ')
		country_name=h3[0]
		country_code=h3[1][:-6] # rm '[edit]'

		for tr in t.find_all('tr'):
			td=tr.find_all('td')
			if not td:
				continue
			MCC=td[0].text
			if not MCC:
				continue
			MNC=td[1].text
			Brand=td[2].text
			Operator=td[3].text
			if MCC not in mcc_codes:
				mcc_codes[MCC]={'c':[country_name, country_code], 'MNC':{}}
			mcc_codes[MCC]['MNC'][MNC]=[Brand, Operator]
	except Exception:
		pass

if mcc_codes:
	with open('mcc_codes.json', 'w') as outfile:
		json.dump(mcc_codes, outfile)
