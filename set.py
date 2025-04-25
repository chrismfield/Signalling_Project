"""set.py provides:
- entry points to change devices
- safety checks before changing
- driver to connect to devices
- handles route setting with checks
- handles route cancelling
- responds to mqtt commands"""

from custom_exceptions import *

main_proceed_aspects = ["clear", "caution", "doublecaution"]
proceed_aspects = ["clear", "caution", "doublecaution", "associated_position_light", "position_light"]


def set_point(point, direction, sections, logger, mqtt_client, route=None):
    # don't move points if section is occupied
    if sections[point.section].occstatus:
        logger.critical("Cannot set points when section is occupied")
        raise InterlockingError("Cannot set points when section is occupied")
    elif sections[point.section].routeset and sections[point.section].routestatus != "setting":
        logger.critical("Cannot set points when route is set through section")
        raise InterlockingError("Cannot set points when route is set through section")
    elif not point.unlocked:
        logger.error("Trying to set points when locked")
    # checks all passed, safe to change
    else:
        comms_status = "no direction set"
        point.set_direction = direction
        point.detection_boolean = False
        point.detection_status = "None"
        point.routeset = route
        if direction == "normal":
            try:
                #coils are write-only modbus registers; one for each direction, must always be opposite
                point.slave.write_bit(point.reverse_coil, 0)
                point.slave.write_bit(point.normal_coil, 1)
                comms_status = " OK"
                # logger.info(point.ref + " set normal")
            except (OSError, ValueError) as error:
                comms_status = (" Comms failure " + str(error))
        if direction == "reverse":
            try:
                point.slave.write_bit(point.normal_coil, 0)
                point.slave.write_bit(point.reverse_coil, 1)
                comms_status = " OK"
                # logger.info(point.ref + " set reverse")
            except (OSError, ValueError) as error:
                comms_status = (" Comms failure " + str(error))

        # Determine if logging is required due to state change
        if point.comms_status != comms_status:
            logger.info(point.ref + comms_status)
            point.comms_status = comms_status


def set_signal(signal, signals, sections, points, logger, aspect=None, nextsignal=None, send_commands=True, route=None):
    # arguments are signal object and aspect as string
    old_aspects = signal.aspect.copy()

    def check_protecting_points(protecting_points):
        """returns true if points are set to protect section"""
        if protecting_points and (signal.ref in protecting_points):
            section_protecting_points = protecting_points[signal.ref]
            for point, direction in section_protecting_points.items():
                if direction != points[point].set_direction:
                    return True
        return False

    def set_aspect():
        """only sets aspect if permitted"""
        # don't set signal if not permitted
        for section in sections.values():
            # you can set signal to danger without any further checks.
            if aspect == "danger":
                break
            # only check signal for section if points are not already protecting the section
            if signal.ref in section.homesignal and not check_protecting_points(section.protecting_points):
                # don't set signal if section is occupied
                if section.occstatus and (aspect in main_proceed_aspects):
                    logger.critical("Cannot clear signal when section is occupied")
                    raise InterlockingError("Cannot clear signal when section is occupied")
                #don't set signal if points in section do not have detection
                for point in points.values():
                    if point.section == section.ref:
                        if not point.detection_boolean:
                            logger.critical("Cannot clear signal when section points not detected")
                            raise InterlockingError("Cannot clear signal when section points not detected")
        # to protect against two signals feeding into one section being set
        for conflicting_signal in signal.conflicting_signals:
            if aspect == "danger":
                break
            if signals[conflicting_signal].aspect != {"danger"}:
                logger.critical("Cannot clear signal when conflicting signal set")
                raise InterlockingError("Cannot clear signal when conflicting signal set")

        # clear other aspects if set to danger
        if aspect == "danger":
            signal.aspect.clear()
            signal.aspect.add(aspect)
        elif aspect:
            # update class instance with aspect instruction
            if aspect in proceed_aspects:
                signal.aspect.discard("danger")
                for PA in proceed_aspects:
                    signal.aspect.discard(PA)
            signal.aspect.add(aspect)
            signal.routeset = route

        # Determine if logging is required
        if signal.aspect != old_aspects:
            logger.info(signal.ref + " aspects requested " + str(signal.aspect))

    def send_aspect_commands():  # set aspects through slaves and lookups
        for req_aspect in signal.aspect:
            comms_status = ""
            if req_aspect == "danger":
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
            if req_aspect == "caution":
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
            if req_aspect == "doublecaution":
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
            if req_aspect == "clear":
                # test if next aspect is a main proceed aspect
                # noinspection PyPep8Naming
                next_signal_MPA = False
                try:
                    # noinspection PyPep8Naming
                    next_signal_MPA = [True for MPA in main_proceed_aspects if MPA in nextsignal.aspect]
                except AttributeError:
                    if nextsignal is None:
                        # noinspection PyPep8Naming
                        next_signal_MPA = True
                if next_signal_MPA:
                    try:
                        signal.slave.write_bit(signal.dangerreg, 0)
                        if signal.cautionreg:  # only turn off caution reg if there is a caution aspect to turn off
                            signal.slave.write_bit(signal.cautionreg, 0)
                        if signal.callingonreg:
                            signal.slave.write_bit(signal.callingonreg, 0)
                        # signal.slave.write_bit(signal.doublecautionreg, 0) # TODO fix this to work if no register for this
                        signal.slave.write_bit(signal.clearreg, 1)
                        comms_status = " OK"
                    except (OSError, ValueError) as error:
                        comms_status = (" Comms failure " + str(error))
                # if not, apply a caution aspect
                else:
                    # TODO add in check of available aspects to understand if possible to clear caution aspect
                    try:
                        signal.slave.write_bit(signal.dangerreg, 0)
                        signal.slave.write_bit(signal.cautionreg, 1)
                        comms_status = " OK"
                    except (OSError, ValueError) as error:
                        comms_status = (" Comms failure " + str(error))
            if req_aspect == "associated_position_light":  # used where main danger aspect not to be turned off
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
            if req_aspect == "position_light":  # used where main danger aspect to be turned off
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    signal.slave.write_bit(signal.callingonreg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "bannerreg":
                try:
                    signal.slave.write_bit(signal.bannerreg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "route1":
                try:
                    signal.slave.write_bit(signal.route1reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "route2":
                try:
                    signal.slave.write_bit(signal.route2reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "route3":
                try:
                    signal.slave.write_bit(signal.route3reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "route4":
                try:
                    signal.slave.write_bit(signal.route4reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "route5":
                try:
                    signal.slave.write_bit(signal.route5reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))
            if req_aspect == "route6":
                try:
                    signal.slave.write_bit(signal.route6reg, 1)
                    comms_status = " OK"
                except (OSError, ValueError) as error:
                    comms_status = (" Comms failure " + str(error))

            # Determine if logging is required
            if signal.comms_status != comms_status:
                logger.error(signal.ref + comms_status)
                signal.comms_status = comms_status

    if aspect:
        set_aspect()
    if send_commands:
        send_aspect_commands()


def check_route_available(route, points, sections, routes_to_cancel=None):
    if routes_to_cancel is None:
        routes_to_cancel = []
    for route_section in route.sections:
        # don't set route if a route is already set or setting through the section and will not be cancelled
        if sections[route_section].routeset and (sections[route_section].routeset not in routes_to_cancel):
            return False
        if sections[route_section].routestatus == "setting" and \
                (sections[route_section].routeset not in routes_to_cancel):
            return False
        # don't set route if section is occupied and signal aspect is a main proceed aspect
        section_signals = sections[route_section].homesignal
        for section_signal in section_signals:
            if section_signal in route.signals:
                signal_aspects = route.signals[section_signal]
                if sections[route_section].occstatus and \
                        [aspect for aspect in signal_aspects if aspect in main_proceed_aspects]:
                    return False
        # don't set route if there is a conflicting section set or occupied
        for section in sections[route_section].conflictingsections:
            if sections[section].routeset and (sections[section].routeset not in routes_to_cancel):
                return False
            if sections[section].routestatus == "setting" and (sections[section].routeset not in routes_to_cancel):
                return False
        for section in sections[route_section].conflictingsections:
            if sections[section].occstatus:
                return False
            # don't set route if points are locked
    for point in route.points:
        if not points[point].unlocked:
            return False
    # TODO don't set route if there is a conflicting signal set - currently raises an exception - OK?

    return True


def set_route(route, sections, points, signals, logger, mqtt_client):

    # check route is clear to set
    if check_route_available(route, points, sections) or route.setting:

        # set points - move to route setting iteration?
        points_detected = False
        route.setting = True
        # iterate once to set the points:
        for point_ref, direction in route.points.items():
            # check if all points are set
            if points[point_ref].detection_boolean and points[point_ref].detection_status == direction:
                pass
            else:
                set_point(points[point_ref], direction, sections, logger, mqtt_client, route=route.ref)
        # iterate again to detect points:
        for point_ref, direction in route.points.items():
            # check if all points are set
            if points[point_ref].detection_boolean and points[point_ref].detection_status == direction:
                points_detected = True
            else:
                points_detected = False
                # break so that the next set of points doesn't set points_detected to true
                break

        # set section.routeset when route is setting or set
        for section in route.sections:
            sections[section].routestatus = "setting"
            sections[section].routeset = route.ref
            # set signals (check that route is clear already completed):
            # check points for that section are set and detected correctly
        if points_detected or not route.points.items():
            # set signal for that section in accordance with route signals to set
            for signal, aspects in route.signals.items():
                for aspect in aspects:
                    set_signal(signals[signal],
                               signals,
                               sections=sections,
                               points=points,
                               logger=logger,
                               aspect=aspect,
                               send_commands=False,
                               route=route.ref)
            # clear trigger once route fully set
            # route.set = True # not required?
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
            set_signal(signals[signal_ref], signals, sections=sections, points=points, logger=logger, aspect="danger")
    for point_ref, direction in route.points.items():
        if points[point_ref].routeset == route.ref:
            points[point_ref].routeset = None
            # unlock points if section not occupied
            if sections[points[point_ref].section].occstatus == 0:
                points[point_ref].unlocked = True
    route.setting = False


def set_plungers_clear(all_plungers_dict):
    for plunger_key, plunger in all_plungers_dict.items():
        plunger.status = 0


def set_ARS(automatic_route_setting, status):
    if status:
        automatic_route_setting.global_active = True
    else:
        automatic_route_setting.global_active = False


def check_route_availability_for_mqtt(routes, points, sections):
    # for every route, make not available if the section is occupied or route already set through:
    for routekey, route in routes.items():
        route.available = check_route_available(route, points, sections)


def set_from_mqtt(command, signals, sections, plungers, points, routes, triggers, logger, mqtt_client,
                  automatic_route_setting, axlecounters):
    mqtt_error = None
    command_l = command.topic.split("/")
    command_payload = str(command.payload.decode("utf-8"))

    def check_protecting_points(protecting_points):
        """returns true if points are set to protect section"""
        if protecting_points and (signal.ref in protecting_points):
            section_protecting_points = protecting_points[signal.ref]
            for point, direction in section_protecting_points.items():
                if direction != points[point].set_direction:
                    return True
        return False

    if command_l[0] != "set":
        return
    if command_l[1] == "axlecounter":
        if command_l[3] == "sessionupcount":
            axlecounters[command_l[2]].sessionupcount = int(command_payload)
        if command_l[3] == "sessiondowncount":
            axlecounters[command_l[2]].sessiondowncount = int(command_payload)
    if command_l[1] == "point":
        point = points[command_l[2]]
        # check this it is OK to set point:
        if sections[point.section].occstatus:
            mqtt_error = "Cannot set points when section is occupied"
        elif sections[point.section].routeset and sections[point.section].routestatus != "setting":
            mqtt_error = "Cannot set points when route is set through section"
        elif not point.unlocked:
            mqtt_error = "Trying to set points when locked"
        else:
            set_point(point=point, direction=command_payload, sections=sections, logger=logger, mqtt_client=mqtt_client)
    if command_l[1] == "signal":
        signal = signals[command_l[2]]
        aspect = command_payload
        for section in sections.values():
            if aspect == "danger":
                break
            if signal.ref in section.homesignal and not check_protecting_points(section.protecting_points):
                if section.occstatus and (aspect in main_proceed_aspects):
                    mqtt_error = "Cannot clear signal when section is occupied"
                for point in points.values():
                    if point.section == section.ref:
                        if not point.detection_boolean:
                            mqtt_error = "Cannot clear signal when section points not detected"
        for conflicting_signal in signal.conflicting_signals:
            if aspect == "danger":
                break
            if signals[conflicting_signal].aspect != {"danger"}:
                mqtt_error = "Cannot clear signal when conflicting signal set"
        if not mqtt_error:
            set_signal(signal=signal,
                       signals=signals,
                       sections=sections,
                       points=points,
                       logger=logger,
                       aspect=aspect,
                       send_commands=False)
    if command_l[1] == "route":
        if eval(command_payload):
            set_route(route=routes[command_l[2]],
                      sections=sections,
                      points=points,
                      signals=signals,
                      logger=logger,
                      mqtt_client=mqtt_client)
        if not eval(command_payload):
            cancel_route(route=routes[command_l[2]],
                         sections=sections,
                         points=points,
                         signals=signals,
                         triggers=triggers,
                         logger=logger,
                         mqtt_client=mqtt_client)
    if command_l[1] == "plunger":
        plungers[command_l[2]].status = command_payload
    if command_l[1] == "trigger":
        triggers[command_l[2]].triggered = eval(command_payload)
    if command_l[1] == "section" and command_l[3] == "occstatus":
        sections[command_l[2]].occstatus = int(command_payload)
        logger.info(str(command_l[2]) + " set to " + str(command_payload))
    if command_l[1] == "automatic_route_settting":
        set_ARS(automatic_route_setting, command_payload)
    return mqtt_error


def send_status_to_mqtt(axlecounters, signals, sections, plungers, points, routes, triggers, logger, mqtt_client,
                        mqtt_dict, automatic_route_setting, mqtt_error):
    mqtt_dict_old = mqtt_dict.copy()

    # set axlecounter dynamic variables
    for axlecounter in axlecounters.values():
        mqtt_dict[("error/axlecounter/comms/" + axlecounter.ref)] = axlecounter.comms_status
    # set signal dynamic variables
    for signal in signals.values():
        mqtt_dict[("report/signal/" + signal.ref + "/aspect")] = (",".join(signal.aspect))
        mqtt_dict[("error/signal/comms/" + signal.ref)] = signal.comms_status
    # set section dynamic variables
    for section in sections.values():
        mqtt_dict[("report/section/" + section.ref+"/occstatus")] = section.occstatus
        mqtt_dict[("report/section/" + section.ref+"/routeset")] = section.routeset
        mqtt_dict[("report/section/" + section.ref + "/routestatus")] = section.routestatus
    # set plunger dynamic variables
    for plunger in plungers.values():
        mqtt_dict[("error/plunger/comms/" + plunger.ref)] = plunger.comms_status
    # set point dynamic variables
    for point in points.values():
        mqtt_dict[("report/point/"+point.ref+"/set_direction")] = point.set_direction
        mqtt_dict[("report/point/"+point.ref+"/detection_status")] = point.detection_status
        mqtt_dict[("report/point/"+point.ref+"/detection_boolean")] = point.detection_boolean
        mqtt_dict[("report/point/"+point.ref+"/unlocked")] = point.unlocked
        mqtt_dict[("error/point/comms/" + point.ref)] = point.comms_status
    # set route dynamic variables
    for route in routes.values():
        route.available = check_route_available(route, points, sections)  # update route availabilty
        mqtt_dict[("report/route/"+route.ref+"/available")] = route.available
        mqtt_dict[("report/route/"+route.ref+"/setting")] = route.setting
    # set trigger dynamic variables
    for trigger in triggers.values():
        mqtt_dict[("report/trigger/"+trigger.ref+"/stored_request")] = trigger.stored_request
    mqtt_dict["report/automatic route setting"] = automatic_route_setting.global_active
    if mqtt_error:
        mqtt_dict["error/MQTT_Command"] = mqtt_error

    # send everything, only if anything has changed
    if mqtt_dict != mqtt_dict_old:
        for key, val in mqtt_dict.items():
            mqtt_client.publish(key, val)
