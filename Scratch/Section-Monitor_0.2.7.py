from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog
import minimalmodbus
import jsons
import json
import os
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


# section create/edit window:
def AddSection(root, existingref):
    def write_section(root):
        homeselection = []
        incselection = {}
        decselection = {}
        conflictselection = []
        for selected in inclistbox.curselection():
            incselection.update(inclistdict[selected])
        for selected in declistbox.curselection():
            decselection.update(declistdict[selected])
        for selected in homesiglistbox.curselection():
            homeselection.append(homesiglistbox.get(selected))
        for selected in conflictlistbox.curselection():
            conflictselection.append(conflictlistbox.get(selected))
        sectiondict[(sectionref.get())] = section(ref=sectionref.get(),
                                                  description=description.get(), mode=mode.get(),
                                                  inctrig=incselection, dectrig=decselection,
                                                  homesignal=homeselection, conflictingsections=conflictselection)
        updatesections(root)
        sectionlist(root)
        sectionsetupwin.destroy()
        print(sectiondict)

    sectionsetupwin = Toplevel(root, takefocus=True)  # create window for adding and managing sections
    sectionsetupwin.title("Section Setup")
    sectionsetupframe = ttk.Frame(sectionsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    sectionsetupframe.grid(column=0, row=0)

    sectionref = StringVar()  # variable for section reference
    description = StringVar()  # variable for description
    mode = IntVar()
    sectionref.set(existingref)

    try:
        description.set(sectiondict[existingref].description)
    except:
        pass
    try:
        mode.set(sectiondict[existingref].mode)
    except:
        pass


    ttk.Label(sectionsetupframe, text="Section ref:").grid(column=0, row=0, sticky=W, padx=10)
    ttk.Entry(sectionsetupframe, width=7, textvariable=sectionref).grid(column=1, row=0, sticky=W,
                                                                        pady=4)  # sectionref entry

    ttk.Label(sectionsetupframe, text="Section mode:").grid(column=0, row=2, sticky=W, padx=10, pady=10)
    Radiobutton(sectionsetupframe, text="Track Circuit", variable=mode, value=0).grid(column=1, row=2, sticky=W)
    Radiobutton(sectionsetupframe, text="Axle Counter", variable=mode, value=1).grid(column=2, row=2, sticky=W)
    Radiobutton(sectionsetupframe, text="Latching", variable=mode, value=2).grid(column=3, row=2, sticky=W)
    Radiobutton(sectionsetupframe, text="RFID Tracking", variable=mode, value=3).grid(column=4, row=2, sticky=W)

    ttk.Label(sectionsetupframe, text="Arrival triggers:").grid(column=0, row=3, sticky=W, pady=4, padx=10)
    incframe = ttk.Frame(sectionsetupframe)
    incframe.grid(column=1, row=3, columnspan=2)
    incscrollbar = Scrollbar(incframe)
    incscrollbar.pack(side=RIGHT, fill=Y)
    inclistbox = Listbox(incframe, selectmode=MULTIPLE, height=4)
    inclistbox.pack(pady=10)
    inclistbox.config(yscrollcommand=incscrollbar.set)
    incscrollbar.config(command=inclistbox.yview)
    inclistbox.configure(exportselection=False)

    #test code start
    #Create dictionary with integer keys; Values are then another dictionary with AxleCounter Key and Value as
    # "Upcount" and "Downcount alternately
    inclistdict = {}
    declistdict = {}
    x = 0
    for item in ACdict:
        inclistdict[x] = {item : "Upcount"}
        declistdict[x] = {item : "Upcount"}
        x += 1
        inclistdict[x] = {item: "Downcount"}
        declistdict[x] = {item: "Downcount"}
        x += 1
    #Populate Listbox with concatenated strings from this dictionary
    for key, val in inclistdict.items():
        for AC, Dir in val.items():
            inclistbox.insert(END, (AC+ " - " + Dir))
    #Set selection from previously defined / saved file
    try:
        for y in range(inclistbox.size()):
            for entry in inclistdict[y].items():
                if entry in sectiondict[existingref].inctrig.items():
                    inclistbox.selection_set(y)
    except:
        pass



    ttk.Label(sectionsetupframe, text="Departure triggers:").grid(column=0, row=4, sticky=W, pady=4, padx=10)
    decframe = ttk.Frame(sectionsetupframe)
    decframe.grid(column=1, row=4, columnspan=2)
    decscrollbar = Scrollbar(decframe)
    decscrollbar.pack(side=RIGHT, fill=Y)
    declistbox = Listbox(decframe, selectmode=MULTIPLE, height=4)
    declistbox.pack(pady=10)
    declistbox.config(yscrollcommand=decscrollbar.set)
    decscrollbar.config(command=declistbox.yview)
    declistbox.configure(exportselection=False)

    #Populate Listbox with concatenated strings from this dictionary
    for key, val in declistdict.items():
        for AC, Dir in val.items():
            declistbox.insert(END, (AC+ " - " + Dir))
    #Set selection from previously defined / saved file
    try:
        for y in range(declistbox.size()):
            for entry in declistdict[y].items():
                if entry in sectiondict[existingref].dectrig.items():
                    declistbox.selection_set(y)
    except:
        pass

    ttk.Label(sectionsetupframe, text="Protecting signals:").grid(column=0, row=5, sticky=W, pady=4, padx=10)
    homesigframe = ttk.Frame(sectionsetupframe)
    homesigframe.grid(column=1, row=5, columnspan=2)
    homesigscrollbar = Scrollbar(homesigframe)
    homesigscrollbar.pack(side=RIGHT, fill=Y)
    homesiglistbox = Listbox(homesigframe, selectmode=MULTIPLE, height=4)
    homesiglistbox.pack(pady=10)
    homesiglistbox.config(yscrollcommand=homesigscrollbar.set)
    homesigscrollbar.config(command=homesiglistbox.yview)
    homesiglistbox.configure(exportselection=False)

    for item in signaldict:
        homesiglistbox.insert(END, item)
    try:
        for x in range(homesiglistbox.size()):
            if homesiglistbox.get(x) in sectiondict[existingref].homesignal:
                homesiglistbox.selection_set(x)
    except:
        pass

    ttk.Label(sectionsetupframe, text="Conflicting sections:").grid(column=0, row=6, sticky=W, pady=4, padx=10)
    conflictframe = ttk.Frame(sectionsetupframe)
    conflictframe.grid(column=1, row=6, columnspan=2)
    conflictscrollbar = Scrollbar(conflictframe)
    conflictscrollbar.pack(side=RIGHT, fill=Y)
    conflictlistbox = Listbox(conflictframe, selectmode=MULTIPLE, height=4)
    conflictlistbox.pack(pady=10)
    conflictlistbox.config(yscrollcommand=conflictscrollbar.set)
    conflictscrollbar.config(command=conflictlistbox.yview)
    conflictlistbox.configure(exportselection=False)

    for item in sectiondict:
        conflictlistbox.insert(END, item)
    try:
        for x in range(conflictlistbox.size()):
            if conflictlistbox.get(x) in sectiondict[existingref].conflictingsections:
                conflictlistbox.selection_set(x)
    except:
        pass

    ttk.Label(sectionsetupframe, text="Section description:").grid(column=0, row=7, sticky=W, pady=4, padx=10)
    ttk.Entry(sectionsetupframe, width=70, textvariable=description).grid(column=1, columnspan=4, row=7,
                                                                          sticky=W)  # sectionref entry

    ttk.Button(sectionsetupframe, text="OK", command=lambda: write_section(root)).grid(column=4, row=10, sticky=E)


# section management list:
def sectionlist(parent):
    windowtype = "Section"

    def deletesection(key, parent):
        if messagebox.askyesno("Delete Section", "Delete " + windowtype + " " + key + " ?"):
            del sectiondict[key]
            sectionlistwindow(parent)
        pass

    def sectionlistwindow(parent):

        try:
            framedict[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create sectionlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try:  # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create sectionlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()

        def sectionline(key, posi, windowtype):
            if sectiondict[key].mode == 0:
                modedescription = "Track circuit"
            if sectiondict[key].mode == 1:
                modedescription = "Axle counter"
            if sectiondict[key].mode == 2:
                modedescription = "Latching"
            if sectiondict[key].mode == 3:
                modedescription = "RFID tracking"
            ttk.Label(framedict[windowtype], text="Section ref: " + key).grid(column=0, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Description: " + sectiondict[key].description).grid(column=5,
                                                                                                       row=posi,
                                                                                                       padx=10)
            ttk.Button(framedict[windowtype], text="Edit", command=lambda: AddSection(parent, key)).grid(column=6,
                                                                                                         row=posi)
            ttk.Button(framedict[windowtype], text="Delete", command=lambda: deletesection(key, parent)).grid(column=7,
                                                                                                              row=posi)

        posi = 0
        for key in sectiondict:  # populate frame with lines for each axlecounter
            sectionline(key, posi, windowtype)
            posi += 1

        ttk.Button(framedict[windowtype], text="Add section", command=lambda: AddSection(parent, "")).grid(column=0,
                                                                                                           columnspan=10,
                                                                                                           row=500,
                                                                                                           sticky=E)  # button to add an axlecounter

    sectionlistwindow(parent)  # Create the list window and frame


# ---------------


# need to add a delete section funcion at some point

def AddAC(parent, existingref):
    def WriteAC(parent):
        ref = ACref.get()
        description = ACdescription.get()
        mode = ACmode.get()
        address = ACaddress.get()
        ACdict[(ACref.get())] = axlecounter(mode, address, ref,
                                            description)  # add an instance of an axlecounter to the list, with all the parameters.
        AClist(parent)
        ACsetupwin.destroy()

    # create a new popup window to enter details into:
    ACsetupwin = Toplevel(parent, takefocus=True)
    ACsetupwin.title("Axle Counter Setup")
    ACsetupframe = ttk.Frame(ACsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    ACsetupframe.grid(column=0, row=0)

    # add in inputs for mode, address, ref and description

    ACref = StringVar()  # TK variable for ACref input
    ACref.set(existingref)  # collect any existing ref for editing
    ACaddress = IntVar()  # TK variable for AC address input
    ACdescription = StringVar()  # TK variable for AC description input
    ACmode = IntVar()  # mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger

    try:
        ACaddress.set(ACdict[existingref].address)  # collect existing
    except:
        pass
    try:
        ACdescription.set(ACdict[existingref].description)
    except:
        pass
    try:
        ACmode.set(ACdict[existingref].mode)
    except:
        pass

    ttk.Label(ACsetupframe, text="Axle Counter Ref:").grid(column=0, row=0, sticky=W)
    ttk.Entry(ACsetupframe, width=7, textvariable=ACref).grid(column=1, row=0, sticky=W)  # ACref entry

    ttk.Label(ACsetupframe, text="Axle Counter Address:").grid(column=0, row=1, sticky=W)
    ttk.Entry(ACsetupframe, width=7, textvariable=ACaddress).grid(column=1, row=1, sticky=W)  # AC address entry

    # add in mode selector
    ttk.Label(ACsetupframe, text="Axle Counter Mode:").grid(column=0, row=2, sticky=W)
    Radiobutton(ACsetupframe, text="Axle Count", variable=ACmode, value=0).grid(column=1, row=2)
    Radiobutton(ACsetupframe, text="Non-directional Trigger", variable=ACmode, value=1).grid(column=2, row=2)
    Radiobutton(ACsetupframe, text="Directional Trigger", variable=ACmode, value=2).grid(column=3, row=2)

    ttk.Label(ACsetupframe, text="Axle Counter Description:").grid(column=0, row=3, sticky=W)
    ttk.Entry(ACsetupframe, width=70, textvariable=ACdescription).grid(column=1, columnspan=4, row=3,
                                                                       sticky=W)  # ACref entry

    ttk.Button(ACsetupframe, text="OK", command=lambda: WriteAC(parent)).grid(column=4, row=10, sticky=E)


def AClist(parent):
    windowtype = "Axle Counter"

    def deleteAC(key, parent):
        if messagebox.askyesno("Delete Asset", "Delete " + windowtype + " " + key + " ?"):
            del ACdict[key]
            AClistwindow(parent)
        pass

    def AClistwindow(parent):

        try:
            framedict[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create AClistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try:  # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create AClistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()

        def ACline(key, posi, windowtype):
            if ACdict[key].mode == 0:
                modedescription = "Axlecount"
            if ACdict[key].mode == 1:
                modedescription = "Non-directional trigger"
            if ACdict[key].mode == 2:
                modedescription = "Directional trigger"
            ttk.Label(framedict[windowtype], text="Axle Counter Ref: " + key).grid(column=0, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Address: ").grid(column=1, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text=ACdict[key].address).grid(column=2, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Mode: " + modedescription).grid(column=3, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Description: " + ACdict[key].description).grid(column=4, row=posi,
                                                                                                  padx=10)
            ttk.Button(framedict[windowtype], text="Edit", command=lambda: AddAC(parent, key)).grid(column=5, row=posi)
            ttk.Button(framedict[windowtype], text="Delete", command=lambda: deleteAC(key, parent)).grid(column=6,
                                                                                                         row=posi)

        posi = 0
        for key in ACdict:  # populate frame with lines for each axlecounter
            ACline(key, posi, windowtype)
            posi += 1

        ttk.Button(framedict[windowtype], text="Add Axlecounter", command=lambda: AddAC(parent, "")).grid(column=0,
                                                                                                          columnspan=10,
                                                                                                          row=500,
                                                                                                          sticky=E)  # button to add an axlecounter

    AClistwindow(parent)  # Create the list window and frame


# -------Plungers--------

def Addplunger(parent, existingref):
    def Writeplunger(parent):
        ref = plungerref.get()
        description = plungerdescription.get()
        mode = plungermode.get()
        address = plungeraddress.get()
        register = plungerregister.get()
        plungerdict[(plungerref.get())] = plunger(mode, address, ref, description,
                                                  register)  # add an instance of an axlecounter to the list, with all the parameters.
        plungerlist(parent)
        plungersetupwin.destroy()

    # create a new popup window to enter details into:
    plungersetupwin = Toplevel(parent, takefocus=True)
    plungersetupwin.title("Plunger Setup")
    plungersetupframe = ttk.Frame(plungersetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    plungersetupframe.grid(column=0, row=0)

    # add in inputs for mode, address, ref and description

    plungerref = StringVar()  # TK variable for plungerref input
    plungerref.set(existingref)  # collect any existing ref for editing
    plungeraddress = IntVar()  # TK variable for plunger address input
    plungerdescription = StringVar()  # TK variable for plunger description input
    plungermode = IntVar()  # mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger
    plungerregister = IntVar()  # register of the individual plunger input (several plungers may be at one address)

    try:
        plungeraddress.set(plungerdict[existingref].address)  # collect existing
    except:
        pass
    try:
        plungerdescription.set(plungerdict[existingref].description)
    except:
        pass
    try:
        plungermode.set(plungerdict[existingref].mode)
    except:
        pass
    try:
        plungerregister.set(plungerdict[existingref].register)
    except:
        pass

    ttk.Label(plungersetupframe, text="Plunger Ref:").grid(column=0, row=0, sticky=W)
    ttk.Entry(plungersetupframe, width=7, textvariable=plungerref).grid(column=1, row=0, sticky=W)  # plungerref entry

    ttk.Label(plungersetupframe, text="Plunger Address:").grid(column=0, row=1, sticky=W)
    ttk.Entry(plungersetupframe, width=7, textvariable=plungeraddress).grid(column=1, row=1,
                                                                            sticky=W)  # plunger address entry

    ttk.Label(plungersetupframe, text="Plunger Register:").grid(column=0, row=2, sticky=W)
    ttk.Entry(plungersetupframe, width=7, textvariable=plungerregister).grid(column=1, row=2,
                                                                             sticky=W)  # plunger address entry

    # add in mode selector
    ttk.Label(plungersetupframe, text="Plunger Mode:").grid(column=0, row=3, sticky=W)
    Radiobutton(plungersetupframe, text="Store request", variable=plungermode, value=0).grid(column=1, row=3)
    Radiobutton(plungersetupframe, text="Don't store request", variable=plungermode, value=1).grid(column=2, row=3)

    ttk.Label(plungersetupframe, text="Plunger Description:").grid(column=0, row=4, sticky=W)
    ttk.Entry(plungersetupframe, width=70, textvariable=plungerdescription).grid(column=1, columnspan=4, row=4,
                                                                                 sticky=W)  # plungerref entry

    ttk.Button(plungersetupframe, text="OK", command=lambda: Writeplunger(parent)).grid(column=0, columnspan=10, row=10,
                                                                                        sticky=E, pady=10)


def plungerlist(parent):
    windowtype = "Plunger"

    def deleteplunger(key, parent):
        if messagebox.askyesno("Delete Asset", "Delete " + windowtype + " " + key + " ?"):
            del plungerdict[key]
            plungerlistwindow(parent)
        pass

    def plungerlistwindow(parent):

        try:
            framedict[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create plungerlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try:  # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create plungerlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()

        def plungerline(key, posi, windowtype):
            if plungerdict[key].mode == 0:
                modedescription = "Store request"
            if plungerdict[key].mode == 1:
                modedescription = "Don't store request"
            ttk.Label(framedict[windowtype], text="Plunger Ref: " + key).grid(column=0, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Address: ").grid(column=1, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text=plungerdict[key].address).grid(column=2, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Register: ").grid(column=3, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text=plungerdict[key].register).grid(column=4, row=posi, padx=0)
            ttk.Label(framedict[windowtype], text="Mode: " + modedescription).grid(column=5, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Description: " + plungerdict[key].description).grid(column=6,
                                                                                                       row=posi,
                                                                                                       padx=10)
            ttk.Button(framedict[windowtype], text="Edit", command=lambda: Addplunger(parent, key)).grid(column=7,
                                                                                                         row=posi)
            ttk.Button(framedict[windowtype], text="Delete", command=lambda: deleteplunger(key, parent)).grid(column=8,
                                                                                                              row=posi)

        posi = 0
        for key in plungerdict:  # populate frame with lines for each axlecounter
            plungerline(key, posi, windowtype)
            posi += 1

        ttk.Button(framedict[windowtype], text="Add Plunger", command=lambda: Addplunger(parent, "")).grid(column=0,
                                                                                                           columnspan=10,
                                                                                                           row=500,
                                                                                                           sticky=E)  # button to add an axlecounter

    plungerlistwindow(parent)  # Create the list window and frame


# ----- Signals -----

def Addsignal(parent, existingref):
    def Writesignal(parent):
        ref = signalref.get()
        description = signaldescription.get()
        sigtype = signaltype.get()
        address = signaladdress.get()
        dangerreg = dangeroutput.get()
        cautionreg = cautionoutput.get()
        clearreg = clearoutput.get()
        callingonreg = callingonoutput.get()
        bannerreg = banneroutput.get()
        route1reg = route1output.get()
        route2reg = route2output.get()
        route3reg = route3output.get()
        route4reg = route4output.get()
        route5reg = route5output.get()
        route6reg = route6output.get()
        # add an instance of an signal to the list, with all the parameters:
        signaldict[(signalref.get())] = signal(sigtype, address, ref, description,
                                               0, 0, dangerreg, cautionreg, clearreg,
                                               callingonreg, bannerreg, route1reg, route2reg, route3reg, route4reg,
                                               route5reg, route6reg)
        signallist(parent)
        # print(signaldict[ref].dangerreg)
        signalsetupwin.destroy()

    # create a new popup window to enter details into:
    signalsetupwin = Toplevel(parent, takefocus=True)
    signalsetupwin.title("Signal Setup")
    signalsetupframe = ttk.Frame(signalsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    signalsetupframe.grid(column=0, row=0)

    # add in inputs for mode, address, ref and description

    signalref = StringVar()  # TK variable for signalref input
    signalref.set(existingref)  # collect any existing ref for editing
    signaladdress = StringVar()  # TK variable for signal address input
    signaldescription = StringVar()  # TK variable for signal description input
    signaltype = IntVar()  # mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger
    danger = IntVar()
    caution = IntVar()
    clear = IntVar()
    callingon = IntVar()
    banner = IntVar()
    route1 = IntVar()
    route2 = IntVar()
    route3 = IntVar()
    route4 = IntVar()
    route5 = IntVar()
    route6 = IntVar()
    dangeroutput = IntVar()
    cautionoutput = IntVar()
    clearoutput = IntVar()
    callingonoutput = IntVar()
    banneroutput = IntVar()
    route1output = IntVar()
    route2output = IntVar()
    route3output = IntVar()
    route4output = IntVar()
    route5output = IntVar()
    route6output = IntVar()

    aspectvariables = [[danger, None, "Danger", 4, dangeroutput],
                       [caution, None, "Caution", 5, cautionoutput],
                       [clear, None, "Clear", 6, clearoutput],
                       [callingon, None, "Calling-on", 7, callingonoutput],
                       [banner, None, "Banner repeater", 8, banneroutput],
                       [route1, None, "Route 1", 9, route1output],
                       [route2, None, "Route 2", 10, route2output],
                       [route3, None, "Route 3", 11, route3output],
                       [route4, None, "Route 4", 12, route4output],
                       [route5, None, "Route 5", 13, route5output],
                       [route6, None, "Route 6", 14, route6output]]

    try:
        signaladdress.set(signaldict[existingref].address)  # collect existing
    except:
        pass
    try:
        signaldescription.set(signaldict[existingref].description)
    except:
        pass
    try:
        signaltype.set(signaldict[existingref].signaltype)
    except:
        pass
    try:
        signaldirectionindicator.set(signaldict[existingref].directionindicator)
    except:
        pass
    try:
        dangeroutput.set(signaldict[
                             existingref].dangerreg)  # collect existing ' put this in after having saved all of this in the instance.
        cautionoutput.set(signaldict[existingref].cautionreg)
        clearoutput.set(signaldict[existingref].clearreg)
        callingonoutput.set(signaldict[existingref].callingonreg)
        banneroutput.set(signaldict[existingref].bannerreg)
        route1output.set(signaldict[existingref].route1reg)
        route2output.set(signaldict[existingref].route2reg)
        route3output.set(signaldict[existingref].route3reg)
        route4output.set(signaldict[existingref].route4reg)
        route5output.set(signaldict[existingref].route5reg)
        route6output.set(signaldict[existingref].route6reg)
    except:
        pass

    # Set the checkboxes if a valid address has been set.
    for checkvar in aspectvariables:
        if checkvar[4].get() > 0:
            checkvar[0].set(1)
        else:
            checkvar[0].set(0)

    ttk.Label(signalsetupframe, text="Signal ref:").grid(column=0, row=0, sticky=W, padx=10)
    ttk.Entry(signalsetupframe, width=7, textvariable=signalref).grid(column=1, row=0, sticky=W,
                                                                      pady=4)  # signalref entry

    ttk.Label(signalsetupframe, text="Signal address:").grid(column=0, row=1, sticky=W, pady=4, padx=10)
    ttk.Entry(signalsetupframe, width=7, textvariable=signaladdress).grid(column=1, row=1,
                                                                          sticky=W)  # signal address entry

    # add in mode selector
    ttk.Label(signalsetupframe, text="Signal mode:").grid(column=0, row=2, sticky=W, padx=10)
    Radiobutton(signalsetupframe, text="Semaphore", variable=signaltype, value=0).grid(column=1, row=2, sticky=W)
    Radiobutton(signalsetupframe, text="Colour Light", variable=signaltype, value=1).grid(column=2, row=2, sticky=W)

    ttk.Label(signalsetupframe, text="Aspect availability:").grid(column=1, row=3, sticky=W, pady=4, padx=10)
    ttk.Label(signalsetupframe, text="Output assignment:").grid(column=2, row=3, sticky=W, pady=4, padx=10)

    aspectvariables = [[danger, None, "Danger", 4, dangeroutput],
                       [caution, None, "Caution", 5, cautionoutput],
                       [clear, None, "Clear", 6, clearoutput],
                       [callingon, None, "Calling-on", 7, callingonoutput],
                       [banner, None, "Banner repeater", 8, banneroutput],
                       [route1, None, "Route 1", 9, route1output],
                       [route2, None, "Route 2", 10, route2output],
                       [route3, None, "Route 3", 11, route3output],
                       [route4, None, "Route 4", 12, route4output],
                       [route5, None, "Route 5", 13, route5output],
                       [route6, None, "Route 6", 14, route6output]]

    # the above defines = the name of the checkbox variable, a place for the entrybox instance, the text for each line, each row number and the outputvariable

    def toggle():
        """Enables or disables the entry widget dependent on checkbox status"""
        for aspect in aspectvariables:
            if aspect[0].get() == 1:
                aspect[1].config(state=NORMAL)
            if aspect[0].get() == 0:
                aspect[1].config(state=DISABLED)

                # Create checkbutton and address entry for each aspect

    for aspect in aspectvariables:
        Checkbutton(signalsetupframe, text=aspect[2] + ":", command=toggle, variable=aspect[0], anchor=W).grid(
            row=aspect[3], column=1, sticky=W)
        aspect[1] = ttk.Entry(signalsetupframe, width=3, textvariable=aspect[4], state=DISABLED)  # signalref entry
        aspect[1].grid(column=2, row=aspect[3], sticky=W)

    toggle()

    ttk.Label(signalsetupframe, text="Signal Description:").grid(column=0, row=15, sticky=W, pady=4, padx=10)
    ttk.Entry(signalsetupframe, width=70, textvariable=signaldescription).grid(column=1, columnspan=4, row=15,
                                                                               sticky=W)  # signalref entry

    ttk.Button(signalsetupframe, text="OK", command=lambda: Writesignal(parent)).grid(column=4, row=21, sticky=E)


def signallist(parent):
    windowtype = "Signal"

    def deletesignal(key, parent):
        if messagebox.askyesno("Delete Asset", "Delete " + windowtype + " " + key + " ?"):
            del signaldict[key]
            signallistwindow(parent)
        pass

    def signallistwindow(parent):

        try:
            framedict[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create signallistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try:  # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create signallistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()

        def signalline(key, posi, windowtype):
            if signaldict[key].sigtype == 0:
                modedescription = "Semaphore"
            if signaldict[key].sigtype == 1:
                modedescription = "Colour Light"
            ttk.Label(framedict[windowtype], text="Signal Ref: " + key).grid(column=0, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Address: " + signaldict[key].address).grid(column=1, row=posi,
                                                                                              padx=10)
            ttk.Label(framedict[windowtype], text="Mode: " + modedescription).grid(column=2, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Description: " + signaldict[key].description).grid(column=3,
                                                                                                      row=posi, padx=10)
            ttk.Button(framedict[windowtype], text="Edit", command=lambda: Addsignal(parent, key)).grid(column=4,
                                                                                                        row=posi)
            ttk.Button(framedict[windowtype], text="Delete", command=lambda: deletesignal(key, parent)).grid(column=5,
                                                                                                             row=posi)

        posi = 0
        for key in signaldict:  # populate frame with lines for esignalh axlecounter
            signalline(key, posi, windowtype)
            posi += 1

        # button to add an axlecounter:    
        ttk.Button(framedict[windowtype], text="Add Signal",
                   command=lambda: Addsignal(parent, "")).grid(column=0,
                                                               columnspan=10, row=500,
                                                               sticky=E)  # button to add an axlecounter

    signallistwindow(parent)  # Create the list window and frame


# ------points-------

def Addpoint(parent, existingref):
    def Writepoint(parent):
        ref = pointref.get()
        description = pointdescription.get()
        mode = pointmode.get()
        address = pointaddress.get()
        pointdict[(pointref.get())] = point(mode, address, ref,
                                            description)  # add an instance of an point to the list, with all the parameters.
        pointlist(parent)
        pointsetupwin.destroy()

    # create a new popup window to enter details into:
    pointsetupwin = Toplevel(parent, takefocus=True)
    pointsetupwin.title("Points Setup")
    pointsetupframe = ttk.Frame(pointsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    pointsetupframe.grid(column=0, row=0)

    # add in inputs for mode, address, ref and description

    pointref = StringVar()  # TK variable for pointref input
    pointref.set(existingref)  # collect any existing ref for editing
    pointaddress = StringVar()  # TK variable for point address input
    pointdescription = StringVar()  # TK variable for point description input
    pointmode = IntVar()  # mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger

    try:
        pointaddress.set(pointdict[existingref].address)  # collect existing
    except:
        pass
    try:
        pointdescription.set(pointdict[existingref].description)
    except:
        pass
    try:
        pointmode.set(pointdict[existingref].mode)
    except:
        pass

    ttk.Label(pointsetupframe, text="Points Ref:").grid(column=0, row=0, sticky=W)
    ttk.Entry(pointsetupframe, width=7, textvariable=pointref).grid(column=1, row=0, sticky=W)  # pointref entry

    ttk.Label(pointsetupframe, text="Points Address:").grid(column=0, row=1, sticky=W)
    ttk.Entry(pointsetupframe, width=7, textvariable=pointaddress).grid(column=1, row=1,
                                                                        sticky=W)  # point address entry

    # add in mode selector
    ttk.Label(pointsetupframe, text="Point Mode:").grid(column=0, row=2, sticky=W)
    Radiobutton(pointsetupframe, text="With detection", variable=pointmode, value=0).grid(column=1, row=2)
    Radiobutton(pointsetupframe, text="Without detection", variable=pointmode, value=1).grid(column=2, row=2)

    ttk.Label(pointsetupframe, text="Points Description:").grid(column=0, row=3, sticky=W)
    ttk.Entry(pointsetupframe, width=70, textvariable=pointdescription).grid(column=1, columnspan=4, row=3,
                                                                             sticky=W)  # pointref entry

    ttk.Button(pointsetupframe, text="OK", command=lambda: Writepoint(parent)).grid(column=4, row=10, sticky=E)


def pointlist(parent):
    windowtype = "Points"

    def deletepoint(key, parent):
        if messagebox.askyesno("Delete Asset", "Delete " + windowtype + " " + key + " ?"):
            del pointdict[key]
            pointlistwindow(parent)
        pass

    def pointlistwindow(parent):

        try:
            framedict[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create pointlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try:  # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create pointlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()

        def pointline(key, posi, windowtype):
            if pointdict[key].mode == 0:
                modedescription = "With detection"
            if pointdict[key].mode == 1:
                modedescription = "Without detection"
            ttk.Label(framedict[windowtype], text="point Ref: " + key).grid(column=0, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Address: " + pointdict[key].address).grid(column=1, row=posi,
                                                                                             padx=10)
            ttk.Label(framedict[windowtype], text="Mode: " + modedescription).grid(column=2, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Description: " + pointdict[key].description).grid(column=3, row=posi,
                                                                                                     padx=10)
            ttk.Button(framedict[windowtype], text="Edit", command=lambda: Addpoint(parent, key)).grid(column=4,
                                                                                                       row=posi)
            ttk.Button(framedict[windowtype], text="Delete", command=lambda: deletepoint(key, parent)).grid(column=5,
                                                                                                            row=posi)

        posi = 0
        for key in pointdict:  # populate frame with lines for each axlecounter
            pointline(key, posi, windowtype)
            posi += 1

        ttk.Button(framedict[windowtype], text="Add points", command=lambda: Addpoint(parent, "")).grid(column=0,
                                                                                                        columnspan=10,
                                                                                                        row=500,
                                                                                                        sticky=E)  # button to add an axlecounter

    pointlistwindow(parent)  # Create the list window and frame


# route create/edit window:
def Add_route(root, existingref):
    def write_route(root):
        routedict[(routeref.get())] = route(ref=routeref.get(),
                                            description=description.get(), mode=mode.get(),
                                            sections=routesectionslistbox.curselection(),
                                            points=pointlistbox.curselection(),
                                            signals=siglistbox.curselection(), priority=priority.get())

        route_list(root)
        routesetupwin.destroy()

    routesetupwin = Toplevel(root, takefocus=True)  # create window for adding and managing routes
    routesetupwin.title("Route Setup")
    routesetupframe = ttk.Frame(routesetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    routesetupframe.grid(column=0, row=0)

    routeref = StringVar()  # variable for route reference
    description = StringVar()  # variable for descriptiion
    mode = IntVar()
    priority = IntVar()
    routeref.set(existingref)

    try:
        description.set(routedict[existingref].description)
    except:
        pass
    try:
        mode.set(routedict[existingref].mode)
    except:
        pass

    ttk.Label(routesetupframe, text="Route ref:").grid(column=0, row=0, sticky=W, padx=10)
    ttk.Entry(routesetupframe, width=7, textvariable=routeref).grid(column=1, row=0, sticky=W, pady=4)  # routeref entry

    ttk.Label(routesetupframe, text="Route mode:").grid(column=0, row=2, sticky=W, padx=10, pady=10)
    Radiobutton(routesetupframe, text="Store request", variable=mode, value=0).grid(column=1, row=2, sticky=W)
    Radiobutton(routesetupframe, text="Do not store request", variable=mode, value=1).grid(column=2, row=2, sticky=W)

    # list box for route sections
    ttk.Label(routesetupframe, text="Route sections:").grid(column=0, row=3, sticky=W, pady=4, padx=10)
    routesectionsframe = ttk.Frame(routesetupframe)
    routesectionsframe.grid(column=1, row=3, columnspan=2)
    routesectionsscrollbar = Scrollbar(routesectionsframe)
    routesectionsscrollbar.pack(side=RIGHT, fill=Y)
    routesectionslistbox = Listbox(routesectionsframe, selectmode=MULTIPLE, height=4)
    routesectionslistbox.pack(pady=10)
    routesectionslistbox.config(yscrollcommand=routesectionsscrollbar.set)
    routesectionsscrollbar.config(command=routesectionslistbox.yview)
    routesectionslistbox.configure(exportselection=False)

    for item in sectiondict:
        routesectionslistbox.insert(END, item)
    try:
        for x in routedict[existingref].sections:
            routesectionslistbox.selection_set(x)
    except:
        pass

    ttk.Label(routesetupframe, text="Route points to set:").grid(column=0, row=4, sticky=W, pady=4, padx=10)
    pointframe = ttk.Frame(routesetupframe)
    pointframe.grid(column=1, row=4, columnspan=2)
    pointscrollbar = Scrollbar(pointframe)
    pointscrollbar.pack(side=RIGHT, fill=Y)
    pointlistbox = Listbox(pointframe, selectmode=MULTIPLE, height=4)
    pointlistbox.pack(pady=10)
    pointlistbox.config(yscrollcommand=pointscrollbar.set)
    pointscrollbar.config(command=pointlistbox.yview)
    pointlistbox.configure(exportselection=False)

    for item in pointdict:
        pointlistbox.insert(END, item)
    try:
        for x in routedict[existingref].points:
            pointlistbox.selection_set(x)
    except:
        pass

    ttk.Label(routesetupframe, text="Signals to set:").grid(column=0, row=5, sticky=W, pady=4, padx=10)
    sigframe = ttk.Frame(routesetupframe)
    sigframe.grid(column=1, row=5, columnspan=2)
    sigscrollbar = Scrollbar(sigframe)
    sigscrollbar.pack(side=RIGHT, fill=Y)
    siglistbox = Listbox(sigframe, selectmode=MULTIPLE, height=4)
    siglistbox.pack(pady=10)
    siglistbox.config(yscrollcommand=sigscrollbar.set)
    sigscrollbar.config(command=siglistbox.yview)
    siglistbox.configure(exportselection=False)

    for item in signaldict:
        siglistbox.insert(END, item)
    try:
        for x in routedict[existingref].signals:
            siglistbox.selection_set(x)  # -------------make sure that signals with aspects set remain selected?
    except:
        pass

    ttk.Label(routesetupframe, text="Route priority:").grid(column=0, row=8, sticky=W, pady=4, padx=10)
    ttk.Entry(routesetupframe, width=70, textvariable=priority).grid(column=1, columnspan=4, row=8,
                                                                     sticky=W)  # routeref entry

    def choose_aspects():
        pass

    popup = Menu(routesetupframe, tearoff=0)
    popup.add_command(label="Set aspects", command=choose_aspects)  # , command=next) etc...

    def do_popup(event):
        # display the popup menu
        try:
            popup.tk_popup(event.x_root, event.y_root, 0)
        finally:
            # make sure to release the grab (Tk 8.0a1 only)
            popup.grab_release()

    siglistbox.bind("<Button-3>", do_popup)

    ttk.Label(routesetupframe, text="Route description:").grid(column=0, row=7, sticky=W, pady=4, padx=10)
    ttk.Entry(routesetupframe, width=70, textvariable=description).grid(column=1, columnspan=4, row=7,
                                                                        sticky=W)  # routeref entry

    ttk.Button(routesetupframe, text="OK", command=lambda: write_route(root)).grid(column=4, row=10, sticky=E)


# route management list:
def route_list(parent):
    windowtype = "route"

    def deleteroute(key, parent):
        if messagebox.askyesno("Delete route", "Delete " + windowtype + " " + key + " ?"):
            del routedict[key]
            routelistwindow(parent)
        pass

    def routelistwindow(parent):

        try:
            framedict[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create routelistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try:  # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,
                                              takefocus=False)  # create routelistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)
            framedict[windowtype] = ttk.Frame(windowdict[windowtype])
            framedict[windowtype].grid()

        def routeline(key, posi, windowtype):
            if routedict[key].mode == 0:
                modedescription = "Store request"
            if routedict[key].mode == 1:
                modedescription = "Do not store request"
            ttk.Label(framedict[windowtype], text="Route ref: " + key).grid(column=0, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Mode: " + modedescription).grid(column=4, row=posi, padx=10)
            ttk.Label(framedict[windowtype], text="Description: " + routedict[key].description).grid(column=5, row=posi,
                                                                                                     padx=10)
            ttk.Button(framedict[windowtype], text="Edit", command=lambda: Add_route(parent, key)).grid(column=6,
                                                                                                        row=posi)
            ttk.Button(framedict[windowtype], text="Delete", command=lambda: deleteroute(key, parent)).grid(column=7,
                                                                                                            row=posi)

        posi = 0
        for key in routedict:  # populate frame with lines for each axlecounter
            routeline(key, posi, windowtype)
            posi += 1

        ttk.Button(framedict[windowtype], text="Add route", command=lambda: Add_route(parent, "")).grid(column=0,
                                                                                                        columnspan=10,
                                                                                                        row=500,
                                                                                                        sticky=E)  # button to add an axlecounter

    routelistwindow(parent)  # Create the list window and frame


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
    json_string = jsons.dumps(infradata)
    temp_objects = json.loads(json_string)
    json_out.write(json.dumps(temp_objects, indent=4))
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
