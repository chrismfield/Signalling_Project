from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import minimalmodbus
import serial.tools.list_ports
import time

comportlist = [comport.device for comport in serial.tools.list_ports.comports()]
comport = comportlist[-1]

class acframe: # axlecounter window class
    items = []  # list for containing instances of axlecounter frame
    def __init__(self, parent, posi, rowposi): #posi arguments allow multiple instances to be tiled
        self.parent = parent
        self.posi = posi
        self.rowposi = rowposi
        self.address = 0

        def goserial1(*args):
                try:
                    print(comport)
                    axlecounter = minimalmodbus.Instrument(comport, int(addrst.get()))  # update comport and slave address
                    axlecounter.debug = True
                    self.upc = axlecounter.read_register(13)  # Load 1 register from location 13 (upcount)
                    self.downc = axlecounter.read_register(14)
                    upcount.set(self.upc)
                    downcount.set(self.downc)
                except IndexError:
                        messagebox.showinfo("Error", "No response from module")
                #parent.after(5000, goserial1())
                return 

        def goserialclr1(*args):
                try:
                    axlecounter = minimalmodbus.Instrument(comport, int(addrst.get()))  # update comport and slave address
                    axlecounter.debug = True
                    axlecounter.write_register(13, 0, functioncode=6)
                    axlecounter.write_register(14, 0, functioncode=6)
                    self.upc = axlecounter.read_register(13)  # Load 1 register from location 13 (upcount)
                    self.downc = axlecounter.read_register(14)
                    upcount.set(self.upc)
                    downcount.set(self.downc)
                except IndexError:
                        messagebox.showinfo("Error", "No response from module")
                return
    
        self.subframe = ttk.Frame(parent, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
        self.subframe.grid(column=posi, row=rowposi, sticky=(N, W, E, S))
        self.subframe.columnconfigure(0, weight=1)
        self.subframe.rowconfigure(0, weight=1)

        addrst = IntVar()
        upcount = IntVar()
        downcount = IntVar()

        addrst_entry = ttk.Entry(self.subframe, width=7, textvariable=addrst, validate="focusout",
                                 validatecommand=lambda: print(addrst.get()))
        addrst_entry.grid(column=2, row=0, sticky=(W, E))

        ttk.Label(self.subframe, textvariable=addrst).grid(column=2, row=1, sticky=(W, E))
        ttk.Button(self.subframe, text="Start", command=lambda:goserial1()).grid(column=1, row=2, sticky=W)
        ttk.Button(self.subframe, text="Clear Count", command=goserialclr1).grid(column=2, row=2, sticky=W)

        ttk.Label(self.subframe, text="Enter Axlecounter Address").grid(column=0, row=0, sticky=W)
        ttk.Label(self.subframe, text="Current Address:").grid(column=0, row=1, sticky=E)
        ttk.Label(self.subframe, text="upcount:").grid(column=0, row=3, sticky=E)
        ttk.Label(self.subframe, text="downcount").grid(column=0, row=4, sticky=E)
        ttk.Label(self.subframe, textvariable=upcount).grid(column=2, row=3, sticky=(W, E))
        ttk.Label(self.subframe, textvariable=downcount).grid(column=2, row=4, sticky=(W, E))

        for child in self.subframe.winfo_children(): child.grid_configure(padx=5, pady=5)

        addrst_entry.focus()
        parent.bind('<Return>', goserial1)


def creatediags(parent,wins):
    print("Old list length: ", len(acframe.items))
    if wins < len(acframe.items):
        for i in range(len(acframe.items)):
            if (i+1) > wins:
                acframe.items[-1].subframe.destroy()
                del acframe.items[-1]
    if wins > len(acframe.items):
        for x in range(wins):
            if (x+1) > len(acframe.items):
                y = 1
                if x > 3 and x < 8:
                    y = 2
                    x = x - 4
                if x > 7:
                    y = 3
                    x = x - 8   
                acframe.items.append(acframe(parent,x,y)) #this just adds a class with the same name to the list.

    print("New list length: ", len(acframe.items))


class setupwindow: # need to change to have an add button and a remove button, and probably give each instace a unique
    # reference. Could use the address? But what if it is necessary to change the address? Then it all goes wrong.
        def __init__(self,master):
                self.master = master
                self.qtyAC = IntVar()
                global comport

                def buttonpress():
                        global comport
                        comport = listbox.get(listbox.curselection())
                        print(comport)
                        self.QtyAC = self.qtyAC.get()
                        creatediags(self.master,self.qtyAC.get())
                        setupwin.destroy()
                        
                setupwin = Toplevel(master,takefocus=True)
                setupframe = ttk.Frame(setupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
                setupframe.pack()

                #retrieve the parameters and variables from axlecounter here
                HED1 = "1"
                ttk.Label(setupframe, text="HED1=").grid(column=0, row=0)
                ttk.Label(setupframe, text="ComPort").grid(column=1, row=0)
                #pdb.set_trace()
                NoOfCounters = Entry(setupframe, width=7, textvariable=self.qtyAC)
                NoOfCounters.grid(column=0,row=1)
                NoOfCounters.delete("0")
                NoOfCounters.insert(0, "2")
                ttk.Label(setupframe, text="Enter Number of Counters:").grid(column=0, row=2, sticky=E)
                ttk.Button(setupframe, text="OK", command=buttonpress).grid(column=1, row=2, sticky=W)

                ttk.Label(setupframe, text="Com port:").grid(column=0, row=0, sticky=E)
                listbox = Listbox(setupframe, selectmode = SINGLE, height=1)
                listbox.grid(column=2, row=0, sticky=(W, E))
                for n in comportlist:
                    listbox.insert(END, n)
                listbox.select_set(0)


# this is still not working
           
def main():
    root = Tk()
    mainwin = ttk.Frame(root)
    creatediags(mainwin,3)
    root.title("Axlecounter Comms")

    
    def setupmenu(parent):

        def cmdsetup():
            cc = setupwindow(parent)

        menubar = Menu(parent)
        menubar.add_command(label="Setup", command=cmdsetup)   
        root.config(menu=menubar)    

    ab = setupmenu(mainwin)
    mainwin.pack()    
    root.mainloop()
    
    #time.sleep(5.5)    # pause 5.5 seconds debugger


if __name__ == '__main__':
    main()


