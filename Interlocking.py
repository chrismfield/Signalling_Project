from object_definitions import AxleCounter, Signal, Point, Plunger, Section, Route
import minimalmodbus
import jsons
import os
import serial.tools.list_ports
import serial_ports_list

currentfile = "default.json"

def loadlayoutjson(loaddefault):
    """Load the layout database from file into instances of classes as defined in object_defintions"""
    global currentfile
    global RS485port
    # put file choser into a config file - set with track setup script
    json_in = open("default.json")
    jsoninfradata = jsons.loads(json_in.read())  # turns file contents into a dictionary of the asset dictionaries
    jsonsectiondict = jsons.load(jsoninfradata["Sections"], dict)  #Strips into seperate assets dicts
    jsonACdict = jsons.load(jsoninfradata["AxleCounters"], dict)
    jsonsignaldict = jsons.load(jsoninfradata["Signals"], dict)
    jsonplungerdict = jsons.load(jsoninfradata["Plungers"], dict)
    jsonpointdict = jsons.load(jsoninfradata["Points"], dict)
    jsonroutesdict = jsons.load(jsoninfradata["Routes"], dict)
    for x in jsonsectiondict.keys(): # for each instance of an asset, turns the dict back into the class instance and adds to the global dict of those assets
        Section.instances[x] = jsons.load(jsonsectiondict[x], Section)
    for x in jsonACdict.keys():
        AxleCounter.instances[x] = jsons.load(jsonACdict[x], AxleCounter)
    for x in jsonsignaldict.keys():
        Signal.instances[x] = jsons.load(jsonsignaldict[x], Signal)
    for x in jsonplungerdict.keys():
        Plunger.instances[x] = jsons.load(jsonplungerdict[x], Plunger)
    for x in jsonpointdict.keys():
        Point.instances[x] = jsons.load(jsonpointdict[x], Point)
    for x in jsonroutesdict.keys():
        Route.instances[x] = jsons.load(jsonroutesdict[x], Route)
    #    RS485port =
    currentfile = os.path.basename(json_in.name)
    print("loadnow")
    updatesections()
    pass

def updatesections():
    pass



# ---------------


# need to apply inputs, outputs and logic.
def check_all_ACs():
    """ get upcount and downcount from all axlecounters and store them in their instance"""
    for ACkey, ACinstance in AxleCounter.instances.items():
        try:
            slave = minimalmodbus.Instrument(RS485port, ACinstance.address)
            ACinstance.upcount, ACinstance.downcount = slave.read_registers(13,
                                                                            2)  # register number, number of registers
            slave.write_register(13, 0, functioncode=6)  # register number, value
            slave.write_register(14, 0, functioncode=6)  # register number, value
            status = "OK"

        except:
            ACinstance.upcount, ACinstance.downcount = 0, 0  # reset these variables to zero if no comms to avoid double counting
            status = "Comms failure with " + ACinstance.ref

        if status != "OK":
            print(status)
    return


def check_all_plungers():
    """ get status from all plungers and store in their instance"""
    for plungerkey, plungerinstance in Plunger.instances.items():
        try:
            slave = minimalmodbus.Instrument(RS485port, plungerinstance.address)
            plungerinstance.status = slave.read_bit(plungerinstance.register, 1)  # register number, number of registers
            slave.write_bit(plungerinstance.register, 0)  # register number,value
            status = "OK"
        except:
            plungerinstance.status = 0  # reset these variables to zero if no comms to avoid double counting
            status = "Comms failure with " + plungerinstance.ref

        if status != "OK":
            print(status)
    return

    pass  # -----------need to implement -------------


def section_update():
    """Update occupancy of sections based on axle-counter readings"""
    for sectionkey, section in Section.instances.items():  # for each section:
        for AC, direction in section.inctrig.items(): #for each increment trigger (which is in form "A1":"Upcount", "A2":"Downcount")
            if direction == "Upcount":
                section.occstatus += AC.upcount
            if direction == "Downcount":
                section.occstatus += AC.downcount
        for AC, direction in section.dectrig.items(): #for each decrement trigger (which is in form "A1":"Upcount", "A2":"Downcount")
            if direction == "Upcount":
                section.occstatus -= AC.upcount
            if direction == "Downcount":
                section.occstatus -= AC.downcount

def interlocking():
    """Set all protecting signals to danger and secure points and routes as required"""
    # for each section:
    for sectionkey, section in Section.instances.items():
        # if section has any axles:
        if section.occstatus > 0:
            # for each homesignal in each section set signal to danger:
            for homesignal in section.homesignal:
                Signal.instances[homesignal].aspect = 0
        #if section has any axles or route is set through section:
        if section.occstatus > 0 or section.routeset == True:
            #for every point, lock if it is in this occupied/route-set section:
            for pointkey, point in Point.instances.items():
                if point.section == sectionkey:
                    point.unlocked = False
            #for every route, make not available if the section is occupied or route already set through:
            for routekey, route in Route.instances.items():
                if sectionkey in route.sections:
                    route.available = False


def check_points():
    pass  # -------------need to implement-----------


# Check route triggers
# Set routes (will need to iterate this to wait for point detection)
# check conflicting sections
# apply interlocking doublecheck

# Send outputs to relevant points and all signals


# ---------------

def process(RS485port):
    while True:
        check_all_ACs()
        section_update()
        interlocking()
        check_points()
        check_all_plungers()
        # put the MQTT update in here



#not used - delete once other com port method proven.
def comm_chooser(master):
    #put logic to work in both linux and windows in here
    mycomlist = ([comport.device for comport in serial.tools.list_ports.comports()])
    RS485port = mycomlist[-1]



def main():
    loaddefault = False
    loadlayoutjson(loaddefault)
    comlist = serial_ports_list()
    RS485port = comlist[-1]
    process(RS485port)
    pass


if __name__ == '__main__':
    main()

# Next Jobs
# Configurable direction on axlecounter triggers
# More work on routes interface - set routes but move route triggers into route scheduling?
# Get all the logic to work
# Pickle Com port selection - put in an ini file?
# Route scheduling? This could be used to cycle routes on a trigger.
