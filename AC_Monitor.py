import minimalmodbus
import serial.tools.list_ports
import datetime
import time
import logging

try:
    comportlist = [comport.device for comport in serial.tools.list_ports.comports()]
    comport = comportlist[-1]
    #insert logging here
except:
    print("No Com Port Available")
    #insert logging here

def find_modubus_slaves():
    list_of_slaves = []
    for test_address in range(0,20):
        findinst = minimalmodbus.Instrument(comport, test_address)
#        print("Test Address" + str(test_address))
        try:
            test_var = findinst.read_register(0)
            list_of_slaves.append(test_address)
        except:
            pass
    print("Discovered slaves:")
    print(list_of_slaves)
    return list_of_slaves

def AC_read_and_clear(AC_address):
    """Get """
    try:
        axlecounter = minimalmodbus.Instrument(comport, AC_address)  # create axlecounter instrument. Perhaps move this outside this module.
        axlecounter.debug = False
        upcount = axlecounter.read_register(13)  # Load 1 register from location 13 (upcount)
        downcount = axlecounter.read_register(14)
        axlecounter.write_register(13, 0, functioncode=6)
        axlecounter.write_register(14, 0, functioncode=6)
        if axlecounter.read_register(13)  != 0:
            print("Axle Counter Reset Failed")
            #insert logging here
        if axlecounter.read_register(14) != 0:
            print("Axle Counter Reset Failed")
            # insert logging here
    except:
        print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed with module address " + str(AC_address))
        upcount, downcount = 0,0

    return upcount, downcount

def MQTT_setup():
    import paho.mqtt.client as mqtt  # import the client1
    broker_address = "127.0.0.1"
    # broker_address="iot.eclipse.org" #use external broker
    client = mqtt.Client("P1")  # create new instance
    client.connect(broker_address)  # connect to broker
    return client

def main(list_of_slaves, client):
    AC_dict = {}
    for slave in list_of_slaves:
        AC_dict[slave] = {"upcount": 0, "downcount": 0}
    while True:
        for slave in list_of_slaves:
            axlecounter_upcount, axlecounter_downcount = AC_read_and_clear(slave)
            AC_dict[slave]["upcount"] += axlecounter_upcount
            AC_dict[slave]["downcount"] += axlecounter_downcount
            #print("Slave " + str(slave), AC_dict[slave]["upcount"], AC_dict[slave]["downcount"])
            if axlecounter_upcount != 0:
                client.publish("AxleCounters/"+str(slave)+"/Up_count", AC_dict[slave]["upcount"])  # publish
            if axlecounter_downcount != 0:
                client.publish("AxleCounters/"+str(slave)+"/Down_count", AC_dict[slave]["downcount"])  # publish
            time.sleep(0.1)


if __name__ == "__main__":
    list_of_slaves = find_modubus_slaves()
    client = MQTT_setup()
    main(list_of_slaves, client)