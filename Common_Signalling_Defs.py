from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import minimalmodbus
import jsons
import os

RS485port = ""

# ---------Assets, Sections and Route instances --------------

runvar = 0  # for defining whether system runs or not


class axlecounter:
    ACdict = {}  # dictionary for containing instances of axlecounters
    def __init__(self, mode, address, ref, description):
        self.mode = mode  # mode = axlecount, simple trigger or directional trigger
        self.address = address  # address
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        self.upcount = 0
        self.downcount = 0


class signal:
    signaldict = {}  # dictionary for containing instances of Signals
    def __init__(self, sigtype, address, ref, description, availableaspects,
                 directionindicator, dangerreg, cautionreg, clearreg, callingonreg,
                 bannerreg, route1reg, route2reg, route3reg, route4reg, route5reg, route6reg):
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
        self.illumination = "On"  # night illumination mode
        self.aspect = "0"  # current aspect


class section:
    sectiondict = {}  # dictionary for containing instances of sections
    def __init__(self, ref, description, mode, inctrig, dectrig, homesignal, conflictingsections):
        self.ref = ref  # Freetext Ref
        self.description = description  # Freetext description
        # add section attributes - this comes after adding the other assets as these can be referenced by a section instance
        self.mode = mode  # mode: axlecounter, trackcircuit, magnet (input trigger) or RFID
        self.inctrig = inctrig  # increment triggers
        self.dectrig = dectrig  # decrement triggers
        self.homesignal = homesignal  # protecting signals
        self.conflictingsections = conflictingsections
        self.occstatus = 0  # occupation status
        self.routestatus = ""  # availability status


class plunger:
    plungerdict = {}  # dictionary for containing instances of Plungers
    def __init__(self, mode, address, ref, description, register):
        self.mode = mode  # mode of operation, request store or no request store.
        self.address = address  # address
        self.ref = ref  # Freetext Referece
        self.description = description  # freetext description
        self.register = register  # register address
        self.status = 0


class point:
    pointdict = {}  # dictionary for containing instances of Point
    def __init__(self, mode, address, ref, description):
        self.address = address  # address
        self.mode = mode  # mode: with detection or without detection
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.setstatus = ""  # set status
        self.detection = ""  # detection status


class route:
    routedict = {}  # dictionary for containing instances of Routes
    def __init__(self, ref, description, mode, sections, points, signals, priority):
        self.mode = mode  # mode: with detection or without detection
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.sections = sections  # ordered list of sections
        self.points = points  # ordered list of points to set
        self.signals = signals  # ordered list of signals to set. Each signal to be a list of aspects of that signal to set
        self.priority = priority  # priority number (change this to be an integer)
        self.trigger = []  # list of triggers for route - section occupation, section non-occupation, plunger, lever etc.
        # Need to include an option for whether the trigger ovverides existing routes or not.


class lever:
    # for later on!
    pass


# load infrastructure database
def loadlayoutjson(root, loaddefault):
    global sectiondict
    global ACdict
    global signaldict
    global plungerdict
    global pointdict
    global routesdict
    global currentfile
    global RS485port

    if loaddefault == False:
        json_in = filedialog.askopenfile(mode='rb', defaultextension=".json")
        if json_in is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
    else:
        json_in = open("default.json")
    jsoninfradata = jsons.loads(json_in.read()) # turns file contents into a dictionary of the asset dictionaries
    jsonsectiondict = jsons.load(jsoninfradata["Sections"], dict)  #Strips into seperate assets dicts
    jsonACdict = jsons.load(jsoninfradata["AxleCounters"], dict)
    jsonsignaldict = jsons.load(jsoninfradata["Signals"], dict)
    jsonplungerdict = jsons.load(jsoninfradata["Plungers"], dict)
    jsonpointdict = jsons.load(jsoninfradata["Points"], dict)
    jsonroutesdict = jsons.load(jsoninfradata["Routes"], dict)
    for x in jsonsectiondict.keys(): # for each instance of an asset, turns the dict back into the class instance and adds to the global dict of those assets
        sectiondict[x] = jsons.load(jsonsectiondict[x], section)
    for x in jsonACdict.keys():
        ACdict[x] = jsons.load(jsonACdict[x], axlecounter)
    for x in jsonsignaldict.keys():
        signaldict[x] = jsons.load(jsonsignaldict[x], signal)
    for x in jsonplungerdict.keys():
        plungerdict[x] = jsons.load(jsonplungerdict[x], plunger)
    for x in jsonpointdict.keys():
        pointdict[x] = jsons.load(jsonpointdict[x], point)
    for x in jsonroutesdict.keys():
        routesdict[x] = jsons.load(jsonroutesdict[x], route)
    #    RS485port =
    currentfile = os.path.basename(json_in.name)
    print("loadnow")
