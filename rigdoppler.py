# Autor:
#   Original from K8DP Doug Papay (v0.1)
#
#   Adapted v0.2 by EA4HCF Pedro Cabrera


import ephem
import socket
import sys
import math
import time
import re
from contextlib import contextmanager
from time import gmtime, strftime
from datetime import datetime, timedelta

from configparser import ConfigParser

C = 299792458.

@contextmanager
def socketcontext(*args, **kwargs):
    s = socket.socket(*args, **kwargs)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    yield s
    s.close()

def tx_dopplercalc():
    mysat.compute(myloc)
    doppler = int(I0 + mysat.range_velocity * I0 / C)
    return doppler

def rx_dopplercalc():
    mysat.compute(myloc)
    doppler = int(F0 - mysat.range_velocity * F0 / C)
    return doppler

def MyError():
    print("Failed to find required file!")
    sys.exit()

print("Rigdoppler v0.2")

try:
    with open('config.ini') as f:
        f.close()
        configur = ConfigParser()
        configur.read('config.ini')
except IOError:
    raise MyError()



LATITUDE = configur.get('qth','latitude')
LONGITUDE = configur.get('qth','longitude')
ALTITUDE = configur.getfloat('qth','altitude')
TLEFILE = configur.get('satellite','tle_file')
SATNAMES = configur.get('satellite','amsatnames')
SQFILE = configur.get('satellite','sqffile')
NORAD_ID = configur.get('satellite','norad_id')
F = 0
I = 0
f_cal = configur.getfloat('radio','freq_rx_correction')
i_cal = configur.getfloat('radio','freq_tx_correction')
ADDRESS = configur.get('hamlib','address')
PORT = configur.getint('hamlib','port')

try:
    with open(TLEFILE, 'r') as f:
     data = f.readlines()   
  
    for index, line in enumerate(data):
        if NORAD_ID in line[2:7]:
            break
except IOError:
    raise MyError()

myloc = ephem.Observer()
myloc.lon = LONGITUDE
myloc.lat = LATITUDE
myloc.elevation = ALTITUDE

mysat = ephem.readtle(data[index-1], data[index], data[index+1])
mysatname=""

# EA4HCF: Checking TLE age
day_of_year = datetime.now().timetuple().tm_yday
tleage = int(data[index][20:23])
diff = day_of_year - tleage

if diff > 7:
    print("***  Warning, your TLE file is getting older: {days} days.".format(days=diff))

#   EA4HCF: Let's use PCSat32 translation from NoradID to Sat names, boring but useful for next step.
#   From NORAD_ID identifier, will get the SatName to search satellite frequencies in dopler file in next step.
try:
    with open(SATNAMES, 'r') as g:
        namesdata = g.readlines()  
        
    for line in namesdata:
        if re.search(NORAD_ID, line):
            mysatname=line.split(" ")[4].strip()
except IOError:
    raise MyError()

#   EA4HCF: Now, let's really use PCSat32 dople file .
#   From SatName,  will get the RX and TX frequencies.
try:
    with open(SQFILE, 'r') as h:
        sqfdata = h.readlines()  
        
    for lineb in sqfdata:
        if re.search(mysatname, lineb):
            F = float(lineb.split(",")[1].strip())*1000
            I = float(lineb.split(",")[2].strip())*1000
            F0 = F + f_cal 
            I0 = I + i_cal
            #print("DEBUG:   Satellite {thename}, RX base freq: {rxfreq}, TX base freq: {txfreq}".format(thename=mysatname,rxfreq=F0,txfreq=I0))
            break
except IOError:
    raise MyError()

try:
    with socketcontext(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((ADDRESS, PORT))
        
        print("Connected to Rigctld on {addr}:{port}".format(addr=ADDRESS,port=PORT))
        print("Tracking: {sat_name}".format(sat_name=mysat.name))
        print("Recieve Freqeuncy (F) = {rx_freq}".format(rx_freq=F))
        print("Transmit Frequency (I) = {tx_freq}".format(tx_freq=I))
        print("Frequency Offset = {freq_off}".format(freq_off=f_cal))
        
        #setup radio here
        #turn off satellite mode
        data_to_send = b"W \\0xFE\\0xFE\\0xA2\\0xE2\\0x16\\0x5A\\0x00\\0xFD 14\n"
        s.sendall(data_to_send)
        time.sleep(0.2)
        #turn on scope waterfall
        s.sendall(b"W \\0xFE\\0xFE\\0xA2\\0xE2\\0x1A\\0x05\\0x01\\0x97\\0x01\\0xFD 16\n")
        time.sleep(0.2)
        #show scope during TX
        s.sendall(b"W \\0xFE\\0xFE\\0xA2\\0xE2\\0x1A\\0x05\\0x01\\0x87\\0x01\\0xFD 16\n")
        time.sleep(0.2)
        #set span = 5kHz
        s.sendall(b"W \\0xFE\\0xFE\\0xA2\\0xE2\\0x1A\\0x05\\0x01\\0x87\\0x01\\0xFD 16\n")
        time.sleep(0.2)
   
        #set VFOA to USB-D mode
        s.sendall(b"V VFOA\n")
        s.sendall(b"M PKTUSB 3000\n")
        #set VFOB to SUB-D mode
        s.sendall(b"V VFOB\n")
        s.sendall(b"M PKTUSB 3000\n")
        #return to VFOA
        s.sendall(b"V VFOA\n")

        rx_doppler = F0
        tx_doppler = I0
        step_size = 10.

        while True:
            date_val = strftime('%Y/%m/%d %H:%M:%S', gmtime())
            myloc.date = ephem.Date(date_val)
            new_rx_doppler = round(rx_dopplercalc(),-1)
            if new_rx_doppler != rx_doppler:
                rx_doppler = new_rx_doppler
#                print(date_val)
#                print(F)
#                print(f_cal)
                F_string = "F {rx_doppler:.0f}\n".format(rx_doppler=rx_doppler)    
                s.send(bytes(F_string, 'ascii'))
                time.sleep(0.2)
                print(F_string,end="")
            
            new_tx_doppler = round(tx_dopplercalc(),-1)
            if new_tx_doppler != tx_doppler:
                tx_doppler = new_tx_doppler
                I_string = "I {tx_doppler:.0f}\n".format(tx_doppler=tx_doppler)
                s.send(bytes(I_string, 'ascii'))
                print(I_string,end="")
                time.sleep(0.2)

except socket.error:
    print("Failed to connect to Rigctld on {addr}:{port}".format(addr=ADDRESS,port=PORT))
    sys.exit()
