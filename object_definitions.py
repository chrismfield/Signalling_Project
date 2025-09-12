import minimalmodbus

# ---------Assets, Sections and Route instances --------------
class InterfaceObject:
    def __init__(self, network, address, ref, description, slave = None):
        self.network = network
        self.address = address
        self.ref = ref
        self.description = description
        self.slave = slave
        self.comms_status = ""

class TrackCircuit(InterfaceObject):
    """Track Circuit object containing static and dynamic variables"""
    instances = {}
    def __init__(self, network, address, ref, description, slave=None, registers=None, mode="self-latching"):
        super().__init__(network, address, ref, description, slave)
        self.registers = registers #coil registers that activate the track circuit e.g. {"self-latching":[1,2] "latch":[3], "unlatch":[4]}
        self.mode = mode #self-latching or non-latching"
        self.occstatus = False #TODO should this be true by default? It would create a lot of trains.


class TreadlePad(InterfaceObject):
    """Treadle Pad or Reed Switch object containing static and dynamic variables"""
    instances = {}
    def __init__(self, network, address, ref, description, slave=None, registers=None, mode="self-latching"):
        super().__init__(network, address, ref, description, slave)
        self.registers = registers #coil registers that activate the track circuit e.g. {"self-latching":[1,2] "latch":[3], "unlatch":[4]}
        self.mode = mode #self-latching or non-latching"
        self.activated = False


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
                 nextsignal=None, board_index=0, slave=None, dynamic_variables=True, conflicting_signals=None):
        #static variables
        self.sigtype = sigtype  # mode = Semaphore or coulour light
        self.address = address  # address
        self.board_index = board_index
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        self.availableaspects = availableaspects  # available aspects
        self.conflicting_signals = [] if conflicting_signals is None else conflicting_signals
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
            self.routeset = None # set to the route ref when signal set


class Section:
    """Section object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description, mode, inctrig=None, dectrig=None, trackcircuits=None, homesignal=None, conflictingsections=None, protecting_points=None):
        #static variables
        self.ref = ref  # Freetext Ref
        self.description = description  # Freetext description
        # add section attributes - this comes after adding the other assets as these can be referenced by a section instance
        self.mode = mode  # mode: axlecounter, trackcircuit, treadlepad or RFID
        self.inctrig = inctrig  # increment triggers dict
        self.dectrig = dectrig  # decrement triggers dict
        self.trackcircuits = trackcircuits
        self.homesignal = homesignal  # protecting signals
        self.protecting_points = {} # dict of dict: homesignal: {point:direction, point:direction}
        self.conflictingsections = conflictingsections
        #dynamic variables
        self.occstatus = 0  # occupation status
        self.routeset = None #set to the route when set through this section
        self.routestatus = ""  # availability status
        self.previousoccstatus = 0
        self.axle_tolerance = None #default axle tolerance is as per config file
        self.trains = []


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
        self.routeset = None # set to the route when point set
        self.last_comms_time = 0

class Route:
    """Route object containing static and dynamic variables"""
    instances = {}
    def __init__(self, ref, description, sections, points, signals, priority):
        #static variables
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
    def __init__(self, ref, description = None, override=False, sections_occupied=None, sections_clear=None, plungers=None, lever=None,
                 timer=None, MQTT=None, routes_to_set=None, routes_to_cancel=None, priority=10, retain_request = False, conditions = None, trigger_expressions = None, trigger_special_actions = None):
        #static variables
        self.ref = ref
        self.description = description
        self.override = override
        self.sections_occupied = [] if sections_occupied is None else sections_occupied
        self.sections_clear = [] if sections_clear is None else sections_clear
        self.plungers = [] if plungers is None else plungers
        self.lever = lever
        self.timer = timer
        self.routes_to_set = [] if routes_to_set is None else routes_to_set
        self.routes_to_cancel = [] if routes_to_cancel is None else routes_to_cancel
        self.priority = priority
        self.retain_request = retain_request
        self.conditions = ["True"] if conditions is None else conditions
        self.trigger_expressions = [] if trigger_expressions is None else trigger_expressions
        self.trigger_special_actions = [] if trigger_special_actions is None else trigger_special_actions
        #dyanamic variables
        self.triggered = False
        self.stored_request = False

class Lever:
    instances = {}
    # for later on!
    pass

class AutomaticRouteSetting:
    global_active = True
    def __init__(self):
        pass

class Train:
    """Contains information about train"""
    instances = {}
    next_ID_counter = 0
    headcode_lookup = {}
    headcode_counter = "1C00"
    def __init__(self):
        self.ID = Train.next_ID_counter
        Train.next_ID_counter += 1
        self.ref = None
        self.RFID = {} # RFIDs to consist of UID of card as key and associated vehicle ID as value
        self.headcode = None
        self.locos = [None]
        self.carriages = [None]
        self.drivers = [None]
        self.guard = [None]
        self.routes = [None]
        self.mileage = 0
        self.berth_section = None
        self.journey_log = []

    @classmethod
    def find_by_berth(cls, berth_section):
        for train in cls.instances.values():
            if train.berth_section == berth_section:
                return train
