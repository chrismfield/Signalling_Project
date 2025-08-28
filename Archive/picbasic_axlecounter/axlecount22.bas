'This is for three sensors, with RS485 Modbus interface
'Revised following first test on track; this version changes trigger logic to look for all three sensors in turn.
'Revised again to eliminate the need for offset and input default sensitivity and hysteresis values derived from datalogging and graphs 
'general set up
disable ' kill BASIC's interrupt handling
DEFINE I2C_SLOW 1
DEFINE OSC 8 ' 8MHz is the fastest internal oscilltor
OSCCON.4 = 1 
OSCCON.5 = 1
OSCCON.6 = 1 ' set up 8MHz as PICBASIC is not doing it properly
Ansel = %00110000 ' A-D converter configure for input on analogue channels 4 and 5
Anselh = 0 ' A-D converter configure for output
TRISC = %11111111 ' set port c as input
TRISB = %11110000 ' set portb as inputs (this is also correct for I2C) Check what is required for serial comms
TRISA = %00000000 ' set porta as output

DEFINE ADC_BITS 10
DEFINE HSER_RCSTA 90h ' Set receive register to receiver enabled
DEFINE HSER_TXSTA 20h ' Set transmit register to transmitter enabled
DEFINE HSER_SPBRG 25 ' Set Baud to 19200
DEFINE HSER_CLROERR 1 ' Automatically clear HSERIN overrun errors
TXSTA.2 = 1 ' Set Baud to 19200
T1CON.0 = 1 ' start timer1
T1CON.4 = 1 ' Timer1 Prescale 8
T1CON.5 = 1 ' Timer1 Prescale 8

ADCON0.7 = 1
ADCON1 = %01100000

Resetcount var byte
Read 40, Resetcount
Resetcount = Resetcount+1
Write 40, Resetcount

HoldingReg VAR word[20] ' Put all of the variables into memory locations offset from HoldingReg[0] IAW "Register Register.xls"
station var HoldingReg[0] 'Address of slave
sensitivity var HoldingReg[1]
hysteresis var HoldingReg[4]
duration var HoldingReg[7]
hallsteady var HoldingReg[10]
upcount var HoldingReg[13]
downcount var Holdingreg[14]
upcount = 0
downcount = 0

InputReg var word[20]
s_upcount var InputReg[1] 'not implemented
s_downcount var InputReg[2] 'not implemented
hall var InputReg[3]
uparm var InputReg[6]
downarm var InputReg[7]
uptrigger1 var bit
downtrigger1 var bit
uptrigger2 var bit
downtrigger2 var bit
waitclear var bit
waitclear = 0
For i = 0 to 20
Inputreg[i] = 0
next i

length var byte
i var byte
swaptemp var byte
Generator var word
Temp var word
CRC var word
crclow var CRC.BYTE0
crchigh var CRC.BYTE1
j var byte
BitVal var bit
bytecount var byte
lengthincCRC var byte
Timer1 var word

low porta.2 'set RS485 transmit pin to recieve/

BufRx VAR BYTE[40] 'Buffer de réception
BufTx VAR BYTE[40] 'Buffer de transmission
timertrig var bit ' bit for monitoring timer reset

EEPROM 2,[7,0,7,0,7,0,5,0,5,0,5,0,2,0,2,0,2,0] 'Default parameters written at programming time. Set Station Address at location 0 manually using MPLAB.
EEPROM 40, [0]

Init:
For i = 0 to 19
BufRx[i]=0 ' clear rx buffer
BufTx[i]=0 ' clear tx buffer
Next i
'read settings for each HED from EEPROM.
for i = 0 to 19
Read i, holdingreg.lowbyte(i)
next i


getsteadystate: ' get steady state values from hall devices
pause 2000
gosub getvalues
For i = 0 to 2
hallsteady[i] = hall[i]
Next i
uparm = 0
downarm = 0
goto main


getvalues:
adcin 4,hall[0]
inputreg.lowbyte(6) = ADRESL
inputreg.lowbyte(7) = ADRESH
adcin 6,hall[1]
inputreg.lowbyte(8) = ADRESL
inputreg.lowbyte(9) = ADRESH
adcin 5,hall[2]
inputreg.lowbyte(10) = ADRESL
inputreg.lowbyte(11) = ADRESH
return

getaxlecount:
if waitclear = 0 then
	if hall[0] < (hallsteady[0] - sensitivity[0]) then ' check first sensor for axle
		if hall[1] > (hallsteady[1] - hysteresis[1]) then	' check last sensor is not already occupied
			uparm = uparm + 1 ' increment uparm if there is an axle on up sensor
			if uparm > duration[0] then
				uptrigger1 = 1
			endif
		endif
	endif
	if uptrigger1 = 1 then
		if hall[2] < (hallsteady[2] - sensitivity[2]) then 'check there is an axle at hall2 mid trigger
			uptrigger2 = 1
		endif
	endif
	if uptrigger2 = 1 then
		if hall[1] < (hallsteady[1] - sensitivity[1]) then ' when an axle counter is seen at final sensor, count the axle and wait until all are clear before doing anything else. 
			upcount = upcount + 1
			uptrigger1 = 0
			uptrigger2 = 0
			uparm = 0
			downarm = 0
			waitclear = 1
		endif
	endif
endif

'same again in opposite direction
if waitclear = 0 then
	if hall[1] < (hallsteady[1] - sensitivity[1]) then ' check first sensor for axle
		if hall[0] > (hallsteady[0] - hysteresis[0]) then	' check last sensor is not already occupied
			downarm = downarm + 1 ' increment downarm if there is an axle on up sensor
			if downarm > duration[1] then
				downtrigger1 = 1
			endif
		endif
	endif
	if downtrigger1 = 1 then
		if hall[2] < (hallsteady[2] - sensitivity[2]) then 'check there is an axle at hall2 mid trigger
				downtrigger2 = 1
		endif
	endif
	if downtrigger2 = 1 then
		if hall[0] < (hallsteady[0] - sensitivity[0]) then ' when an axle counter is seen at final sensor, count the axle and wait until all are clear before doing anything else. 
			downcount = downcount + 1
			downtrigger1 = 0
			downtrigger2 = 0
			uparm = 0
			downarm = 0
			waitclear = 1
		endif
	endif
endif
Return


allsensorsvacant: ' reset all triggers to zero if all no axles detected
if hall[2] > (hallsteady[2] - hysteresis[2]) then 'check if mid sensor has returned to steady state
	if hall[0] > (hallsteady[0] - hysteresis[0]) then
		if hall[1] > (hallsteady[1] - hysteresis[1]) then
			uptrigger1 = 0
			uptrigger2 = 0
			downtrigger1 = 0
			downtrigger2 = 0
			uparm = 0
			downarm = 0
			waitclear = 1
			waitclear = 0
		endif
	endif
endif
return
		

func3: ' read holding registers
bytecount = (BufRx[5] * 2) ' BufRx[5] requests number of values
lengthincCRC =  bytecount + 5 ' number of bytes = address, function, bytecount byte, data x bytecount, plus two for CRC
length = bytecount + 3
BufTx[0] = Station
BufTx[1] = 3
BufTx[2] = bytecount
for i = 0 to (bytecount-1)
BufTx[(i+3)] = HoldingReg.lowbyte((2*BufRx[3])+i) ' this should extract all the bytes from the word variables. Currently we have lowbyte first which is a problem.
next i
for i = 0 to ((bytecount/2)-1)
swaptemp = BufTx[(3+(2*i))]
BufTx[(3+(2*i))] = BufTx[(4+(2*i))]
BufTx[(4+(2*i))] = swaptemp
next i
Gosub crc__16Tx	'create CRC
BufTx[length] = crclow 'lowbyte CRC
BufTx[length+1] = crchigh 'highbyte CRC
high porta.2 'enable transmit
pause 1
'Hserout [STR BufTx\lengthincCRC] ' send register value back (note this has not checked the network is ready. It also happens after broadcast which it should not.)
for i = 0 to lengthincCRC
	Hserout [BufTx[i]]
	gosub docount
	next i
pause 1
low porta.2
Return


func4: ' read input registers
bytecount = (BufRx[5] * 2) ' BufRx[5] requests number of values
lengthincCRC =  bytecount + 5 ' number of bytes = address, function, bytecount byte, data x bytecount, plus two for CRC
length = bytecount + 3
BufTx[0] = Station
BufTx[1] = 4
BufTx[2] = bytecount
for i = 0 to (bytecount - 1)
BufTx[(i+3)] = InputReg.lowbyte((2*BufRx[3])+i) ' this should extract all the bytes from the word variables. Currently we have lowbyte first which is a problem.
next i
for i = 0 to ((bytecount/2)-1) ' have to now swap the byte order
swaptemp = BufTx[(3+(2*i))]
BufTx[(3+(2*i))] = BufTx[(4+(2*i))]
BufTx[(4+(2*i))] = swaptemp
next i
Gosub crc__16Tx	'create CRC
BufTx[length] = CRClow 'lowbyte CRC
BufTx[length+1] = CRChigh 'highbyte CRC
high porta.2
pause 1
Hserout [STR BufTx\lengthincCRC] ' send register value back (note this has not checked the network is ready. It also happens after broadcast which it should not.)
pause 1
low porta.2
Return


func6: ' write single register
if BufRx[3] < 10 then
	Write ((BufRx[3]*2)), BufRx[5] 'only considers registers uptp 255. But that's fine as there are non higher (ref register register.xls)
	Write ((BufRx[3]*2)+1), BufRx[4]
	for i = 0 to 19
	Read i, holdingreg.lowbyte(i)' read written parameters into current programme variables.
	next i
endif
if BufRx[3] >= 10 then
	holdingreg.lowbyte((BufRx[3]*2)) = BufRx[5]
	holdingreg.lowbyte((BufRx[3]*2)+1) = BufRx[4]
endif
BufTx[0] = Station
BufTx[1] = 6
BufTx[2] = BufRx[2]
BufTx[3] = BufRx[3]
BufTx[4] = holdingreg.lowbyte((2*BufRx[3])+1)
BufTx[5] = holdingreg.lowbyte(2*BufRx[3])
length = 6
lengthincCRC = 8
Gosub crc__16Tx	'create CRC
BufTx[length] = CRClow 'lowbyte CRC
BufTx[length+1] = CRChigh 'highbyte CRC
high porta.2
pause 1
'Hserout [STR BufTx\lengthincCRC] ' send register value back (note this has not checked the network is ready. It also happens after broadcast which it should not.)
for i = 0 to lengthincCRC
	Hserout [BufTx[i]]
	gosub docount
	next i
pause 1
low porta.2
Return


read485:
For i = 0 to 39
BufRx[i]=0 ' clear rx buffer
BufTx[i]=0 ' clear tx buffer
Next i
i = 0
hserin 1, getreturn, [BufRx[i]]
TMR1H=0
TMR1L=0	'reset timer as byte has been received 
PIR1.0 = 0 'reset timer overflow flag
gosub docount
if (BufRx[0] = station) AND (timertrig = 1) then
		timertrig = 0	
		for i = 1 to 7
			hserin 1, getreturn, [BufRx[i]] ' read the rest of the frame
			TMR1H=0
			TMR1L=0	'reset timer as byte has been received 
			PIR1.0 = 0
			gosub docount
		next i	
		length = 6 ' all requests are assumed to be 6 bytes plus 2 CRC. Only functions 1-6 are implemented.
		Gosub crc__16Rx
		Gosub docount
		if (BufRx[6]=crclow) AND (BufRx[7]=crchigh) then
			if BufRx[1] = 3 then func3 ' read holding registers
			if BufRx[1] = 4 then func4 ' read input registers
			if BufRx[1] = 6 then func6 ' write holding registers	
		else
		endif	
else
endif
'if BufRx[0] = 0 then' check if it is a broadcast
'	gosub readframe ' if so, read the rest of the frame.
Return


checktimer:
timer1.byte0 = TMR1L
timer1.byte1 = TMR1H
if timer1 > 456 then ' messages start with a silent interval of at least 3.5 character times = 456. Check timing at this baud rate and 8Mhz'
	timertrig = 1
endif
if PIR1.0 = 1 then
	timertrig = 1
endif
return

crc__16Rx:	' Function to calculate CRC16 checksum
CRC = 65535
Generator = 40961
For i = 0 To (length-1)
    CRC = CRC ^ BufRx[i]
    For j = 1 To 8
        BitVal = CRC.0
        If BitVal = 1 Then
           	CRC = Generator ^ (CRC >> 1)
		else
			CRC = CRC >> 1
        EndIf
    Next j
Next i
Return


crc__16Tx:	' Function to calculate CRC16 checksum
CRC = 65535
Generator = 40961
For i = 0 To (length-1)
    CRC = CRC ^ BufTx[i]
    For j = 1 To 8
        BitVal = CRC.0
        If BitVal = 1 Then
           	CRC = Generator ^ (CRC >> 1)
		else
			CRC = CRC >> 1
        EndIf
    Next j
Next i
Return

getreturn: 'to get back to main loop after timeout in Hserout
Return

docount:
gosub getvalues
gosub getaxlecount
gosub allsensorsvacant
gosub checktimer
Return

main:
gosub docount
gosub read485
goto main

