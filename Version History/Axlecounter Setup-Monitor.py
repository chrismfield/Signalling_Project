from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import serial
from struct import *
import serial.tools.list_ports

comportlist = [comport.device for comport in serial.tools.list_ports.comports()]

def cmd1(addr,comport):
        ser = serial.Serial(comport, 19200, timeout=2)
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 1 # function code
        #        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(5)
        ser.close()
#        print("Start:",s[0],"\n","Address:",s[1],"\n","Function:",s[2],"\n","Upcount:",s[3],"\n","Downcount:",s[4])
        return s[3],s[4]

def cmd2(addr,comport):
        ser = serial.Serial(comport, 19200, timeout=2)
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 2 # function code
#        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(5)
        ser.close()
        print("Start:",s[0],"\n","Address:",s[1],"\n","Function:",s[2],"\n","Upcount:",s[3],"\n","Downcount:",s[4])
        return s[3],s[4]

def cmd99():
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 99 # function code
#        o[3] = crc # crc or lrc?
        ser.write(o)
        d = ser.readline().decode("ascii")
        print(d)
        list(d)
        ser.close()
        return

def cmd98():
        o = bytearray(12)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 98 # function code
        o[3:12] = s[3:12]
#        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(12)
        print(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11])
        ser.close()
        return        

def cmd97():
        o = bytearray(3)
        o[0] = 254 # start of frame identifier
        o[1] = addr # address of slave to communicate with
        o[2] = 97 # function code
#        o[3] = crc # crc or lrc?
        ser.write(o)
        s = ser.read(12)
        print(s[0], s[1], s[2], s[3], s[4], s[5], s[6], s[7], s[8], s[9], s[10], s[11])
        ser.close()
        return

root = Tk()
root.title("Axlecounter Comms")

mainframe = ttk.Frame(root, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
mainframe.grid(column=0, row=0, sticky=(N, W, E, S))
mainframe.columnconfigure(0, weight=1)
mainframe.rowconfigure(0, weight=1)

ttk.Label(mainframe, text="Com port:").grid(column=0, row=0, sticky=E)
listbox = Listbox(mainframe, selectmode = SINGLE, height=1)
listbox.grid(column=2, row=0, sticky=(W, E))
for n in comportlist:
    listbox.insert(END, n)


#comport_entry = ttk.Entry(mainframe, width=7, textvariable=comport)
#comport_entry.grid(column=2, row=0, sticky=(W, E))

class acwindow:
    def __init__(self, posi,comport):
        self.posi = posi

        def goserial1(*args):
                try:
                        comport = listbox.get(listbox.curselection())
                        print(comport)
                except TclError:
                        messagebox.showinfo("Error", "Please select a Com Port")
                try:
                        self.upc,self.downc = cmd1(int(addrst.get()),comport)
                        upcount.set(self.upc)
                        downcount.set(self.downc)
                except IndexError:
                        messagebox.showinfo("Error", "No response from module")         
                return 

        def goserialclr1(*args):
                try:
                        self.upc,self.downc = cmd2(int(addrst.get(),comport))
                        upcount.set(self.upc)
                        downcount.set(self.downc)
                except IndexError:
                        messagebox.showinfo("Error", "No response from module")
                return
    
        mainframe = ttk.Frame(root, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
        mainframe.grid(column=posi, row=1, sticky=(N, W, E, S))
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
comport = "COM6"
x = acwindow(0,comport)
y = acwindow(1,comport)
z = acwindow(2,comport)

def setupwindow(*args):

    setupbox = Tk()
    setupbox.title = "Diagnostics and Setup"
    setupframe = ttk.Frame(setupbox, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
    setupframe.grid()

    #retrieve the parameters and variables from axlecounter here
    HED1 = "1"
    ttk.Label(setupframe, text="HED1=").grid(column=0, row=0)
    ttk.Label(setupframe, text=comport).grid(column=1, row=0)    
    return

#setupwindow("COM6")   

menu = Menu(root)
root.config(menu=menu)
setupmenu = Menu(menu)
menu.add_cascade(label="Setup", menu=setupmenu)
setupmenu.add_command(label="Setup", command=setupwindow)

root.mainloop()



