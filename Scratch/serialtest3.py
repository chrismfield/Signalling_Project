import serial
import json
from struct import *

def cmd1(addr):
        ser = serial.Serial('COM6', 19200, timeout=2)
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 1 # function code
        #        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(5)
        ser.close()
#        print("Start:",s[0],"\n","Address:",s[1],"\n","Function:",s[2],"\n","Upcount:",s[3],"\n","Downcount:",s[4])
        return s[3],s[4]

def cmd2(addr):
        ser = serial.Serial('COM6', 19200, timeout=2)
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 2 # function code
#        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(5)
        ser.close()
        print("Start:",s[0],"\n","Address:",s[1],"\n","Function:",s[2],"\n","Upcount:",s[3],"\n","Downcount:",s[4])
        return s[3],s[4]

def cmd99():
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 99 # function code
#        o[3] = crc # crc or lrc?
        ser.write(o)
        d = ser.readline().decode("ascii")
        print(d)
        list(d)
        ser.close()
        return

def cmd98():
        o = bytearray(12)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 98 # function code
        o[3:12] = s[3:12]
#        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(12)
        print(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11])
        ser.close()
        return        

def cmd97():
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 97 # function code
#        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(12)
        print(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11])
        ser.close()
        return

#cmdentry()
while False:
#        ser = serial.Serial('COM1', 19200, timeout=2)
        cmd = int(input("Please enter an command - Get(1), Clear(2) or Diag(99): "))
        if cmd == 1:      
                cmd1(addr)
        if cmd == 2:
                cmd2(addr)
        if cmd == 99:      # Read diagnostics - ASCII text sent
                cmd99()
        if cmd == 98:       # Write Parameters
                cmd98()
        if cmd == 97:       # Read Parameters
                cmd97()
