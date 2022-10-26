from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import minimalmodbus

Sectionlist = {} # dictionary for containing instances of sections
ACdict = {} # dictionary for containing instances of axlecounters
Signallist = {} # dictionary for containing instances of Signals
Plungerlist = {} # dictionary for containing instances of Plungers
Pointslist = {} # dictionary for containing instances of Points
Routeslist = {} # dictionary for containing instances of Routes

AClistdict = {} # dictionary for containing lines in the tkinter window for AC's.

class axlecounter:
    def __init__(self,mode,address,ref,description):
        self.mode = mode         #mode = axlecount, simple trigger or directional trigger
        self.address = address    #address
        self.ref = ref    #Freetext Reference
        self.description = description #Freetext description

class signals:
        #address
        #Ref
        #freetext name
        #Semaphore or colour light
        #available aspects
        #night illumination state
        #current aspect        
    pass


class sections:
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
        self.routes = ""   #autoset routes - perhaps in order of preference
        
class plungers:
    def __init__(self):
        self.mode = ""    #mode of operation, perhaps plunger, switch or rotary switch
        self.address = ""      #address
        self.ref = ""    #Freetext Referece
        self.description = ""    #freetext description
        self.routes = "" # associated routes


class points:
    def __init__(self):
        self.address = "" #address
        self.mode = "" #mode: with detection or without detection
        self.ref = "" # Freetext reference
        self.description = "" # Freetext description
        self.setstatus = "" #set status
        self.detection = "" #detection status
        self.section = "" #containing section


class route:
    def __init__(self):
        self.sections = []    #ordered list of sections
        self.points = []    #ordered list of points to set
        self.signals = []    #ordered list of signals to set
        self.priority = ""  #priority number (change this to be an integer)

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

def AddAC(root,existingref):

    def WriteAC():
        ref = ACref.get()
        description = ACdescription.get()
        mode = ACmode.get()
        address = ACaddress.get()
        ACdict[(ACref.get())]=axlecounter(mode,address,ref,description)  # add an instance of an axlecounter to the list, with all the parameters.
        assetlist(root,"Axle Counter")
        ACsetupwin.destroy()

    #create a new popup window to enter details into:
    ACsetupwin = Toplevel(root,takefocus=True)
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

    ttk.Button(ACsetupframe, text="OK", command=WriteAC).grid(column=4, row=10, sticky=E)    
    
class assetlist:
    windowdict = {} # for containing all the windows associated with asset lists
    framelist = {} # for containing the frames that contain the lines
    def __init__(self,parent, windowtype):

        def deleteasset(key,parent,windowtype):
            if messagebox.askyesno("Delete Asset","Delete Asset "+key+" ?"):
                del ACdict[key]
                AClist(parent,windowtype)
            pass
        
        def AClist(parent,windowtype):
            try:
                self.framelist[windowtype].destroy()
            except:
                pass
            if windowtype in self.windowdict:
                pass
            else:
                self.windowdict[windowtype] = Toplevel(parent,takefocus=False) #create AClistwindow and put it into class dictionary windowdict
                self.windowdict[windowtype].title(windowtype)

            try: # this try is required for when the window has been closed and cant be found to put a frame in, although the instance still lives in the dict
                self.framelist[windowtype] = ttk.Frame(assetlist.windowdict[windowtype])
                self.framelist[windowtype].grid()
            except:
                self.windowdict[windowtype] = Toplevel(parent,takefocus=False) #create AClistwindow and put it into class dictionary windowdict
                self.windowdict[windowtype].title(windowtype)                
                self.framelist[windowtype] = ttk.Frame(assetlist.windowdict[windowtype])
                self.framelist[windowtype].grid()            
            
            def ACline(parent,key,posi,windowtype):
                if ACdict[key].mode == 0:
                    modedescription = "Axlecount"
                if ACdict[key].mode == 1:
                    modedescription = "Non-directional trigger"
                if ACdict[key].mode == 2:
                    modedescription = "Directional trigger"
                ttk.Label(self.framelist[windowtype], text="Axle Counter Ref: "+key).grid(column = 0, row = posi, padx = 10)
                ttk.Label(self.framelist[windowtype], text="Address: "+ACdict[key].address).grid(column = 1, row = posi, padx = 10)
                ttk.Label(self.framelist[windowtype], text="Mode: " +modedescription).grid(column = 2, row = posi, padx = 10)
                ttk.Label(self.framelist[windowtype], text="Description: "+ACdict[key].description).grid(column = 3, row = posi, padx = 10)
                ttk.Button(self.framelist[windowtype], text="Edit", command= lambda: AddAC(parent,key)).grid(column = 4, row = posi)
                ttk.Button(self.framelist[windowtype], text="Delete", command = lambda: deleteasset(key,parent,windowtype)).grid(column = 5, row = posi)

            posi = 0
            for key in ACdict:
                ACline(assetlist.framelist[windowtype],key,posi,windowtype)
                posi += 1
            ttk.Button(assetlist.framelist[windowtype], text="Add Axlecounter", command= lambda: AddAC(parent,"")).grid(column=0, columnspan=10, row=500, sticky=E) # button to add an axlecounter

        for key in AClistdict:
            try:
                AClistdict[key].destroy()
            except:
                pass
    
        AClist(parent,windowtype)

def main():
    root = Tk()
    root.title("Section Monitor")
    SectionMonitor = ttk.Frame(root) # create main window for monitoring sections
    SectionMonitor.grid(column=0, row=0, sticky=W)
    ttk.Button(SectionMonitor, text="Add Section", command= lambda: AddSection(root)).grid(column=0, row=1, sticky=NW) # button to add a sectionline
    menubar = Menu(root)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Open", command=lambda:AClist)
    filemenu.add_command(label="Save", command=lambda:AClist)
    filemenu.add_separator()
    filemenu.add_command(label="Exit", command=root.quit)
    menubar.add_cascade(label="File", menu=filemenu)
    assetmenu = Menu(menubar,tearoff=1)
    assetmenu.add_command(label="Axle counters", command=lambda:assetlist(root,"Axle Counter"))
    assetmenu.add_command(label="Plungers", command=lambda:assetlist(root,"Plunger"))    
    menubar.add_cascade(label="Assets", menu=assetmenu)
    # display the menu
    root.config(menu=menubar)
    root.mainloop() # run infitite Tk loop

if __name__ == '__main__':
    main()


