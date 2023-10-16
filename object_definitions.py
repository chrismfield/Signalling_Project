# ---------Assets, Sections and Route instances --------------

sectiondict = {}  # dictionary for containing instances of sections
ACdict = {}  # dictionary for containing instances of axlecounters
signaldict = {}  # dictionary for containing instances of Signals
plungerdict = {}  # dictionary for containing instances of Plungers
pointdict = {}  # dictionary for containing instances of Points
routedict = {}  # dictionary for containing instances of Routes

class AxleCounter:
    """Axle-counter object containing static and dynamic variables"""
    instances = {}
    def __init__(self, mode, address, ref, description):
        #Static variables
        self.mode = mode  # mode = axlecount, simple trigger or directional trigger
        self.address = address  # address
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        #Dynamic variables
        self.upcount = 0
        self.downcount = 0


class Signal:
    """Signal object containing static and dynamic variables"""
    instances = {}
    def __init__(self, sigtype, address, ref, description, availableaspects,
                 directionindicator, dangerreg, cautionreg, clearreg, callingonreg,
                 bannerreg, route1reg, route2reg, route3reg, route4reg, route5reg, route6reg):
        #static variables
        self.sigtype = sigtype  # mode = Semaphore or coulour light
        self.address = address  # address
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
    def __init__(self, mode, address, ref, description, section=""):
        #static variables
        self.address = address  # address
        self.detection_mode = mode  # mode: with detection or without detection
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.section = section
        #dynamic variables
        self.set_direction = ""  # set status
        self.detection = ""  # detection status
        self.unlocked = False


class Route:
    """Route object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description, mode, sections, points, signals, priority):
        #static variables
        self.mode = mode  # mode: with detection or without detection
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.sections = sections  # ordered list of sections
        self.points = points  # ordered list of points to set
        self.signals = signals  # ordered list of signals to set. Each signal to be a list of aspects of that signal to set
        self.priority = priority  # priority number (change this to be an integer)
        self.trigger = []  # list of triggers for route - section occupation, section non-occupation, plunger, lever etc.
        # Need to include an option for whether the trigger ovverides existing routes or not.
        # dynamic variables
        self.available = False
        self.set = False

class Trigger:
    """Trigger object containing static and dynamic variables"""
    def __init__(self, override, section, sectionclear, plunger, lever,  timer, MQTT):
        #static variables
        self.override = override
        self.section = section
        self.sectionclear = sectionclear
        self.plunger = plunger
        self.lever = lever
        self.timer = timer
        self.MQTT = MQTT
        #dyanamic variables
        self.triggered = False5

class Lever:
    instances = {}
    # for later on!
    pass
