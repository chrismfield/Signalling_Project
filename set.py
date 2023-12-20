from custom_exceptions import *

def set_point(point, direction, sections, logger):
    # don't move points if section is occupied
    if sections[point.section].occstatus:
        logger.critical("Cannot set points when section is occupied")
        raise InterlockingError("Cannot set points when section is occupied")
    else:
        if sections[point.section].routeset:
            logger.critical("Cannot set points when route is set through section")
            raise InterlockingError("Cannot set points when route is set through section")
        else:
            comms_status = ""
            if direction == "normal":
                try:
                    point.slave.write_bit(point.reverse_coil, 0)
                    point.slave.write_bit(point.normal_coil, 1)
                    comms_status = " OK"
                    logger.info(point.ref + " set normal")
                except ValueError:
                    comms_status = " Comms failure"
            if direction == "reverse":
                try:
                    point.slave.write_bit(point.normal_coil, 0)
                    point.slave.write_bit(point.reverse_coil, 1)
                    comms_status = " OK"
                    logger.info(point.ref + " set reverse")
                except ValueError:
                    comms_status = " Comms failure"

            if point.comms_status != comms_status:
                logger.error(point.ref + comms_status)
                point.comms_status = comms_status

def set_signal(signal, sections, logger, aspect=None, nextsignal =None): #arguments are signal object and aspect as string
    #don't set signal if section is occupied
    main_proceed_aspects = ["clear", "caution", "doublecaution"]
    old_aspects = signal.aspect
    if aspect in main_proceed_aspects:
        for section in sections.values():
            if signal.ref in section.homesignal:
                if section.occstatus:
                    logger.critical("Cannot clear signal when section is occupied")
                    raise InterlockingError("Cannot clear when section is occupied")
    comms_status = ""
    #clear other aspects if set to danger
    if aspect == "danger":
        signal.aspect.clear()
        signal.aspect.add(aspect)
    elif aspect:
        #update class instance with aspect instruction
        signal.aspect.add(aspect)
        if aspect in main_proceed_aspects:
            signal.aspect.discard("danger")
    #set aspects through slaves and lookups

    for set_aspect in signal.aspect:

        if set_aspect == "danger":
            try:
                signal.slave.write_bit(signal.dangerreg, 1)
                signal.slave.write_bit(signal.cautionreg, 0)
                signal.slave.write_bit(signal.clearreg, 0)
                signal.slave.write_bit(signal.callingonreg, 0)
                signal.slave.write_bit(signal.bannerreg, 0)
                signal.slave.write_bit(signal.route1reg, 0)
                signal.slave.write_bit(signal.route2reg, 0)
                signal.slave.write_bit(signal.route3reg, 0)
                signal.slave.write_bit(signal.route4reg, 0)
                signal.slave.write_bit(signal.route5reg, 0)
                signal.slave.write_bit(signal.route6reg, 0)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "caution":
            try:
                signal.slave.write_bit(signal.dangerreg, 0)
                signal.slave.write_bit(signal.cautionreg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "doublecaution":
            try:
                signal.slave.write_bit(signal.dangerreg, 0)
                signal.slave.write_bit(signal.cautionreg, 1)
                signal.slave.write_bit(signal.doublecautionreg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "clear":
            #test if next aspect is a main proceed aspect
            if [True for MPA in main_proceed_aspects if MPA in nextsignal.aspect]:
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    signal.slave.write_bit(signal.cautionreg, 0)
                    signal.slave.write_bit(signal.doublecautionreg, 0)
                    signal.slave.write_bit(signal.clearreg, 1)
                    comms_status = " OK"
                except OSError:
                    comms_status = " Comms failure"
            #if not, apply a caution aspect
            else:
                # TODO add in check of available aspects to understand if possible to clear caution aspect
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    signal.slave.write_bit(signal.cautionreg, 1)
                    comms_status = " OK"
                except OSError:
                    comms_status = " Comms failure"
        if set_aspect == "callingon":
            try:
                signal.slave.write_bit(signal.dangerreg, 1)
                signal.slave.write_bit(signal.callingon, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "bannerreg":
            try:
                signal.slave.write_bit(signal.bannerreg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "route1":
            try:
                signal.slave.write_bit(signal.route1reg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "route2":
            try:
                signal.slave.write_bit(signal.route2reg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "route3":
            try:
                signal.slave.write_bit(signal.route3reg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "route4":
            try:
                signal.slave.write_bit(signal.route4reg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "route5":
            try:
                signal.slave.write_bit(signal.route5reg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if set_aspect == "route6":
            try:
                signal.slave.write_bit(signal.route6reg, 1)
                comms_status = " OK"
            except OSError:
                comms_status = " Comms failure"
        if signal.comms_status != comms_status:
            logger.error(signal.ref + comms_status)
            signal.comms_status = comms_status
        if signal.aspect != old_aspects:
            logger.info(signal.ref + " aspects requested " + str(signal.aspect))


def check_route_available(route, points, sections):
    for route_section in route.sections:
        if sections[route_section].routeset:
            return False
        if sections[route_section].occstatus:
            return False # don't set if route is occupied
        if sections[sections[route_section].conflictingsections].routeset:
            return False
        if sections[sections[route_section].conflictingsections].occstatus:
            return False
    for point in route.points:
        if not points[point].unlocked:
            return False
    return True
def set_route(route, sections, points, signals, logger):

    # check route is clear to set
    if check_route_available(route, points, sections):
        route.setting = True
        # set points - move to route setting iteration?
        points_detected = False
        for point_ref, direction in route.points.items():
            set_point(points[point_ref], direction, sections, logger)
            #check if all points are set
            if points[point_ref].detection_boolean:
                points_detected = True
            else:
                points_detected = False
                #this also prevents next points setting until previous points detected
                break
        # set section.routeset when route is setting or set
        for section in route.sections:
            sections[section].routeset = True
            # set signals (check that route is clear already completed):
            # check points for that section are set and detected correctly
        if points_detected:
            # set signal for that section in accordance with route signals to set
            for signal, aspects in route.signals.items():
                for aspect in aspects:
                    set_signal(signals[signal], sections=sections, logger=logger, aspect=aspect)
            # clear trigger once route fully set
            route.setting = False
    else:
        return "route not available"
def set_plungers_clear(all_plungers_dict):
    for plunger_key, plunger in all_plungers_dict.items():
        plunger.status = 0