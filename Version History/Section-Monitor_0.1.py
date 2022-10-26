from tkinter import *
from tkinter import ttk
import minimalmodbus

Sectionlist = [] # list for containing instances of sections
AClist = [] # list for containing instances of axlecounters
Signallist = [] # list for containing instances of Signals
Plungerlist = [] # list for containing instances of Plungers
Pointslist = [] # list for containing instances of Points
Routeslist = [] # list for containing instances of Routes

class axlecounters:
    def __init__(self):
        self.mode = ""         #mode = axlecount, simple trigger or directional trigger
        self.address = ""    #address
        self.ref = ""    #Freetext Reference
        self.description = "" #Freetext description

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


class lever:
    #for later on!
    pass

class sectionsetupframe:
    def __init__(self, sectionref):
        pass

class sectionline:
    def __init__(self, parent, posi):
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
        SectionRef = ttk.Entry(self.sectionframe, width=7, textvariable=sectionref) # sectionref entry
        SectionRef.grid(column=1, row=0, sticky=W)
        ttk.Label(self.sectionframe, text="Description:").grid(column=2, row=0, sticky=W)
        Descript = ttk.Entry(self.sectionframe, width=7, textvariable=description) # sectionref entry
        Descript.grid(column=3, row=0, sticky=W)
        ttk.Label(self.sectionframe, text="Status:"+" AXLECOUNT GOES HERE ").grid(column=49,row=0) # add status variable in here.        
        ttk.Button(self.sectionframe, text="Remove Section", command=removesection).grid(column=50, row=0) # destroy self button (does not yet destroy the instance of the class)
        SectionRef.bind("<FocusOut>", Update)
        Descript.bind("<FocusOut>", Update)        
        #need to create an associated instance of a section and assign it with the variables - need to do this when updated.



class sectionmonitor:
    def __init__(self):
        pass



def AddSection(root):

    def WriteSection():
        sectionclassname = sectionref.get() # get the name of the class - is this really necessary, should I just assign a name in code?
        sectionclassname = sections # create an instance of a section with the name just aquired
        sectionclassname.ref = sectionref.get() # assign the ref to the variable
        sectionclassname.description = description.get() # assign the description to the variable
        sectionclassname.mode = mode.get()
        sectionclassname.inctrig = inctrig.get()
        sectionclassname.dectrig = dectrig.get()
        Sectionlist.append(sectionclassname) #add section to the list of sections (Sectionlist) - not sure if this works properly
        print(sectionclassname.ref,sectionclassname.description,Sectionlist)
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
    
def main():
    root = Tk()
    root.title("Section Monitor")
    SectionMonitor = ttk.Frame(root) # create main window for monitoring sections
    SectionMonitor.grid(column=0, row=0, sticky=W)
    ttk.Button(SectionMonitor, text="Add Section", command= lambda: AddSection(root)).grid(column=0, row=0, sticky=NW) # button to add a sectionline
    root.mainloop() # run infitite Tk loop

if __name__ == '__main__':
    main()


