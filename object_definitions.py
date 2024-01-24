import minimalmodbus

# ---------Assets, Sections and Route instances --------------

class AxleCounter:
    """Axle-counter object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description, slave=None):
        #Static variables
        self.mode = mode  # mode = axlecount, simple trigger or directional trigger
        self.address = address  # address
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        self.board_index = 0 # TODO get and set these in json file
        self.upcount_reg = 13 # TODO get and set these in json file
        self.downcount_reg = 14 # TODO get and set these in json file
        self.slave = slave
        self.network = "network_1" # TODO set this in json file using infrastructure editor
        #Dynamic variables
        self.upcount = 0
        self.downcount = 0
        self.comms_status = ""


class Signal:
    """Signal object containing static and dynamic variables"""
    instances = {}
    def __init__(self, sigtype, address, ref, description, availableaspects,
                 directionindicator, dangerreg, cautionreg, clearreg, callingonreg,
                 bannerreg, route1reg, route2reg, route3reg, route4reg, route5reg, route6reg, doublecaution=None,
                 nextsignal=None, board_index=0, slave=None, dynamic_variables = True):
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
        self.doublecaution = doublecaution # TODO set this in json file using infrastructure editor
        self.clearreg = clearreg
        self.callingonreg = callingonreg
        self.bannerreg = bannerreg
        self.route1reg = route1reg
        self.route2reg = route2reg
        self.route3reg = route3reg
        self.route4reg = route4reg
        self.route5reg = route5reg
        self.route6reg = route6reg
        self.nextsignal = nextsignal # TODO set this in json file using infrastructure editor
        self.network = "network_1" # TODO set this in json file using infrastructure editor
        self.slave = slave
        # dynamic variables
        if dynamic_variables: # this prevents infrastructure editor from creating these variables. useful as set
                                # (for aspect) is not supported in json and gets translated into a list
            self.illumination = "On"  # night illumination mode
            self.aspect = {"danger"}  # set of current aspects
            self.comms_status = ""


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
        self.previousoccstatus = 0


class Plunger:
    """Plunger object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description, register, slave=None):
        #static variables
        self.mode = mode  # mode of operation, request store or no request store.
        self.address = address  # address
        self.ref = ref  # Freetext Referece
        self.description = description  # freetext description
        self.register = register  # register address
        self.network = "network_1"  # TODO set this in json file using infrastructure editor
        self.slave = slave
        #dynamic variables
        self.status = 0
        self.comms_status = ""


class Point:
    """Point object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description, section="", normal_coil=22, reverse_coil=23, board_index=0, slave=None):
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
        self.network = "network_1"  # TODO set this in json file using infrastructure editor
        self.slave = slave
        #self.slave = minimalmodbus.Instrument(self.network, self.address)
        #dynamic variables
        self.set_direction = ""  # set status
        self.detection_status = ""  # detection status
        self.detection_boolean = False
        self.unlocked = True
        self.comms_status = ""

class Route:
    """Route object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description, mode, sections, points, signals, priority):
        #static variables
        self.mode = mode  # mode: store request (=1) or not store request (=0)
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.sections = sections  # ordered list of sections
        self.points = points  # dictionary of points and direction to set
        self.signals = signals  # ordered dictionary of signals to set. Each signal to be a list of aspects of that signal to set
        # dynamic variables
        self.available = False
        self.setting = False
        self.set = False

class Trigger:
    """Trigger object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description = None, override=False, sections_occupied=[], sections_clear=[], plungers=[], lever=None,
                 timer=None, MQTT=None, routes_to_set=[], routes_to_cancel=[], priority=10, store_request = False, conditions = ["True"], trigger_expressions = []):
        #static variables
        self.ref = ref
        self.description = description
        self.override = override
        self.sections_occupied = sections_occupied
        self.sections_clear = sections_clear
        self.plungers = plungers
        self.lever = lever
        self.timer = timer
        self.routes_to_set = routes_to_set
        self.routes_to_cancel = routes_to_cancel
        self.priority = priority
        self.store_request = store_request
        self.conditions = conditions
        self.trigger_expressions = trigger_expressions
        #dyanamic variables
        self.triggered = False
        self.stored_request = False

class Lever:
    instances = {}
    # for later on!
    pass
