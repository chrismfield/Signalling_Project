from object_definitions import AxleCounter, Signal, Point, Plunger, Section, Route, Trigger
import minimalmodbus
import jsons
import os
import operator
import serial.tools.list_ports
#import serial_ports_list
import set

with open("config.json") as config_file:
    config = jsons.loads(config_file.read())
print(config["layoutDB"])


def loadlayoutjson(loaddefault):
    """Load the layout database from file into instances of classes as defined in object_defintions"""
    global current_file
    # put file choser into a config file - set with track setup script
    json_in = open("default.json")
    jsoninfradata = jsons.loads(json_in.read())  # turns file contents into a dictionary of the asset dictionaries
    jsonsectiondict = jsons.load(jsoninfradata["Sections"], dict)  #Strips into seperate assets dicts
    jsonACdict = jsons.load(jsoninfradata["AxleCounters"], dict)
    jsonsignaldict = jsons.load(jsoninfradata["Signals"], dict)
    jsonplungerdict = jsons.load(jsoninfradata["Plungers"], dict)
    jsonpointdict = jsons.load(jsoninfradata["Points"], dict)
    jsonroutesdict = jsons.load(jsoninfradata["Routes"], dict)
    json_trigger_dict = jsons.load(jsoninfradata["Triggers"], dict)
    # for each instance of an asset, turn the dict back into the class instance and add to the class variable dict of
    # those assets
    for x in jsonsectiondict.keys():
        Section.instances[x] = jsons.load(jsonsectiondict[x], Section)
    for x in jsonACdict.keys():
        AxleCounter.instances[x] = jsons.load(jsonACdict[x], AxleCounter)
        # create modbus slave object for each Axlecounter instance:
        AxleCounter.instances[x].slave = minimalmodbus.Instrument(
            config["network_ports"][AxleCounter.instances[x].network], AxleCounter.instances[x].address)
    for x in jsonsignaldict.keys():
        Signal.instances[x] = jsons.load(jsonsignaldict[x], Signal)
        Signal.instances[x].slave = minimalmodbus.Instrument(
            config["network_ports"][Signal.instances[x].network], Signal.instances[x].address)
    for x in jsonplungerdict.keys():
        Plunger.instances[x] = jsons.load(jsonplungerdict[x], Plunger)
        Plunger.instances[x].slave = minimalmodbus.Instrument(
            config["network_ports"][Plunger.instances[x].network], Plunger.instances[x].address)
    for x in jsonpointdict.keys():
        Point.instances[x] = jsons.load(jsonpointdict[x], Point)
        # create modbus slave object for each Point instance:
        Point.instances[x].slave = minimalmodbus.Instrument(
            config["network_ports"][Point.instances[x].network], Point.instances[x].address)
    for x in jsonroutesdict.keys():
        Route.instances[x] = jsons.load(jsonroutesdict[x], Route)
    for x in json_trigger_dict.keys():
        Trigger.instances[x] = jsons.load(json_trigger_dict[x], Trigger)
    #    RS485port =
    currentfile = os.path.basename(json_in.name)
    print("loadnow")
    section_update()
    pass

# ---------------


# need to apply inputs, outputs and logic.
def check_all_ACs():
    """ get upcount and downcount from all axlecounters and store them in their instance"""
    for ACkey, ACinstance in AxleCounter.instances.items():
        try:
            ACinstance.upcount, ACinstance.downcount = ACinstance.slave.read_registers(13,
                                                                            2)  # register number, number of registers
            ACinstance.slave.write_register(13, 0, functioncode=6)  # register number, value
            ACinstance.slave.write_register(14, 0, functioncode=6)  # register number, value
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
            plungerinstance.status = plungerinstance.slave.read_bit(plungerinstance.register, 1)  # register number, number of registers
            plungerinstance.slave.write_bit(plungerinstance.register, 0)  # register number,value
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
        #create sub functions depending on type of section occupation detection
        if section.mode == "axlecounter":
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
        if section.occstatus:
            section.routeset = False


def interlocking():
    """Set all protecting signals to danger and secure points and routes as required"""
    # for each section:
    for sectionkey, section in Section.instances.items():
        # if section has any axles:
        if section.occstatus > 0:
            # for each homesignal in each section set signal to danger:
            for homesignal in section.homesignal:
                Signal.instances[homesignal].aspect = "danger"
        #if section has any axles or route is set through section:
        if section.occstatus > 0 or section.routeset == True:
            #for every point, lock if it is in this occupied/route-set section:
            for pointkey, point in Point.instances.items():
                if point.section == sectionkey:
                    point.unlocked = False
                else:
                    point.unlocked = True
            #for every route, make not available if the section is occupied or route already set through:
            for routekey, route in Route.instances.items():
                if sectionkey in route.sections:
                    route.available = False
                else:
                    route.available = True


def check_points():
    for pointkey, point in Point.instances.items():
        if point.detection_mode:
            try:
                detection_normal = point.slave.read_bit(point.register, 21) # replace 21 with reference from JSON file
                detection_reverse = point.slave.read_bit(point.register, 21) # re[;ace 22 with reference from JSON file
            except:
                detection_status = None
                detection_normal = detection_reverse = False
            if detection_normal:
                detection_status = "normal"
            elif detection_reverse:
                detection_status = "reverse"
            else:
                detection_status = None
            if detection_status == point.set_direction: #need to create get_detection function
                point.detection_boolean = True
                point.detection_status = detection_status
                #add point to list of set points in section

            else:
                point.detection_boolean = False
                point.detection_status = ""
                set.set_signal(Signal.instances[Section.instances[point.section].homesignal], "danger")

                #remove point from list of set points in section
                #set route status to not available
                #set protecting signal to danger - or do this elsewhere??

def maintain_signals():
    # maintain signals by sending aspect regularly to avoid timeout
    for signal in Signal.instances():
        set.set_signal(signal, nextsignal = Signal.instances[signal.nextsignal])


def clear_used_routes(): #if required
    pass


def check_triggers():

    for trigger_key, trigger in (sorted(Trigger.instances.items(), key=operator.attrgetter("priority"))):
        #check all conditions are true and continue to next trigger if not
        if not all([eval(condition) for condition in trigger.conditions]):
            continue
        # check if triggered by plunger:
        for plunger in trigger.plungers:
            if Plunger.instances[plunger].status:
                trigger.triggered = True
        # check if triggered by section occupancy:
        for trigger_section in trigger.sections_occupied:
            if Section.instances[trigger_section].occstatus > 0:
                trigger.triggered = True
        # check if triggered by section vacancy:
        for trigger_section_clear in trigger.sections_clear:
            if Section.instances[trigger_section_clear].occstatus == 0:
                trigger.triggered = True
        # check if triggered by stored request:
        if trigger.stored_request:
            trigger.triggered = True
        # TODO check if triggered by timer
        pass
        # check if triggered by expression - use eval()
        for expression in trigger.trigger_expressions:
            if eval(expression):
                trigger.triggered = True
        # TODO check if triggered by MQTT
        pass

        # try to set routes if triggered
        if trigger.triggered:
            full_route_ok = False
            for route in trigger.routes_to_set:
                # test if full route can be set
                if set.check_route_available(Route.instances[route]):
                    full_route_ok = True
                else:
                    full_route_ok = False
                    # store trigger if not possible to execute:
                    if trigger.store_request:
                        trigger.stored_request = True
                    continue

            if full_route_ok:
                for route in trigger.routes_to_set:
                    set.set_route(route,
                                  sections = Section.instances,
                                  points = Point.instances,
                                  signals = Signal.instances)
                    trigger.triggered = False

        pass # set route

    # clear all plungers requests after checking all triggers:
    set.set_plungers_clear(Plunger.instances)


# TODO apply interlocking doublecheck?

# ---------------

def process():
    while True:
        check_all_ACs()
        section_update()
        interlocking()
        check_points()
        maintain_signals()
        check_all_plungers()
        check_triggers()
        # iterate through setting routes
        for route in Route.instances.values():
            if route.set == "setting":
                set.set_route(route, sections = Section.instances, points = Point.instances, signals = Signal.instances)
        # TODO put the MQTT update in here
        # TODO put MQTT commands in too


def main():
    loaddefault = False
    loadlayoutjson(loaddefault)
    process()
    pass


if __name__ == '__main__':
    main()

# Next Jobs
# Finish points
# More work on routes interface - set routes but move route triggers into route scheduling?
# Get all the logic to work
# Route scheduling? This could be used to cycle routes on a trigger. Helper variables may be required
