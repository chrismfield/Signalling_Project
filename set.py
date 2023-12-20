def set_point(point, direction):
    # TODO check points section not occupied or set before moving points. "setting" is OK
    if direction == "normal":
        try:
            point.slave.write_bit(point.reverse_coil, 0)
            point.slave.write_bit(point.normal_coil, 1)
            return True
        except ValueError:
            status = "Comms failure" # add details and logging
            return False
    if direction == "reverse":
        try:
            point.slave.write_bit(point.normal_coil, 0)
            point.slave.write_bit(point.reverse_coil, 1)
            return True
        except ValueError:
            status = "Comms failure" # TODO add details and logging
            return False

def set_signal(signal, aspect=None, nextsignal =None): #arguments are signal object and aspect as string
    #clear other aspects if set to danger
    if aspect == "danger":
        signal.aspect.clear()
        signal.aspect.append(aspect)
    elif aspect:
        #update class instance with aspect instruction
        signal.aspect.append(aspect)
    #set aspects through slaves and lookups

    for aspect in signal.aspect:
        main_proceed_aspects = ["clear", "caution", "doublecaution"]
        if aspect == "danger":
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
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "caution":
            try:
                signal.slave.write_bit(signal.dangerreg, 0)
                signal.slave.write_bit(signal.cautionreg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "doublecaution":
            try:
                signal.slave.write_bit(signal.dangerreg, 0)
                signal.slave.write_bit(signal.cautionreg, 1)
                signal.slave.write_bit(signal.doublecautionreg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "clear":
            #test if next aspect is a main proceed aspect
            if [True for MPA in main_proceed_aspects if MPA in nextsignal.aspect]:
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    signal.slave.write_bit(signal.cautionreg, 0)
                    signal.slave.write_bit(signal.doublecautionreg, 0)
                    signal.slave.write_bit(signal.clearreg, 1)
                except ValueError:
                    status = "Comms failure" # TODO add details and logging
            #if not, apply a caution aspect
            else:
                try:
                    signal.slave.write_bit(signal.dangerreg, 0)
                    signal.slave.write_bit(signal.cautionreg, 1)
                except ValueError:
                    status = "Comms failure"  # TODO add details and logging
        if aspect == "callingon":
            try:
                signal.slave.write_bit(signal.dangerreg, 1)
                signal.slave.write_bit(signal.callingon, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "bannerreg":
            try:
                signal.slave.write_bit(signal.bannerreg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "route1":
            try:
                signal.slave.write_bit(signal.route1reg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "route2":
            try:
                signal.slave.write_bit(signal.route2reg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "route3":
            try:
                signal.slave.write_bit(signal.route3reg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "route4":
            try:
                signal.slave.write_bit(signal.route4reg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "route5":
            try:
                signal.slave.write_bit(signal.route5reg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging
        if aspect == "route6":
            try:
                signal.slave.write_bit(signal.route6reg, 1)
            except ValueError:
                status = "Comms failure" # TODO add details and logging

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
        if not point.unlocked:
            return False
    return True
def set_route(route, sections, points, signals):

    # check route is clear to set
    if check_route_available(route, points, sections):
        route.setting = True
        # set points - move to route setting iteration?
        points_detected = False
        for point_ref, direction in route.points.items():
            set_point(points[point_ref], direction)
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
            for signal, aspect in route.signals.items():
                set_signal(signals[signal], aspect)
                # clear trigger once route fully set
            route.setting = False
    else:
        return "route not available"
def set_plungers_clear(all_plungers_dict):
    for plunger_key, plunger in all_plungers_dict.items():
        plunger.status = 0