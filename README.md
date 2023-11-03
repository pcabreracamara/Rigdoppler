# RigDoppler v0.2

Autor: K8DP Doug Papay v0.1 (@K8DP_Doug)  
Adapted v0.2 by EA4HCF Pedro Cabrera (@PCabreraCamara)  
  
RigDoppler is a very simple Python3 script to correct doppler efect in radio satellites using Icom rigs connected to a computer.  
  
## Requeriments:  
    1) Python3  
    2) Python3 ephem module 
       pip3 install ephem
    3) HamLib (https://hamlib.github.io/)  
  
Support files and download links:  

    1) TLE ephemerides file. (Exmple: https://www.pe0sat.vgnet.nl/satellite/tle/)   
    2) AmsatNames.txt (https://www.ea5wa.com/satpc32/archivos-auxiliares-de-satpc32)   
    3) dopler.sqf (https://www.ea5wa.com/satpc32/archivos-auxiliares-de-satpc32)  

  
AmsatNames.txt and dopler.sqf are wide and well known files used by PCSat32 software, so can be reused in the same computer.  

## Basic Configuration:
    1) Edit *config.ini* file and set your coordinates and altitude:
    
        ;rigdoppler configuration file
        [qth]
        ;station location
        latitude = 48.188
        longitude = -5.708
        altitude = 70
  
## Operation:  
    1) Open TCP connection from your computer to Icom rig using HamLib *rigctld* command:
    
      Icom 705: rigctld -m 3085 -r /dev/YOUR_DEVICE -c 0xA4 -s 57600 -T 127.0.0.1

    2) Check *config.ini* file and review all parameters:  
        QTH coordinates and NORAD ID satellite you want to track  
        Correct RX and TX frequencies offsets  
        etc.  
        
    3) Execute RigDoppler: python3 /path/to/rigdoppler.py

## Advanced Configuration:
    1) Support files can be modified in the *config.ini* file:
    
        [satellite]
        ;path to your TLE file
        tle_file = mykepler.txt
        ;path to AmsatNames file
        amsatnames = AmsatNames.txt
        ;path to dopler.sqf file
        sqffile = doppler.sqf
        [hamlib]
        address = localhost
        port = 4532

tle_file must contains ephemerides two line elements to calculate satellite passes over the coordinates in the [qth] section.

sqffile must contains satellites' frequencies (both downlink and uplink), following the same format as the original PCSat32 file.

amsatnames is just an auxiliary file son NORAD_ID satellites identifiers could be correlated with common satellites names used in doppler.sf file. Three columns per each satellite will list NORAD_ID identifier and common satellite name.
