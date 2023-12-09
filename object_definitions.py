import minimalmodbus

# ---------Assets, Sections and Route instances --------------

class AxleCounter:
    """Axle-counter object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description):
        #Static variables
        self.mode = mode  # mode = axlecount, simple trigger or directional trigger
        self.address = address  # address
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        self.board_index = 0 # TO DO get and set these in json file
        self.normal_coil = 22 # TO DO get and set these in json file
        self.reverse_coil = 23 # TO DO get and set these in json file
        #Dynamic variables
        self.upcount = 0
        self.downcount = 0


class Signal:
    """Signal object containing static and dynamic variables"""
    instances = {}
    def __init__(self, sigtype, address, ref, description, availableaspects,
                 directionindicator, dangerreg, cautionreg, clearreg, callingonreg,
                 bannerreg, route1reg, route2reg, route3reg, route4reg, route5reg, route6reg, board_index=0):
        #static variables
        self.sigtype = sigtype  # mode = Semaphore or coulour light
        self.address = address  # address
        self.board_index = board_index
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        self.availableaspects = availableaspects  # available aspects
        self.directionindicator = directionindicator
        self.dangerreg = dangerreg
        self.cautionreg = cautionreg
        self.clearreg = clearreg
        self.callingonreg = callingonreg
        self.bannerreg = bannerreg
        self.route1reg = route1reg
        self.route2reg = route2reg
        self.route3reg = route3reg
        self.route4reg = route4reg
        self.route5reg = route5reg
        self.route6reg = route6reg
        # dynamic variables
        self.illumination = "On"  # night illumination mode
        self.aspect = "0"  # current aspect


class Section:
    """Section object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description, mode, inctrig, dectrig, homesignal, conflictingsections):
        #static variables
        self.ref = ref  # Freetext Ref
        self.description = description  # Freetext description
        # add section attributes - this comes after adding the other assets as these can be referenced by a section instance
        self.mode = mode  # mode: axlecounter, trackcircuit, magnet (input trigger) or RFID
        self.inctrig = inctrig  # increment triggers
        self.dectrig = dectrig  # decrement triggers
        self.homesignal = homesignal  # protecting signals
        self.conflictingsections = conflictingsections
        #dynamic variables
        self.occstatus = 0  # occupation status
        self.routeset = False #set to true if route is set through this section
        self.routestatus = ""  # availability status


class Plunger:
    """Plunger object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description, register):
        #static variables
        self.mode = mode  # mode of operation, request store or no request store.
        self.address = address  # address
        self.ref = ref  # Freetext Referece
        self.description = description  # freetext description
        self.register = register  # register address
        #dynamic variables
        self.status = 0


class Point:
    """Point object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description, section="", normal_coil=22, reverse_coil=23, board_index=0):
        #static variables
        self.mode = mode
        self.address = address  # address
        self.detection_mode = mode  # mode: with detection or without detection
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        if not section:
            self.section = ""
        else:
            self.section = section
        self.board_index = board_index
        self.normal_coil = normal_coil
        self.reverse_coil = reverse_coil
        self.network = "" # get this from config file
        #self.slave = minimalmodbus.Instrument(self.network, self.address)
        #dynamic variables
        self.set_direction = ""  # set status
        self.detection = ""  # detection status
        self.unlocked = False


    def set_point(self, direction):
        if direction == "normal":
            try:
                self.slave.write_bit(self.reverse_coil, 0)
                self.slave.write_bit(self.normal_coil, 1)
                return True
            except ValueError:
                status = "Comms failure" # add details and logging
                return False
        if direction == "reverse":
            try:
                self.slave.write_bit(self.normal_coil, 0)
                self.slave.write_bit(self.reverse_coil, 1)
                return True
            except ValueError:
                status = "Comms failure" # add details and logging
                return False

class Route:
    """Route object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description, mode, sections, points, signals, priority):
        #static variables
        self.mode = mode  # mode: store request (=1) or not store request (=0)
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.sections = sections  # ordered list of sections
        self.points = points  # ordered list of points to set - dictionary of points and direction to set?
        self.signals = signals  # ordered dictionary of signals to set. Each signal to be a list of aspects of that signal to set
        self.priority = priority  # priority number (change this to be an integer)
        self.trigger = []  # list of triggers for route - section occupation, section non-occupation, plunger, lever etc.
        # Need to include an option for whether the trigger ovverides existing routes or not.
        # dynamic variables
        self.available = False
        self.set = False
        self.requested = False

class Trigger:
    """Trigger object containing static and dynamic variables"""
    def __init__(self, ref, description = None, override=False, sections_occupied=None, sections_clear=None, plungers=None, lever=None,
                 timer=None, MQTT=None, routes_to_set=None, routes_to_cancel=None, priority=10, store_request = 0):
        #static variables
        self.ref = ref
        self.description = description
        self.override = override
        self.sections_occupied = sections_occupied
        self.sections_clear = sections_clear
        self.plungers = plungers
        self.lever = lever
        self.timer = timer
        self.MQTT = MQTT
        self.routes_to_set = routes_to_set
        self.routes_to_cancel = routes_to_cancel
        self.priority = priority
        self.store_request = store_request
        #dyanamic variables
        self.triggered = False

class Lever:
    instances = {}
    # for later on!
    pass
