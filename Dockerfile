FROM ubuntu:bionic

MAINTAINER Dmitry Abakumov, a.k.a 0MazaHacka0 <killerinshadow2@gmail.com>

# Update container
RUN apt-get update

# GR-GSM
RUN export TZ=America/New_York && export DEBIAN_FRONTEND=noninteractive && apt-get install -y  gnuradio gnuradio-dev git cmake autoconf libtool pkg-config g++ gcc make libc6 \
libc6-dev libcppunit-1.14-0 libcppunit-dev swig doxygen liblog4cpp5v5 liblog4cpp5-dev python-scipy \
gr-osmosdr libosmocore libosmocore-dev

RUN git clone https://git.osmocom.org/gr-gsm

RUN cd gr-gsm && mkdir build && cd build && cmake .. && make && make install && ldconfig

# IMSI-catcher script
RUN apt-get install -y python-numpy python-scipy python-scapy

ADD . /imsi-catcher/

# Wireshark
RUN export DEBIAN_FRONTEND=noninteractive && apt-get install -y wireshark tshark
