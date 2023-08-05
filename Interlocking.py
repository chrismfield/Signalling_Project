from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import minimalmodbus
import pickle
import jsons
import os
import Comselector
import serial.tools.list_ports

RS485port = ""

# ---------Assets, Sections and Route instances --------------

sectiondict = {}  # dictionary for containing instances of sections
ACdict = {}  # dictionary for containing instances of axlecounters
signaldict = {}  # dictionary for containing instances of Signals
plungerdict = {}  # dictionary for containing instances of Plungers
pointdict = {}  # dictionary for containing instances of Points
routedict = {}  # dictionary for containing instances of Routes

windowdict = {}  # for containing all the windows associated with asset lists
framedict = {}  # for containing the frames that contain the lines
currentfile = "default.json"
occstatustkvar = {}  # dictionary for occstatus variable for tk window not to be pickled (StringVar's cant be pickled)
runvar = 0  # for defining whether system runs or not


class axlecounter:
    def __init__(self, mode, address, ref, description):
        self.mode = mode  # mode = axlecount, simple trigger or directional trigger
        self.address = address  # address
        self.ref = ref  # Freetext Reference
        self.description = description  # Freetext description
        self.upcount = 0
        self.downcount = 0


class signal:
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
    def __init__(self, mode, address, ref, description, register):
        self.mode = mode  # mode of operation, request store or no request store.
        self.address = address  # address
        self.ref = ref  # Freetext Referece
        self.description = description  # freetext description
        self.register = register  # register address
        self.status = 0


class point:
    def __init__(self, mode, address, ref, description):
        self.address = address  # address
        self.mode = mode  # mode: with detection or without detection
        self.ref = ref  # Freetext reference
        self.description = description  # Freetext description
        self.setstatus = ""  # set status
        self.detection = ""  # detection status


class route:
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


# ---------Setup Windows-------------
# main monitoring window:
def updatesections(root):  # use this to update the main monitoring window
    try:
        framedict["mainframe"].destroy()
    except:
        pass

    framedict["mainframe"] = ttk.Frame(root)
    framedict["mainframe"].grid(column=0, row=1)

    def mainline(i, key):
        global occstatustkvar
        occstatustkvar[key] = StringVar()
        ttk.Label(framedict["mainframe"], text="Section Ref:").grid(column=0, row=i, sticky=W)
        ttk.Label(framedict["mainframe"], text=key).grid(column=1, row=i)
        ttk.Label(framedict["mainframe"], text="Status: ").grid(column=2, row=i)  # add status variable in here.
        ttk.Label(framedict["mainframe"], textvariable=(occstatustkvar[key])).grid(column=3, row=i)

    i = 0
    for key in sectiondict:
        mainline(i, key)
        i += 1

# ---------------


# need to apply inputs, outputs and logic.
def check_all_ACs():
    """ get upcount and downcount from all axlecounters and store them in their instance"""
    for ACkey, ACinstance in ACdict.items():
        try:
            slave = minimalmodbus.Instrument(RS485port, ACinstance.address)
            ACinstance.upcount, ACinstance.downcount = slave.read_registers(13,
                                                                            2)  # register number, number of registers
            slave.write_register(13, 0, functioncode=6)  # register number, value
            slave.write_register(14, 0, functioncode=6)  # register number, value
            status = "OK"

        except:
            ACinstance.upcount, ACinstance.downcount = 0, 0  # reset these variables to zero if no comms to avoid double counting
            status = "Comms failure with " + ACinstance.ref

        finally:
            if status != "OK":
                print(status)
    return


def check_all_plungers():
    """ get status from all plungers and store in their instance"""
    for plungerkey, plungerinstance in plungerdict.items():
        try:
            slave = minimalmodbus.Instrument(RS485port, plungerinstance.address)
            plungerinstance.status = slave.read_bit(plungerinstance.register, 1)  # register number, number of registers
            slave.write_bit(plungerinstance.register, 0)  # register number,value
            status = "OK"
        except:
            plungerinstance.status = 0  # reset these variables to zero if no comms to avoid double counting
            status = "Comms failure with " + plungerinstance.ref

        finally:
            if status != "OK":
                print(status)
    return

    pass  # -----------need to implement -------------


def section_update():
    global occstatustkvar
    for sectionkey, section in sectiondict.items():  # increment or decrement
        for trigger in section.inctrig:  # note each trigger consists of a list: axlecounter and direction - "upcount" or "downcount"
            if trigger[1] == "upcount":
                section.occstatus += ACdict[trigger[0]].upcount
                section.occstatus -= ACdict[trigger[0]].downcount
            if trigger[1] == "downcount":
                section.occstatus += ACdict[trigger[0]].downcount
                section.occstatus -= ACdict[trigger[0]].upcount
        for trigger in section.dectrig:
            if trigger[1] == "upcount":
                section.occstatus -= ACdict[trigger[0]].upcount
                section.occstatus += ACdict[trigger[0]].downcount
            if trigger[1] == "downcount":
                section.occstatus -= ACdict[trigger[0]].downcount
                section.occstatus += ACdict[trigger[0]].upcount
                # set the TK variable to autoupdate GUI
        occstatustkvar[sectionkey].set(section.occstatus)
        # set homesignal to danger if section occupied - might need to repeat after any routesetting and before output. 
        for homesignal in section.homesignal:
            if section.occstatus > 0:
                signaldict[homesignal].aspect = 0
    return


def check_points():
    pass  # -------------need to implement-----------


# Check route triggers
# Set routes (will need to iterate this to wait for point detection)
# check conflicting sections
# apply interlocking doublecheck

# Send outputs to relevant points and all signals


# ---------------

def process(root):
    if runvar == 1:
        check_all_ACs()
        check_points()
        check_all_plungers()
        section_update()
        root.after(500, lambda: process(root))
        return


def comm_chooser(master):
    mycomlist = ([comport.device for comport in serial.tools.list_ports.comports()])

    commwindow = Toplevel(master, takefocus=True)
    listbox = Listbox(commwindow)
    listbox.pack()

    for item in mycomlist:
        listbox.insert(END, item)

    def callback():
        global RS485port
        RS485port = listbox.get(listbox.curselection())
        commwindow.destroy()

    b = Button(commwindow, text="OK", command=callback)
    b.pack()



def saveaslayoutjson(root, currentfile, saveas):
    if saveas == True:
        json_out = filedialog.asksaveasfile(mode='w', defaultextension=".json")
        if json_out is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
    else:
        json_out = open(currentfile, 'w')
    infradata = {"Sections": sectiondict, "AxleCounters": ACdict, "Signals": signaldict, "Plungers": plungerdict,
                 "Points": pointdict, "Routes": routedict}
    json_out.write(jsons.dumps(infradata))
    json_out.close()  # close the file
    print("saved")


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
    updatesections(root)
    root.title("Section Monitor - " + currentfile)
    pass



def control_frame(root):
    runvartk = IntVar()

    def run_system():
        global runvar
        runvar = runvartk.get()
        if runvar == 1:
            process(root)

    ControlFrame = ttk.Frame(root)  # create frame for run/stop control
    ControlFrame.grid(column=0, row=0, sticky=W)
    Checkbutton(ControlFrame, text="Run System", command=run_system, variable=runvartk, anchor=W).grid(row=0, column=0,
                                                                                                       sticky=W)


def main():
    root = Tk()
    control_frame(root)
    SectionMonitor = ttk.Frame(root)  # create main window for monitoring sections
    SectionMonitor.grid(column=0, row=1, sticky=W)
    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open json...", command=lambda: loadlayoutjson(root, False))
    filemenu.add_command(label="Save As json...", command=lambda: saveaslayoutjson(root, currentfile, True))
    filemenu.add_command(label="Save", command=lambda: saveaslayoutjson(root, currentfile, False))
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=lambda: root.destroy())
    menubar.add_cascade(label="File", menu=filemenu)
    setupmenu = Menu(menubar, tearoff=0)
    setupmenu.add_command(label="Comm Port", command=lambda: comm_chooser(root))
    menubar.add_cascade(label="Setup", menu=setupmenu)
    assetmenu = Menu(menubar, tearoff=0)
    assetmenu.add_command(label="Axle counters", command=lambda: AClist(root))
    assetmenu.add_command(label="Plungers", command=lambda: plungerlist(root))
    assetmenu.add_command(label="Signals", command=lambda: signallist(root))
    assetmenu.add_command(label="Points", command=lambda: pointlist(root))
    menubar.add_cascade(label="Assets", menu=assetmenu)
    sectionmenu = Menu(menubar, tearoff=0)
    sectionmenu.add_command(label="Manage sections", command=lambda: sectionlist(root))
    menubar.add_cascade(label="Section", menu=sectionmenu)
    routemenu = Menu(menubar, tearoff=0)
    routemenu.add_command(label="Manage routes", command=lambda: route_list(root))
    menubar.add_cascade(label="Route", menu=routemenu)
    # display the menu
    root.config(menu=menubar)
    root.geometry("1000x1000")  # Width x Height of main window
    loadlayoutjson(root, True)
    root.title("Section Monitor - " + currentfile)
    root.mainloop()  # run infitite Tk loop


if __name__ == '__main__':
    main()

# Next Jobs
# Configurable direction on axlecounter triggers
# More work on routes interface - set routes but move route triggers into route scheduling?
# Get all the logic to work
# Pickle Com port selection - put in an ini file?
# re-work Pickling to allow differing version compatibility - perhaps put everything in one dictionary of dictionaries and pickle that.
# Route scheduling? This could be used to cycle routes on a trigger.
