from tkinter import *
from tkinter import ttk
from tkinter import messagebox
#import minimalmodbus
import pickle

Sectionlist = {} # dictionary for containing instances of sections
ACdict = {} # dictionary for containing instances of axlecounters
signaldict = {} # dictionary for containing instances of Signals
plungerdict = {} # dictionary for containing instances of Plungers
pointdict = {} # dictionary for containing instances of Points
routesdict = {} # dictionary for containing instances of Routes

windowdict = {} # for containing all the windows associated with asset lists
framelist = {} # for containing the frames that contain the lines

class axlecounter:
    def __init__(self,mode,address,ref,description):
        self.mode = mode         #mode = axlecount, simple trigger or directional trigger
        self.address = address    #address
        self.ref = ref    #Freetext Reference
        self.description = description #Freetext description

class signal:
    def __init__(self,sigtype,address,ref,description,availableaspects,directionindicator,dangerreg,cautionreg,clearreg,callingonreg,bannerreg,route1reg,route2reg,route3reg,route4reg,route5reg,route6reg):
        self.sigtype = sigtype         #mode = Semaphore or coulour light
        self.address = address    #address
        self.ref = ref    #Freetext Reference
        self.description = description #Freetext description
        self.availableaspects = availableaspects #available aspects
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
        self.illumination = "On" #night illumination mode
        self.aspect = "0" #current aspect        

class section:
    def __init__(self):
        self.ref = ""        #Freetext Ref
        self.description = ""        #Freetext description
        #add section attributes - this comes after adding the other assets as these can be referenced by a section instance
        self.mode = ""        #mode: axlecounter, trackcircuit, magnet (input trigger) or RFID
        self.inctrig = ""   #increment triggers
        self.dectrig = ""    #decrement triggers
        self.homesignal = ""    #protecting signals
        self.occstatus = ""    #occupation status
        self.routestatus = ""    #availability status
        
class plunger:
    def __init__(self,mode,address,ref,description,register):
        self.mode = mode    #mode of operation, request store or no request store.
        self.address = address      #address
        self.ref = ref    #Freetext Referece
        self.description = description    #freetext description
        self.register = register #register address

class point:
    def __init__(self,mode,address,ref,description):
        self.address = address #address
        self.mode = mode #mode: with detection or without detection
        self.ref = ref # Freetext reference
        self.description = description # Freetext description
        self.setstatus = "" #set status
        self.detection = "" #detection status

class route:
    def __init__(self):
        self.sections = []    #ordered list of sections
        self.points = []    #ordered list of points to set
        self.signals = []    #ordered list of signals to set
        self.priority = ""  #priority number (change this to be an integer)
        self.trigger = [] #list of triggers for route - section occupation, section non-occupation, plunger, lever etc.

class lever:
    #for later on!
    pass

class sectionsetupframe:
    def __init__(self, sectionref):
        pass

class sectionline:
    def __init__(self, parent, posi, sectionclassname):
        self.parent = parent
        self.posi = posi
       
        def removesection(): # destroy functon for button on each line to delete itslef
            self.sectionframe.destroy()

        def Update(self):
            print("Update now")
            pass

        self.sectionframe = ttk.Frame(self.parent, padding="3 3 12 12", borderwidth=1, relief=SUNKEN) # frame to contain each line
        self.sectionframe.grid(column=0,row=self.posi) # put frame in position passed as arg
        ttk.Label(self.sectionframe, text="Section Ref:").grid(column=0, row=0, sticky=W)
        ttk.Label(self.sectionframe, text=sectionclassname.ref).grid(column=1,row=0)
        ttk.Label(self.sectionframe, text="Description:").grid(column=2, row=0, sticky=W)
        ttk.Label(self.sectionframe, text=sectionclassname.description).grid(column=3,row=0)
        ttk.Label(self.sectionframe, text="Status:"+" AXLECOUNT GOES HERE ").grid(column=49,row=0) # add status variable in here.        
        ttk.Button(self.sectionframe, text="Remove Section", command=removesection).grid(column=50, row=0) # destroy self button (does not yet destroy the instance of the class)      
        #need to create an associated instance of a section and assign it with the variables - need to do this when updated.

class sectionmonitor:
    def __init__(self):
        pass

def updatesections(root):
    i = 0
    sectionlinelist = []
    for section in Sectionlist:
        pass
        sectionlinelist.append(sectionline(root,(i+1),section))
        print(Sectionlist[i].ref)
        i += 1

def AddSection(root):

    def WriteSection():
        Sectionlist.append(sections()) # add an instance of a section to the list
        Sectionlist[-1].ref = sectionref.get() # assign the ref to the variable
        Sectionlist[-1].description = description.get() # assign the description to the variable
        Sectionlist[-1].mode = mode.get()
        Sectionlist[-1].inctrig = inctrig.get()
        Sectionlist[-1].dectrig = dectrig.get()
        print(Sectionlist[-1].ref,Sectionlist[-1].description,Sectionlist)
        updatesections(root)
        sectionsetupwin.destroy()

    #now need to iterate across list of sections (Sectionlist) to create the list of sections window. Need to consider how to update and remove lines as required

    sectionsetupwin = Toplevel(root,takefocus=True) # create window for adding and managing sections
    sectionsetupwin.title("Section Setup")
    sectionsetupframe = ttk.Frame(sectionsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    sectionsetupframe.grid(column = 0, row = 0)

    sectionref = StringVar() # variable for section reference
    description = StringVar() # variable for descriptiion
    mode = StringVar() # might not need this if I put a list here instead
    inctrig = StringVar() # ditto
    dectrig = StringVar() # ditto
    
    ttk.Label(sectionsetupframe, text="Section Ref:").grid(column=0, row=0, sticky=W)
    SectionRef = ttk.Entry(sectionsetupframe, width=7, textvariable=sectionref) # sectionref entry
    SectionRef.grid(column=1, row=0, sticky=W)
    
    ttk.Label(sectionsetupframe, text="Description:").grid(column=0, row=1, sticky=W)
    Descript = ttk.Entry(sectionsetupframe, width=7, textvariable=description) # sectionref entry
    Descript.grid(column=1, row=1, sticky=W)


    ttk.Label(sectionsetupframe, text="Mode:").grid(column=0, row=2, sticky=W)
    Descript = ttk.Entry(sectionsetupframe, width=7, textvariable=mode)  #mode entry: axlecounter, trackcircuit, magnet (input trigger) or RFID
    Descript.grid(column=1, row=2)

    ttk.Label(sectionsetupframe, text="Increment Triggers:").grid(column=0, row=3, sticky=W)
    Descript = ttk.Entry(sectionsetupframe, width=7, textvariable=inctrig) # increment trigger entry
    Descript.grid(column=1, row=3)

    ttk.Label(sectionsetupframe, text="Decrement Triggers:").grid(column=0, row=4, sticky=W)
    Descript = ttk.Entry(sectionsetupframe, width=7, textvariable=dectrig) # decrement trigger entry
    Descript.grid(column=1, row=4)
        
    ttk.Button(sectionsetupframe, text="OK", command=WriteSection).grid(column=0, row=10, sticky=NW)

    #need to add a delete section funcion at some point

def AddAC(parent,existingref):

    def WriteAC(parent):
        ref = ACref.get()
        description = ACdescription.get()
        mode = ACmode.get()
        address = ACaddress.get()
        ACdict[(ACref.get())]=axlecounter(mode,address,ref,description)  # add an instance of an axlecounter to the list, with all the parameters.
        AClist(parent)
        ACsetupwin.destroy()

    #create a new popup window to enter details into:
    ACsetupwin = Toplevel(parent,takefocus=True) 
    ACsetupwin.title("Axle Counter Setup")
    ACsetupframe = ttk.Frame(ACsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    ACsetupframe.grid(column = 0, row = 0)

    #add in inputs for mode, address, ref and description

    ACref = StringVar() #TK variable for ACref input
    ACref.set(existingref) #collect any existing ref for editing
    ACaddress = StringVar() #TK variable for AC address input
    ACdescription = StringVar() #TK variable for AC description input
    ACmode = IntVar() #mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger

    try:
        ACaddress.set(ACdict[existingref].address) # collect existing
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
    ttk.Entry(ACsetupframe, width=7, textvariable=ACref).grid(column=1, row=0, sticky=W) # ACref entry
  
    ttk.Label(ACsetupframe, text="Axle Counter Address:").grid(column=0, row=1, sticky=W)
    ttk.Entry(ACsetupframe, width=7, textvariable=ACaddress).grid(column=1, row=1, sticky=W) # AC address entry

    #add in mode selector
    ttk.Label(ACsetupframe, text="Axle Counter Mode:").grid(column=0, row=2, sticky=W)   
    Radiobutton(ACsetupframe, text="Axle Count", variable=ACmode, value = 0).grid(column=1,row=2)
    Radiobutton(ACsetupframe, text="Non-directional Trigger", variable=ACmode, value = 1).grid(column=2,row=2)
    Radiobutton(ACsetupframe, text="Directional Trigger", variable=ACmode, value = 2).grid(column=3,row=2)

    ttk.Label(ACsetupframe, text="Axle Counter Description:").grid(column=0, row=3, sticky=W)
    ttk.Entry(ACsetupframe, width=70, textvariable=ACdescription).grid(column=1, columnspan=4, row=3, sticky=W) # ACref entry

    ttk.Button(ACsetupframe, text="OK", command=lambda: WriteAC(parent)).grid(column=4, row=10, sticky=E)    
    
def AClist(parent):
    windowtype = "Axle Counter"    
    def deleteAC(key,parent):
        if messagebox.askyesno("Delete Asset","Delete "+windowtype+" "+key+" ?"):
            del ACdict[key]
            AClistwindow(parent)
        pass
    
    def AClistwindow(parent):
        
        try:
            framelist[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create AClistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try: # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create AClistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)                
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()            
        
        def ACline(key,posi,windowtype):
            if ACdict[key].mode == 0:
                modedescription = "Axlecount"
            if ACdict[key].mode == 1:
                modedescription = "Non-directional trigger"
            if ACdict[key].mode == 2:
                modedescription = "Directional trigger"
            ttk.Label(framelist[windowtype], text="Axle Counter Ref: "+key).grid(column = 0, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Address: "+ACdict[key].address).grid(column = 1, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Mode: " +modedescription).grid(column = 2, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Description: "+ACdict[key].description).grid(column = 3, row = posi, padx = 10)
            ttk.Button(framelist[windowtype], text="Edit", command= lambda: AddAC(parent,key)).grid(column = 4, row = posi)
            ttk.Button(framelist[windowtype], text="Delete", command = lambda: deleteAC(key,parent)).grid(column = 5, row = posi)

        posi = 0
        for key in ACdict: #populate frame with lines for each axlecounter
            ACline(key,posi,windowtype)
            posi += 1
            
        ttk.Button(framelist[windowtype], text="Add Axlecounter", command= lambda: AddAC(parent,"")).grid(column=0, columnspan=10, row=500, sticky=E) # button to add an axlecounter
    AClistwindow(parent) # Create the list window and frame

#-------Plungers--------

def Addplunger(parent,existingref):

    def Writeplunger(parent):
        ref = plungerref.get()
        description = plungerdescription.get()
        mode = plungermode.get()
        address = plungeraddress.get()
        register  = plungerregister.get()
        plungerdict[(plungerref.get())]=plunger(mode,address,ref,description,register)  # add an instance of an axlecounter to the list, with all the parameters.
        plungerlist(parent)
        plungersetupwin.destroy()

    #create a new popup window to enter details into:
    plungersetupwin = Toplevel(parent,takefocus=True)
    plungersetupwin.title("Plunger Setup")
    plungersetupframe = ttk.Frame(plungersetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    plungersetupframe.grid(column = 0, row = 0)

    #add in inputs for mode, address, ref and description

    plungerref = StringVar() #TK variable for plungerref input
    plungerref.set(existingref) #collect any existing ref for editing
    plungeraddress = StringVar() #TK variable for plunger address input
    plungerdescription = StringVar() #TK variable for plunger description input
    plungermode = IntVar() #mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger
    plungerregister = IntVar() #register of the individual plunger input (several plungers may be at one address)

    try:
        plungeraddress.set(plungerdict[existingref].address) # collect existing
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
    ttk.Entry(plungersetupframe, width=7, textvariable=plungerref).grid(column=1, row=0, sticky=W) # plungerref entry
  
    ttk.Label(plungersetupframe, text="Plunger Address:").grid(column=0, row=1, sticky=W)
    ttk.Entry(plungersetupframe, width=7, textvariable=plungeraddress).grid(column=1, row=1, sticky=W) # plunger address entry

    ttk.Label(plungersetupframe, text="Plunger Register:").grid(column=0, row=2, sticky=W)
    ttk.Entry(plungersetupframe, width=7, textvariable=plungerregister).grid(column=1, row=2, sticky=W) # plunger address entry

    #add in mode selector
    ttk.Label(plungersetupframe, text="Plunger Mode:").grid(column=0, row=3, sticky=W)   
    Radiobutton(plungersetupframe, text="Store request", variable=plungermode, value = 0).grid(column=1,row=3)
    Radiobutton(plungersetupframe, text="Don't store request", variable=plungermode, value = 1).grid(column=2,row=3)

    ttk.Label(plungersetupframe, text="Plunger Description:").grid(column=0, row=4, sticky=W)
    ttk.Entry(plungersetupframe, width=70, textvariable=plungerdescription).grid(column=1, columnspan=4, row=4, sticky=W) # plungerref entry

    ttk.Button(plungersetupframe, text="OK", command=lambda: Writeplunger(parent)).grid(column=0, columnspan=10, row=10, sticky=E, pady=10)    
    
def plungerlist(parent):
    windowtype = "Plunger"    
    def deleteplunger(key,parent):
        if messagebox.askyesno("Delete Asset","Delete "+windowtype+" "+key+" ?"):
            del plungerdict[key]
            plungerlistwindow(parent)
        pass
    
    def plungerlistwindow(parent):
        
        try:
            framelist[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create plungerlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try: # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create plungerlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)                
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()            
        
        def plungerline(key,posi,windowtype):
            if plungerdict[key].mode == 0:
                modedescription = "Store request"
            if plungerdict[key].mode == 1:
                modedescription = "Don't store request"
            ttk.Label(framelist[windowtype], text="Plunger Ref: "+key).grid(column = 0, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Address: "+plungerdict[key].address).grid(column = 1, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Register: ").grid(column = 2, row = posi, padx = 10)              
            ttk.Label(framelist[windowtype], text=plungerdict[key].register).grid(column = 3, row = posi, padx = 0)            
            ttk.Label(framelist[windowtype], text="Mode: " +modedescription).grid(column = 4, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Description: "+plungerdict[key].description).grid(column = 5, row = posi, padx = 10)
            ttk.Button(framelist[windowtype], text="Edit", command= lambda: Addplunger(parent,key)).grid(column = 6, row = posi)
            ttk.Button(framelist[windowtype], text="Delete", command = lambda: deleteplunger(key,parent)).grid(column = 7, row = posi)

        posi = 0
        for key in plungerdict: #populate frame with lines for each axlecounter
            plungerline(key,posi,windowtype)
            posi += 1
            
        ttk.Button(framelist[windowtype], text="Add Plunger", command= lambda: Addplunger(parent,"")).grid(column=0, columnspan=10, row=500, sticky=E) # button to add an axlecounter

    plungerlistwindow(parent) # Create the list window and frame

#----- Signals -----

def Addsignal(parent,existingref):

    
    def Writesignal(parent):
        ref = signalref.get()
        description = signaldescription.get()
        sigtype = signaltype.get()
        address = signaladdress.get()
        availableaspects = listbox.curselection() # coded list of available aspects - 0 = Danger, 1 = Caution, 2 = clear, 3 = Calling on
        directionindicator = signaldirectionindicator.get()
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
        signaldict[(signalref.get())]=signal(sigtype,address,ref,description,availableaspects,directionindicator,dangerreg,cautionreg,clearreg,callingonreg,bannerreg,route1reg,route2reg,route3reg,route4reg,route5reg,route6reg)  # add an instance of an signal to the list, with all the parameters. 
        signallist(parent)
        #print(signaldict[ref].dangerreg)
        signalsetupwin.destroy()

    def aspectassignment():

        try:
            dangeroutput.set(signaldict[existingref].dangerreg)# collect existing ' put this in after having saved all of this in the instance. 
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



        #--------make the above work and then do for all the other assignments.

        aspectassignmentframe = ttk.Frame(signalsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
        aspectassignmentframe.grid(column = 0, row = 1)
        ttk.Label(aspectassignmentframe, text="Danger:").grid(column=0, row=0, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=dangeroutput).grid(column=1, row=0, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Caution:").grid(column=0, row=1, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=cautionoutput).grid(column=1, row=1, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Clear:").grid(column=0, row=2, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=clearoutput).grid(column=1, row=2, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Calling on:").grid(column=0, row=3, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=callingonoutput).grid(column=1, row=3, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Banner repeater:").grid(column=0, row=4, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=banneroutput).grid(column=1, row=4, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Route indication 1:").grid(column=0, row=5, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=route1output).grid(column=1, row=5, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Route indication 2:").grid(column=0, row=6, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=route2output).grid(column=1, row=6, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Route indication 3:").grid(column=0, row=7, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=route3output).grid(column=1, row=7, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Route indication 4:").grid(column=0, row=8, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=route4output).grid(column=1, row=8, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Route indication 5:").grid(column=0, row=9, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=route5output).grid(column=1, row=9, sticky=W, pady=4)
        ttk.Label(aspectassignmentframe, text="Route indication 6:").grid(column=0, row=10, sticky=W, padx=10)
        ttk.Entry(aspectassignmentframe, width=7, textvariable=route6output).grid(column=1, row=10, sticky=W, pady=4)

    #create a new popup window to enter details into:
    signalsetupwin = Toplevel(parent,takefocus=True)
    signalsetupwin.title("Signal Setup")
    signalsetupframe = ttk.Frame(signalsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    signalsetupframe.grid(column = 0, row = 0)

    #add in inputs for mode, address, ref and description

    signalref = StringVar() #TK variable for signalref input
    signalref.set(existingref) #collect any existing ref for editing
    signaladdress = StringVar() #TK variable for signal address input
    signaldescription = StringVar() #TK variable for signal description input
    signaltype = IntVar() #mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger
    signaldirectionindicator = IntVar()
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

    try:
        signaladdress.set(signaldict[existingref].address) # collect existing
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


    ttk.Label(signalsetupframe, text="Signal ref:").grid(column=0, row=0, sticky=W, padx=10)
    ttk.Entry(signalsetupframe, width=7, textvariable=signalref).grid(column=1, row=0, sticky=W, pady=4) # signalref entry
  
    ttk.Label(signalsetupframe, text="Signal address:").grid(column=0, row=1, sticky=W, pady = 4, padx=10)
    ttk.Entry(signalsetupframe, width=7, textvariable=signaladdress).grid(column=1, row=1, sticky=W) # signal address entry

    #add in mode selector
    ttk.Label(signalsetupframe, text="Signal mode:").grid(column=0, row=2, sticky=W, padx=10)   
    Radiobutton(signalsetupframe, text="Semaphore", variable=signaltype, value = 0).grid(column=1,row=2,sticky=W)
    Radiobutton(signalsetupframe, text="Colour Light", variable=signaltype, value = 1).grid(column=2,row=2,sticky=W)

    ttk.Label(signalsetupframe, text="Available aspects:").grid(column=0, row=3, sticky=W, pady=4, padx=10)
    listbox = Listbox(signalsetupframe, selectmode=MULTIPLE, height=5)
    listbox.grid(column=1, row = 3, sticky=W, pady=10)
    for item in ["Danger", "Caution", "Clear", "Calling On","Banner Repeater"]:
        listbox.insert(END,item)
    try:
        for x in signaldict[existingref].availableaspects:
            listbox.selection_set(x)      
    except:
        pass

    ttk.Button(signalsetupframe, text=" Aspect to output assignment setup ", command=aspectassignment).grid(column=2,row=3,sticky=W,padx=10)
    
    ttk.Label(signalsetupframe, text="Route / direction indicator:").grid(column=0, row=4, sticky=W, pady=4, padx=10)    
    Checkbutton(signalsetupframe, variable=signaldirectionindicator).grid(column=1,row=4,pady=4,sticky=W)

    ttk.Label(signalsetupframe, text="Signal Description:").grid(column=0, row=5, sticky=W, pady=4, padx=10)
    ttk.Entry(signalsetupframe, width=70, textvariable=signaldescription).grid(column=1, columnspan=4, row=5, sticky=W) # signalref entry

    ttk.Button(signalsetupframe, text="OK", command=lambda: Writesignal(parent)).grid(column=4, row=10, sticky=E)    
    
def signallist(parent):
    windowtype = "Signal"    
    def deletesignal(key,parent):
        if messagebox.askyesno("Delete Asset","Delete "+windowtype+" "+key+" ?"):
            del signaldict[key]
            signallistwindow(parent)
        pass
    
    def signallistwindow(parent):
        
        try:
            framelist[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create signallistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try: # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create signallistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)                
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()            
        
        def signalline(key,posi,windowtype):
            if signaldict[key].sigtype == 0:
                modedescription = "Semaphore"
            if signaldict[key].sigtype == 1:
                modedescription = "Colour Light"
            ttk.Label(framelist[windowtype], text="Signal Ref: "+key).grid(column = 0, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Address: "+signaldict[key].address).grid(column = 1, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Mode: " +modedescription).grid(column = 2, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Description: "+signaldict[key].description).grid(column = 3, row = posi, padx = 10)
            ttk.Button(framelist[windowtype], text="Edit", command= lambda: Addsignal(parent,key)).grid(column = 4, row = posi)
            ttk.Button(framelist[windowtype], text="Delete", command = lambda: deletesignal(key,parent)).grid(column = 5, row = posi)

        posi = 0
        for key in signaldict: #populate frame with lines for esignalh axlecounter
            signalline(key,posi,windowtype)
            posi += 1
            
        ttk.Button(framelist[windowtype], text="Add Signal", command= lambda: Addsignal(parent,"")).grid(column=0, columnspan=10, row=500, sticky=E) # button to add an axlecounter

    signallistwindow(parent) # Create the list window and frame

#------points-------

def Addpoint(parent,existingref):

    def Writepoint(parent):
        ref = pointref.get()
        description = pointdescription.get()
        mode = pointmode.get()
        address = pointaddress.get()
        pointdict[(pointref.get())]=point(mode,address,ref,description)  # add an instance of an point to the list, with all the parameters.
        pointlist(parent)
        pointsetupwin.destroy()

    #create a new popup window to enter details into:
    pointsetupwin = Toplevel(parent,takefocus=True)
    pointsetupwin.title("Points Setup")
    pointsetupframe = ttk.Frame(pointsetupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    pointsetupframe.grid(column = 0, row = 0)

    #add in inputs for mode, address, ref and description

    pointref = StringVar() #TK variable for pointref input
    pointref.set(existingref) #collect any existing ref for editing
    pointaddress = StringVar() #TK variable for point address input
    pointdescription = StringVar() #TK variable for point description input
    pointmode = IntVar() #mode is 0 for Axlecount, 1 for non-directional trigger and 2 for directional trigger

    try:
        pointaddress.set(pointdict[existingref].address) # collect existing
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
    ttk.Entry(pointsetupframe, width=7, textvariable=pointref).grid(column=1, row=0, sticky=W) # pointref entry
  
    ttk.Label(pointsetupframe, text="Points Address:").grid(column=0, row=1, sticky=W)
    ttk.Entry(pointsetupframe, width=7, textvariable=pointaddress).grid(column=1, row=1, sticky=W) # point address entry

    #add in mode selector
    ttk.Label(pointsetupframe, text="Point Mode:").grid(column=0, row=2, sticky=W)   
    Radiobutton(pointsetupframe, text="With detection", variable=pointmode, value = 0).grid(column=1,row=2)
    Radiobutton(pointsetupframe, text="Without detection", variable=pointmode, value = 1).grid(column=2,row=2)

    ttk.Label(pointsetupframe, text="Points Description:").grid(column=0, row=3, sticky=W)
    ttk.Entry(pointsetupframe, width=70, textvariable=pointdescription).grid(column=1, columnspan=4, row=3, sticky=W) # pointref entry

    ttk.Button(pointsetupframe, text="OK", command=lambda: Writepoint(parent)).grid(column=4, row=10, sticky=E)    
    
def pointlist(parent):
    windowtype = "Points"    
    def deletepoint(key,parent):
        if messagebox.askyesno("Delete Asset","Delete "+windowtype+" "+key+" ?"):
            del pointdict[key]
            pointlistwindow(parent)
        pass
    
    def pointlistwindow(parent):
        
        try:
            framelist[windowtype].destroy()
        except:
            pass
        if windowtype in windowdict:
            pass
        else:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create pointlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)

        try: # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()
        except:
            windowdict[windowtype] = Toplevel(parent,takefocus=False) #create pointlistwindow and put it into class dictionary windowdict
            windowdict[windowtype].title(windowtype)                
            framelist[windowtype] = ttk.Frame(windowdict[windowtype])
            framelist[windowtype].grid()            
        
        def pointline(key,posi,windowtype):
            if pointdict[key].mode == 0:
                modedescription = "With detection"
            if pointdict[key].mode == 1:
                modedescription = "Without detection"
            ttk.Label(framelist[windowtype], text="point Ref: "+key).grid(column = 0, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Address: "+pointdict[key].address).grid(column = 1, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Mode: " +modedescription).grid(column = 2, row = posi, padx = 10)
            ttk.Label(framelist[windowtype], text="Description: "+pointdict[key].description).grid(column = 3, row = posi, padx = 10)
            ttk.Button(framelist[windowtype], text="Edit", command= lambda: Addpoint(parent,key)).grid(column = 4, row = posi)
            ttk.Button(framelist[windowtype], text="Delete", command = lambda: deletepoint(key,parent)).grid(column = 5, row = posi)

        posi = 0
        for key in pointdict: #populate frame with lines for each axlecounter
            pointline(key,posi,windowtype)
            posi += 1
            
        ttk.Button(framelist[windowtype], text="Add points", command= lambda: Addpoint(parent,"")).grid(column=0, columnspan=10, row=500, sticky=E) # button to add an axlecounter

    pointlistwindow(parent) # Create the list window and frame

def savelayout():
    pickle_out = open("../layout.pickle", "wb") #open the file to write
    pickle.dump(Sectionlist, pickle_out)
    pickle.dump(ACdict, pickle_out)
    pickle.dump(signaldict, pickle_out)
    pickle.dump(plungerdict, pickle_out)
    pickle.dump(pointdict, pickle_out)
    pickle.dump(routesdict, pickle_out)    
    pickle_out.close() # close the file
    print("saved")


def loadlayout():
    global Sectionlist
    global ACdict
    global signaldict
    global plungerdict
    global pointdict
    global routesdict
    
    pickle_in = open("../layout.pickle", "rb") #open the file to read
    Sectionlist = pickle.load(pickle_in)
    ACdict = pickle.load(pickle_in)
    signaldict = pickle.load(pickle_in)
    plungerdict = pickle.load(pickle_in)
    pointdict = pickle.load(pickle_in)
    routesdict = pickle.load(pickle_in)    
    print("loadnow")
    pass

def main():
    root = Tk()
    root.title("Section Monitor")
    SectionMonitor = ttk.Frame(root) # create main window for monitoring sections
    SectionMonitor.grid(column=0, row=0, sticky=W)
    ttk.Button(SectionMonitor, text="Add Section", command= lambda: AddSection(root)).grid(column=0, row=1, sticky=NW) # button to add a sectionline
    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open", command=lambda:loadlayout())
    filemenu.add_command(label="Save", command=lambda:savelayout())
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    assetmenu = Menu(menubar,tearoff=0)
    assetmenu.add_command(label="Axle counters", command=lambda:AClist(root))
    assetmenu.add_command(label="Plungers", command=lambda:plungerlist(root))
    assetmenu.add_command(label="Signals", command=lambda:signallist(root))
    assetmenu.add_command(label="Points", command=lambda:pointlist(root))
    menubar.add_cascade(label="Assets", menu=assetmenu)
    sectionmenu = Menu(menubar,tearoff=0)
    sectionmenu.add_command(label="Add section", command=lambda:AddSection(root))
    menubar.add_cascade(label="Section", menu=sectionmenu)
    # display the menu
    root.config(menu=menubar)
    root.mainloop() # run infitite Tk loop

if __name__ == '__main__':
    main()


