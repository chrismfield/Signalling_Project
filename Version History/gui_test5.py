from tkinter import *
from tkinter import ttk
from serialtest2 import *

upcount = int(99)
downcount = str(99)

def goserial1(*args):
    addr = address_entry(int(addrst.get()))
    upc,downc = cmd1(addr)
    upcount.set(upc)
    downcount.set(downc)
    return 

def goserial2(*args): 
    addr = address_entry(int(addrst.get()))
    upc,downc = cmd2(addr)
    upcount.set(upc)
    downcount.set(downc)
    return


root = Tk()
root.title("Axlecounter Comms")

mainframe = ttk.Frame(root, padding="3 3 12 12")
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

addrst = IntVar()
upcount = IntVar()
downcount = IntVar()

addrst_entry = ttk.Entry(mainframe, width=7, textvariable=addrst)
addrst_entry.grid(column=2, row=0, sticky=(W, E))

ttk.Label(mainframe, textvariable=addrst).grid(column=2, row=1, sticky=(W, E))
ttk.Button(mainframe, text="Get Count", command=goserial1).grid(column=1, row=2, sticky=W)
ttk.Button(mainframe, text="Clear Count", command=goserial2).grid(column=2, row=2, sticky=W)

ttk.Label(mainframe, text="Enter Axlecounter Address").grid(column=0, row=0, sticky=W)
ttk.Label(mainframe, text="Current Address:").grid(column=0, row=1, sticky=E)
ttk.Label(mainframe, text="upcount:").grid(column=0, row=3, sticky=E)
ttk.Label(mainframe, text="downcount").grid(column=0, row=4, sticky=E)
ttk.Label(mainframe, textvariable=upcount).grid(column=2, row=3, sticky=(W, E))
ttk.Label(mainframe, textvariable=downcount).grid(column=2, row=4, sticky=(W, E))

for child in mainframe.winfo_children(): child.grid_configure(padx=5, pady=5)

addrst_entry.focus()
root.bind('<Return>', goserial1)

root.mainloop()

