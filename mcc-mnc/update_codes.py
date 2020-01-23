#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Oros
# 2020-01-23
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

try:
	# For Python 3.0 and later
	from urllib.request import urlopen
	pythonVersion="3"
except ImportError:
	# Fall back to Python 2's urllib2
	from urllib2 import urlopen
	pythonVersion="2"
import json
import io

wikipediaURLs = [
	'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_2xx_(Europe)',
	'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_3xx_(North_America)',
	'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_4xx_(Asia)',
	'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_5xx_(Oceania)',
	'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_6xx_(Africa)',
	'https://en.wikipedia.org/wiki/Mobile_Network_Codes_in_ITU_region_7xx_(South_America)'
]
mcc_codes={}
for url in wikipediaURLs:
	webpage = urlopen(url)
	soup = BeautifulSoup(webpage,'html.parser')
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
			h4=t.find_previous_sibling("h4")
			if not h4 or ' - ' not in h4.text or '[edit]' not in h4.text:
				continue
			h4=h4.text.split(' - ')
			country_name=h4[0]
			country_code=h4[1][:-6] # rm '[edit]'

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
					mcc_codes[MCC]={}

				mcc_codes[MCC][MNC] = [Brand, Operator, country_name, country_code]
		except Exception:
			pass

if mcc_codes:
	with io.open('mcc_codes.json', 'w', encoding='utf8') as outfile:
		if pythonVersion == "2":
			outfile.write(json.dumps(mcc_codes, ensure_ascii=False, encoding="utf-8"))
		else:
			outfile.write(json.dumps(mcc_codes, ensure_ascii=False))
