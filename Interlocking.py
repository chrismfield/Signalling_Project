import logging
from logging.handlers import RotatingFileHandler

import jsons
import minimalmodbus
import paho.mqtt.client as mqtt
import time

import set
from object_definitions import AxleCounter, Signal, Point, Plunger, Section, Route, Trigger, AutomaticRouteSetting

mqtt_received_queue = []
mqtt_dict = {}

dynamic_variables = True

with open("config.json") as config_file:
    config = jsons.loads(config_file.read())


def on_message(mqtt_client, userdata, message):
    mqtt_received_queue.append(message)


def setup_mqtt():
    broker_address = config["mqtt_broker_address"]
    mqtt_client = mqtt.Client("interlocking")  # create new instance
    mqtt_client.connect(broker_address)  # connect to broker
    mqtt_client.on_message = on_message
    mqtt_client.subscribe("set/#")
    mqtt_client.loop_start()
    mqtt_client.publish("interlocking", "running")  # publish
    return mqtt_client


def setup_logger(logging_level):
    logger = logging.getLogger('Interlocking Processor')
    RFH = logging.handlers.RotatingFileHandler('./log.txt', maxBytes=1000000, backupCount=3)
    RFH.setFormatter(logging.Formatter("%(asctime)s;%(levelname)s;%(message)s"))
    logger.addHandler(RFH)
    CH = logging.StreamHandler()
    CH.setFormatter(logging.Formatter("%(asctime)s;%(levelname)s;%(message)s"))
    logger.addHandler(CH)
    logger.info(",Boot-Up")
    logger.setLevel(logging_level)
    return logger


def loadlayoutjson(logger, mqtt_client):
    """Load the layout database from file into instances of classes as defined in object_defintions"""
    json_in = open(config["layoutDB"])
    logger.info(" loaded " + config["layoutDB"])
    jsoninfradata = jsons.loads(json_in.read())  # turns file contents into a dictionary of the asset dictionaries
    jsonsectiondict = jsons.load(jsoninfradata["Sections"], dict)  # Strips into seperate assets dicts
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
        Section.instances[x].previousoccstatus = 0
    for x in jsonACdict.keys():
        AxleCounter.instances[x] = jsons.load(jsonACdict[x], AxleCounter)
        # create modbus slave object for each Axlecounter instance:
        AxleCounter.instances[x].slave = minimalmodbus.Instrument(
            config["network_ports"][AxleCounter.instances[x].network], AxleCounter.instances[x].address)
    for x in jsonsignaldict.keys():
        Signal.instances[x] = jsons.load(jsonsignaldict[x], Signal)
        Signal.instances[x].slave = minimalmodbus.Instrument(
            config["network_ports"][Signal.instances[x].network], Signal.instances[x].address)
        Signal.instances[x].aspect = {"danger"}  # convert aspect from dictionary to set following deserialisation.
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
    section_update(logger, mqtt_client)
    pass


# ---------------


# need to apply inputs, outputs and logic.
def check_all_ACs(logger, mqtt_client):
    """ get upcount and downcount from all axlecounters and store them in their instance"""
    for ACkey, ACinstance in AxleCounter.instances.items():
        ACinstance.upcount, ACinstance.downcount = 0, 0  # reset these variables to zero prior to read
        try:
            ACinstance.upcount, ACinstance.downcount = ACinstance.slave.read_registers(13,
                                                                                       2)  # register number, number of registers
            ACinstance.slave.write_register(13, 0, functioncode=6)  # register number, value
            ACinstance.slave.write_register(14, 0, functioncode=6)  # register number, value
            comms_status = " OK"

        except (OSError, ValueError) as error:
            ACinstance.upcount, ACinstance.downcount = 0, 0  # reset these variables to zero if no comms to avoid double counting
            comms_status = (" Comms failure " + str(error))

        if ACinstance.comms_status != comms_status:
            logger.error(ACinstance.ref + comms_status)
            ACinstance.comms_status = comms_status

    return


def check_all_plungers(logger):
    """ get status from all plungers and store in their instance"""
    for plungerkey, plungerinstance in Plunger.instances.items():
        try:
            plungerinstance.status = plungerinstance.slave.read_bit(plungerinstance.register,
                                                                    functioncode=1)  # register number, number of registers
            plungerinstance.slave.write_bit(plungerinstance.register, 0)  # register number,value
            if plungerinstance.status:
                logger.info(str(plungerinstance.ref) + " operated")
            comms_status = " OK"
        except (OSError, ValueError) as error:
            plungerinstance.status = 0  # reset these variables to zero if no comms to avoid double counting
            comms_status = (" Comms failure " + str(error))

        if plungerinstance.comms_status != comms_status:
            logger.error(plungerinstance.ref + comms_status)
            plungerinstance.comms_status = comms_status

    return

    pass  # -----------need to implement -------------


def section_update(logger, mqtt_client):
    """Update occupancy of sections based on axle-counter readings"""
    axle_tolerance = config["axle_tolerance"]
    for sectionkey, section in Section.instances.items():  # for each section:
        # create sub functions depending on type of section occupation detection
        old_occstatus = section.occstatus
        if section.mode == "axlecounter":
            for AC, direction in section.inctrig.items():  # for each increment trigger (which is in form "A1":"Upcount", "A2":"Downcount")
                if direction == "Upcount":
                    section.occstatus += AxleCounter.instances[AC].upcount
                if direction == "Downcount":
                    section.occstatus += AxleCounter.instances[AC].downcount
            if section.occstatus > 0:  # these three lines in here to help clear virtual section
                section.routeset = False
                section.routestatus = "not set"
            for AC, direction in section.dectrig.items():  # for each decrement trigger (which is in form "A1":"Upcount", "A2":"Downcount")
                if direction == "Upcount":
                    section.occstatus -= AxleCounter.instances[AC].upcount
                    if AxleCounter.instances[AC].upcount and (section.occstatus < axle_tolerance):
                        section.occstatus = 0
                if direction == "Downcount":
                    section.occstatus -= AxleCounter.instances[AC].downcount
                    if AxleCounter.instances[AC].downcount and (section.occstatus < axle_tolerance):
                        section.occstatus = 0
        # TODO add in other detection modes logic i.e. treadle and track circuit
        if section.occstatus != old_occstatus:
            logger.info(sectionkey + " " + str(section.occstatus))
        if section.occstatus:
            section.routeset = False
            section.routestatus = "not set"


def interlocking(logger):
    """Set all protecting signals to danger and secure points and routes as required"""

    def check_protecting_points(section, homesignal):
        """returns true if points are set to protect section"""
        if homesignal in section.protecting_points:
            protecting_points_dict = section.protecting_points[homesignal]
            for point, direction in protecting_points_dict.items():
                if Point.instances[point].set_direction and \
                        direction != Point.instances[point].set_direction:
                    return True
        return False

    def set_protecting_signals(section):
        # for each homesignal in each section set signal to danger: #TODO allow points to protect sections instead
        for homesignal in section.homesignal:
            if ("associated_position_light" not in Signal.instances[homesignal].aspect) and \
                    ("position_light" not in Signal.instances[homesignal].aspect) and \
                    not check_protecting_points(section, homesignal):
                Signal.instances[homesignal].aspect = {"danger"}

    def cancel_position_light(section):
        for homesignal in section.homesignal:
            if ("associated_position_light" in Signal.instances[homesignal].aspect) or \
                    ("position_light" in Signal.instances[homesignal].aspect):
                Signal.instances[homesignal].aspect = {"danger"}

    # for each section:
    for sectionkey, section in Section.instances.items():
        # if section has any axles:
        if section.occstatus > 0:
            set_protecting_signals(section)
        # if section count has increased, clear position light signal
        if section.occstatus > section.previousoccstatus:
            cancel_position_light(section)
        section.previousoccstatus = section.occstatus
        # if section has any axles or route is set through section:
        if section.occstatus > 0:
            # for every point, lock if it is in this occupied:
            # TODO ought to also check for section.routeset to lock points. But makes cancel and set new route harder.
            for pointkey, point in Point.instances.items():
                if point.section == sectionkey:
                    point.unlocked = False
                else:
                    point.unlocked = True
            # for every route, make not available if the section is occupied or route already set through:
            for routekey, route in Route.instances.items():
                if sectionkey in route.sections:
                    route.available = False
                else:
                    route.available = True


def check_points(logger, mqtt_client):
    for pointkey, point in Point.instances.items():
        old_detection_status = point.detection_status
        old_detection_boolean = point.detection_boolean
        if point.detection_mode:
            try:
                detection_normal = point.slave.read_bit(point.normal_coil, 2)  # read input corresponding to coil
                detection_reverse = point.slave.read_bit(point.reverse_coil, 2)  # read input corresponding to coil
                comms_status = " OK"
                point.last_comms_time = time.time()
            except (OSError, ValueError) as error:
                detection_status = "None"
                detection_normal = False
                detection_reverse = False
                comms_status = " Comms failure"
                if point.comms_status != comms_status:
                    logger.error(point.ref + comms_status)
                    point.comms_status = comms_status
                # don't loose detection if comms timeout is not reached.
                if time.time() - point.last_comms_time < config["point_interlock_timeout"]:
                    continue
            if detection_normal:
                detection_status = "normal"
            elif detection_reverse:
                detection_status = "reverse"
            else:
                detection_status = "None"
            if detection_status == point.set_direction:  # need to create get_detection function
                point.detection_boolean = True
                point.detection_status = detection_status
                # add point to list of set points in section

            else:
                point.detection_boolean = False
                point.detection_status = "None"
                for home_signal in Section.instances[point.section].homesignal:
                    set.set_signal(Signal.instances[home_signal], Signal.instances, Section.instances, Point.instances,
                                   logger=logger, aspect="danger")

            if point.comms_status != comms_status:
                logger.error(point.ref + comms_status)
                point.comms_status = comms_status
        else:
            point.detection_boolean = True
        if (point.detection_status != old_detection_status) or (point.detection_boolean != old_detection_boolean):
            logger.info(point.ref + " detection direction " + point.detection_status + " boolean " +
                        str(point.detection_boolean))


def maintain_signals(logger):
    # maintain signals by sending aspect regularly to avoid timeout
    for signal in Signal.instances.values():
        try:
            next_signal = Signal.instances[signal.nextsignal]
        except KeyError:
            next_signal = None
        set.set_signal(signal, Signal.instances, Section.instances, Point.instances, logger=logger,
                       nextsignal=next_signal)


def check_triggers(logger, mqtt_client, automatic_route_setting):
    def sections_to_cancel(trigger):
        """function to return a list of sections to cancel from a trigger with routes to cancel"""
        sections_to_cancel_list = []
        for route in trigger.routes_to_cancel:
            for section in Route.instances[route].sections:
                sections_to_cancel_list.append(section)
        return sections_to_cancel_list

    for trigger in sorted(Trigger.instances.values(), key=lambda x: x.priority, reverse=True):
        # check all conditions are true and continue to next trigger if not
        if not all([eval(condition) for condition in trigger.conditions]):
            continue
        else:
            pass
        # check if triggered by plunger:
        for plunger in trigger.plungers:
            if Plunger.instances[plunger].status:
                trigger.triggered = True
        # check if triggered by section occupancy:
        if trigger.sections_occupied and AutomaticRouteSetting.global_active:
            for trigger_section in trigger.sections_occupied:
                if Section.instances[trigger_section].occstatus > 0:
                    trigger.triggered = True
        # check if triggered by section vacancy:
        if trigger.sections_clear:
            for trigger_section_clear in trigger.sections_clear:
                if Section.instances[trigger_section_clear].occstatus == 0:
                    trigger.triggered = True
        # check if triggered by stored request:
        if trigger.stored_request:
            trigger.triggered = True
        # TODO implement timer?
        pass
        # check if triggered by expression - use eval()
        for expression in trigger.trigger_expressions:
            if eval(expression):
                trigger.triggered = True

        # try to set routes if triggered
        if trigger.triggered:
            logging.debug(trigger.ref + " triggered")
            full_route_ok = False

            if trigger.routes_to_set:
                for route in trigger.routes_to_set:
                    # test if full route can be set
                    if set.check_route_available(Route.instances[route],
                                                 sections=Section.instances,
                                                 points=Point.instances,
                                                 routes_to_cancel=trigger.routes_to_cancel,
                                                 sections_to_cancel=sections_to_cancel(trigger)):
                        full_route_ok = True
                    else:
                        full_route_ok = False
                        # store trigger if not possible to execute:
                        if trigger.store_request:
                            if not trigger.stored_request:
                                trigger.stored_request = True
                                logging.info(trigger.ref + " trigger stored")
                        else:
                            trigger.triggered = False
                        break
            else:
                full_route_ok = True

            if full_route_ok:
                # execute special trigger actions
                for action in trigger.trigger_special_actions:
                    exec(action)
                # cancel routes first
                for route in trigger.routes_to_cancel:
                    set.cancel_route(Route.instances[route],
                                     sections=Section.instances,
                                     points=Point.instances,
                                     signals=Signal.instances,
                                     triggers=Trigger.instances,
                                     logger=logger,
                                     mqtt_client=mqtt_client)
                # then set routes
                for route in trigger.routes_to_set:
                    set.set_route(Route.instances[route],
                                  sections=Section.instances,
                                  points=Point.instances,
                                  signals=Signal.instances,
                                  logger=logger,
                                  mqtt_client=mqtt_client)
                trigger.triggered = False
                trigger.stored_request = False
                logging.info(trigger.ref + " triggered and set")

    # clear all plungers requests after checking all triggers:
    set.set_plungers_clear(Plunger.instances)


def check_mqtt(logger, mqtt_client):
    while mqtt_received_queue:
        set.set_from_mqtt(command=mqtt_received_queue.pop(), signals=Signal.instances, sections=Section.instances,
                          points=Point.instances,
                          routes=Route.instances, triggers=Trigger.instances, logger=logger, mqtt_client=mqtt_client,
                          automatic_route_setting=AutomaticRouteSetting)
    # put command actions in here


def process(logger, mqtt_client):
    while True:
        check_all_ACs(logger, mqtt_client)
        section_update(logger, mqtt_client)
        interlocking(logger)
        check_points(logger, mqtt_client)
        maintain_signals(logger)
        check_all_plungers(logger)
        check_triggers(logger, mqtt_client, AutomaticRouteSetting)
        # iterate through setting routes
        for route in Route.instances.values():
            if route.setting:
                set.set_route(route,
                              sections=Section.instances,
                              points=Point.instances,
                              signals=Signal.instances,
                              logger=logger,
                              mqtt_client=mqtt_client)
        check_mqtt(logger, mqtt_client)
        set.send_status_to_mqtt(axlecounters=AxleCounter.instances,
                                signals=Signal.instances,
                                sections=Section.instances,
                                plungers=Plunger.instances,
                                points=Point.instances,
                                routes=Route.instances,
                                triggers=Trigger.instances,
                                logger=logger,
                                mqtt_client=mqtt_client,
                                mqtt_dict=mqtt_dict,
                                automatic_route_setting=AutomaticRouteSetting)


def main():
    logger = setup_logger(config["logging_level"])
    mqtt_client = setup_mqtt()
    loadlayoutjson(logger, mqtt_client)
    process(logger, mqtt_client)
    pass


if __name__ == '__main__':
    main()

# Next Jobs
# Finish points
# More work on routes interface - set routes but move route triggers into route scheduling?
# Get all the logic to work
# Route scheduling? This could be used to cycle routes on a trigger. Helper variables may be required
