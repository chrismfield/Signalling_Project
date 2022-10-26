from tkinter import *
from tkinter import ttk
from serialtest3 import *

root = Tk()
root.title("Axlecounter Comms")

class acwindow:
    def __init__(self, posi):
        self.posi = posi

        def goserial1(*args):
            self.upc,self.downc = cmd1(int(addrst.get()))
            upcount.set(self.upc)
            downcount.set(self.downc)
            root.after(100,goserial1)
            return 

        def goserialclr1(*args): 
            self.upc,self.downc = cmd2(int(addrst.get()))
            upcount.set(self.upc)
            downcount.set(self.downc)
            return
    
        mainframe = ttk.Frame(root, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
        mainframe.grid(column=posi, row=0, sticky=(N, W, E, S))
        mainframe.columnconfigure(0, weight=1)
        mainframe.rowconfigure(0, weight=1)

        addrst = IntVar()
        upcount = IntVar()
        downcount = IntVar()

        addrst_entry = ttk.Entry(mainframe, width=7, textvariable=addrst)
        addrst_entry.grid(column=2, row=0, sticky=(W, E))

        ttk.Label(mainframe, textvariable=addrst).grid(column=2, row=1, sticky=(W, E))
        ttk.Button(mainframe, text="Start", command=goserial1).grid(column=1, row=2, sticky=W)
        ttk.Button(mainframe, text="Clear Count", command=goserialclr1).grid(column=2, row=2, sticky=W)

        ttk.Label(mainframe, text="Enter Axlecounter Address").grid(column=0, row=0, sticky=W)
        ttk.Label(mainframe, text="Current Address:").grid(column=0, row=1, sticky=E)
        ttk.Label(mainframe, text="upcount:").grid(column=0, row=3, sticky=E)
        ttk.Label(mainframe, text="downcount").grid(column=0, row=4, sticky=E)
        ttk.Label(mainframe, textvariable=upcount).grid(column=2, row=3, sticky=(W, E))
        ttk.Label(mainframe, textvariable=downcount).grid(column=2, row=4, sticky=(W, E))

        for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

        addrst_entry.focus()
        root.bind('<Return>', goserial1)

x = acwindow(0)
y = acwindow(1)
z = acwindow(2)

root.mainloop()



