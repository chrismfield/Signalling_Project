from custom_exceptions import *

def set_point(point, direction, sections, logger, mqtt_client, route = None):
    # don't move points if section is occupied
    if sections[point.section].occstatus:
        logger.critical("Cannot set points when section is occupied")
        raise InterlockingError("Cannot set points when section is occupied")
    elif sections[point.section].routeset and sections[point.section].routestatus != "setting":
        logger.critical("Cannot set points when route is set through section")
        raise InterlockingError("Cannot set points when route is set through section")
    elif not point.unlocked:
        logger.error("Trying to set points when locked")
    else:
        comms_status = "no direction set"
        point.set_direction = direction
        point.detection_boolean = False
        point.detection_status = "None"
        point.routeset = route
        if direction == "normal":
            try:
                point.slave.write_bit(point.reverse_coil, 0)
                point.slave.write_bit(point.normal_coil, 1)
                comms_status = " OK"
                #logger.info(point.ref + " set normal")
            except (OSError, ValueError) as error:
                comms_status = (" Comms failure " + str(error))
        if direction == "reverse":
            try:
                point.slave.write_bit(point.normal_coil, 0)
                point.slave.write_bit(point.reverse_coil, 1)
                comms_status = " OK"
                #logger.info(point.ref + " set reverse")
            except (OSError, ValueError) as error:
                comms_status = (" Comms failure " + str(error))

        if point.comms_status != comms_status:
            logger.error(point.ref + comms_status)
            point.comms_status = comms_status

def set_signal(signal, sections, points, logger, aspect=None, nextsignal =None, send_commands = True, route = None): #arguments are signal object and aspect as string
    main_proceed_aspects = ["clear", "caution", "doublecaution"]
    proceed_aspects = ["clear", "caution", "doublecaution", "associated_position_light", "position_light"]
    old_aspects = signal.aspect.copy()
    def set_aspect():
        #don't set signal if section is occupied


        if aspect in main_proceed_aspects:
            for section in sections.values():
                if signal.ref in section.homesignal:
                    if section.occstatus:
                        logger.critical("Cannot clear signal when section is occupied")
                        raise InterlockingError("Cannot clear signal when section is occupied")
                    for point in points.values():
                        if point.section == section.ref:
                            if not point.detection_boolean:
                                logger.critical("Cannot clear signal when section points not detected")
                                raise InterlockingError("Cannot clear signal when section points not detected")
        comms_status = ""
        #clear other aspects if set to danger
        if aspect == "danger":
            signal.aspect.clear()
            signal.aspect.add(aspect)
        elif aspect:
            #update class instance with aspect instruction
            if aspect in proceed_aspects:
                signal.aspect.discard("danger")
                for PA in proceed_aspects:
                    signal.aspect.discard(PA)
            signal.aspect.add(aspect)
            signal.routeset = route
        if signal.aspect != old_aspects:
            logger.info(signal.ref + " aspects requested " + str(signal.aspect))



    def send_aspect_commands():  #set aspects through slaves and lookups
        for set_aspect in signal.aspect:

            if set_aspect == "danger":
                try:
                    if signal.dangerreg:
                        signal.slave.write_bit(signal.dangerreg, 1)
                    if signal.cautionreg:
                        signal.slave.write_bit(signal.cautionreg, 0)
                    if signal.clearreg:
                        signal.slave.write_bit(signal.clearreg, 0)
                    if signal.callingonreg:
                        signal.slave.write_bit(signal.callingonreg, 0)
                    if signal.bannerreg:
                        signal.slave.write_bit(signal.bannerreg, 0)
                    if signal.route1reg:
                        signal.slave.write_bit(signal.route1reg, 0)
                    if signal.route2reg:
                        signal.slave.write_bit(signal.route2reg, 0)
                    if signal.route3reg:
                        signal.slave.write_bit(signal.route3reg, 0)
                    if signal.route4reg:
                        signal.slave.write_bit(signal.route4reg, 0)
                    if signal.route5reg:
                        signal.slave.write_bit(signal.route5reg, 0)
                    if signal.route6reg:
                        signal.slave.write_bit(signal.route6reg, 0)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "caution":
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    if signal.clearreg:
                        signal.slave.write_bit(signal.clearreg, 0)
                    if signal.callingonreg:
                        signal.slave.write_bit(signal.callingonreg, 0)
                    signal.slave.write_bit(signal.cautionreg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "doublecaution":
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    if signal.clearreg:
                        signal.slave.write_bit(signal.clearreg, 0)
                    if signal.callingonreg:
                        signal.slave.write_bit(signal.callingonreg, 0)
                    signal.slave.write_bit(signal.cautionreg, 1)
                    signal.slave.write_bit(signal.doublecautionreg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "clear":
                #test if next aspect is a main proceed aspect
                next_signal_MPA = False
                try:
                    next_signal_MPA = [True for MPA in main_proceed_aspects if MPA in nextsignal.aspect]
                except AttributeError:
                    if nextsignal == None:
                        next_signal_MPA = True
                if next_signal_MPA:
                    try:
                        signal.slave.write_bit(signal.dangerreg, 0)
                        if signal.cautionreg: # only turn off caution reg if there is a caution aspect to turn off
                            signal.slave.write_bit(signal.cautionreg, 0)
                        if signal.callingonreg:
                            signal.slave.write_bit(signal.callingonreg, 0)
                        #signal.slave.write_bit(signal.doublecautionreg, 0) # TODO fix this to work if no register for this
                        signal.slave.write_bit(signal.clearreg, 1)
                        comms_status = " OK"
                    except (OSError, ValueError) as error:
                        comms_status = (" Comms failure " + str(error))
                #if not, apply a caution aspect
                else:
                    # TODO add in check of available aspects to understand if possible to clear caution aspect
                    try:
                        signal.slave.write_bit(signal.dangerreg, 0)
                        signal.slave.write_bit(signal.cautionreg, 1)
                        comms_status = " OK"
                    except (OSError, ValueError) as error:
                        comms_status = (" Comms failure " + str(error))
            if set_aspect == "associated_position_light":  # used where main danger aspect not to be turned off
                try:
                    signal.slave.write_bit(signal.dangerreg, 1)
                    signal.slave.write_bit(signal.callingonreg, 1)
                    if signal.cautionreg:
                        signal.slave.write_bit(signal.cautionreg, 0)
                    if signal.clearreg:
                        signal.slave.write_bit(signal.clearreg, 0)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "position_light": # used where main danger aspect to be turned off
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    signal.slave.write_bit(signal.callingonreg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "bannerreg":
                try:
                    signal.slave.write_bit(signal.bannerreg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "route1":
                try:
                    signal.slave.write_bit(signal.route1reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "route2":
                try:
                    signal.slave.write_bit(signal.route2reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "route3":
                try:
                    signal.slave.write_bit(signal.route3reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "route4":
                try:
                    signal.slave.write_bit(signal.route4reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "route5":
                try:
                    signal.slave.write_bit(signal.route5reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if set_aspect == "route6":
                try:
                    signal.slave.write_bit(signal.route6reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))


            if signal.comms_status != comms_status:
                logger.error(signal.ref + comms_status)
                signal.comms_status = comms_status


    set_aspect()
    if send_commands:
        send_aspect_commands()

def check_route_available(route, points, sections, routes_to_cancel = [], sections_to_cancel = []):
    for route_section in route.sections:
        # exclude sections_to_cancel from routeset sections
        if sections[route_section].routeset and (sections[route_section].routeset not in routes_to_cancel):
            return False
        if sections[route_section].routestatus == "setting" and (route_section not in sections_to_cancel):
            return False
        if sections[route_section].occstatus:
            return False # don't set if route is occupied
        for section in sections[route_section].conflictingsections:
            if sections[section].routeset and (sections[section].routeset not in routes_to_cancel):
                return False
            if sections[section].routestatus == "setting" and (sections[section].routeset not in routes_to_cancel):
                return False
        for section in sections[route_section].conflictingsections:
            if sections[section].occstatus:
                return False
    for point in route.points:
        if not points[point].unlocked:
            return False
    return True
def set_route(route, sections, points, signals, logger, mqtt_client):

    # check route is clear to set
    if check_route_available(route, points, sections) or route.setting:

        #route.set = "setting" # not required?
        # set points - move to route setting iteration?
        points_detected = False
        route.setting = True
        for point_ref, direction in route.points.items():
            #check if all points are set
            if points[point_ref].detection_boolean and points[point_ref].detection_status == direction:
                points_detected = True
            else:
                points_detected = False
                set_point(points[point_ref], direction, sections, logger, mqtt_client, route = route.ref)
                #this also prevents next points setting until previous points detected
                break

        # set section.routeset when route is setting or set
        for section in route.sections:
            sections[section].routestatus = "setting"
            # set signals (check that route is clear already completed):
            # check points for that section are set and detected correctly
        if points_detected or not route.points.items():
            # set signal for that section in accordance with route signals to set
            for signal, aspects in route.signals.items():
                for aspect in aspects:
                    set_signal(signals[signal], sections=sections, points=points, logger=logger, aspect=aspect, send_commands = False, route=route.ref)
            # clear trigger once route fully set
            #route.set = True # not required?
            route.setting = False
            for section in route.sections:
                sections[section].routestatus = "set"
                sections[section].routeset = route.ref
    else:
        return "route not available"

def cancel_route(route, sections, points, signals, triggers, logger, mqtt_client):
    for section in route.sections:
        if sections[section].routeset == route.ref:
            sections[section].routeset = False
            sections[section].routestatus = "not set"
    for signal_ref, aspects in route.signals.items():
        if signals[signal_ref].routeset == route.ref:
            set_signal(signals[signal_ref], sections=sections, points=points, logger=logger, aspect="danger")
    for point_ref, direction in route.points.items():
        if points[point_ref].routeset == route.ref:
            points[point_ref].routeset = None
            # unlock points if section not occupied
            if sections[points[point_ref].section].occstatus == 0:
                points[point_ref].unlocked = True
    for trigger_ref, trigger in triggers.items():
        if route.ref in trigger.routes_to_set:
            trigger.stored_request = False
    route.setting = False

def set_plungers_clear(all_plungers_dict):
    for plunger_key, plunger in all_plungers_dict.items():
        plunger.status = 0

def set_from_mqtt(command, signals, sections, points, routes, triggers, logger, mqtt_client):
    command_l = command.topic.split("/")
    command_payload = str(command.payload.decode("utf-8"))
    if command_l[0] != "set":
        return
    if command_l[1] == "point":
        set_point(point=points[command_l[2]], direction=command_payload, sections=sections, logger=logger, mqtt_client=mqtt_client)
    # TODO implement point locking
    if command_l[1] == "signal":
        set_signal(signal=signals[command_l[2]], sections=sections, points=points, logger=logger, aspect=command_payload, send_commands = False)
    if command_l[1] == "route":
        if eval(command_payload):
            set_route(route=routes[command_l[2]], sections=sections, points=points, signals = signals, logger=logger, mqtt_client=mqtt_client)
        if not eval(command_payload):
            cancel_route(route=routes[command_l[2]], sections=sections, points=points, signals = signals, triggers = triggers, logger=logger, mqtt_client=mqtt_client)
    if command_l[1] == "trigger":
        triggers[command_l[2]].triggered = eval(command_payload)
    if command_l[1] == "section" and command_l[3] == "occstatus":
        sections[command_l[2]].occstatus = int(command_payload)
        logger.info(str(command_l[2]) + " reset")



def send_status_to_mqtt(axlecounters, signals, sections, plungers, points, routes, triggers, logger, mqtt_client):
    pass
    # send axlecounter dynamic variables
    for axlecounter in axlecounters.values():
        mqtt_client.publish("error/axlecounter/comms/"+ axlecounter.ref, axlecounter.comms_status)
    # send signal dynamic variables
    for signal in signals.values():
        mqtt_client.publish("report/signal/"+ signal.ref +"/aspect", (",".join(signal.aspect)))
        mqtt_client.publish("error/signal/comms/"+ signal.ref, signal.comms_status)
    # send section dynamic variables
    for section in sections.values():
        mqtt_client.publish("report/section/"+ section.ref+"/occstatus", section.occstatus)
        mqtt_client.publish("report/section/"+ section.ref+"/routeset", section.routeset)
        mqtt_client.publish("report/section/" + section.ref + "/routestatus", section.routestatus)
    # send plunger dynamic variables
    for plunger in plungers.values():
        mqtt_client.publish("error/plunger/comms/" + plunger.ref, plunger.comms_status)
    # send point dynamic variables
    for point in points.values():
        mqtt_client.publish("report/point/"+point.ref+"/set_direction", point.set_direction)
        mqtt_client.publish("report/point/"+point.ref+"/detection_status", point.detection_status)
        mqtt_client.publish("report/point/"+point.ref+"/detection_boolean", point.detection_boolean)
        mqtt_client.publish("report/point/"+point.ref+"/unlocked", point.unlocked)
        mqtt_client.publish("error/point/comms/" + point.ref, point.comms_status)
    # send route dynamic variables
    for route in routes.values():
        mqtt_client.publish("report/route/"+route.ref+"/available", route.available)
        mqtt_client.publish("report/route/"+route.ref+"/setting", route.setting)
    # send trigger dynamic variables
    for trigger in triggers.values():
        #mqtt_client.publish("report/trigger/"+trigger.ref+"/triggered", trigger.triggered) # not req- never true here.
        mqtt_client.publish("report/trigger/"+trigger.ref+"/stored_request", trigger.stored_request)
