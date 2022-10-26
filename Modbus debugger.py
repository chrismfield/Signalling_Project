import minimalmodbus
import serial.tools.list_ports
from Comselector import Comselector

rs485port = Comselector()
print(rs485port)

axlecounter = minimalmodbus.Instrument(rs485port,1) #update comport and slave address
axlecounter.debug = True
print(axlecounter.read_register(0, 10)) # Load 1 register from location 289
