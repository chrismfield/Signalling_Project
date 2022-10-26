from tkinter import *
from tkinter import ttk
from tkinter import messagebox
import serial
from struct import *
import pdb; 
import serial.tools.list_ports
import time

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

#comport_entry = ttk.Entry(mainframe, width=7, textvariable=comport)
#comport_entry.grid(column=2, row=0, sticky=(W, E))

class acframe: # axlecounter window class
    def __init__(self, parent, posi, rowposi, comport): #posi arguments allow multiple instances to be tiled
        self.parent = parent
        self.posi = posi
        self.rowposi = rowposi

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
    
        subframe = ttk.Frame(parent, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
        subframe.grid(column=posi, row=rowposi, sticky=(N, W, E, S))
        subframe.columnconfigure(0, weight=1)
        subframe.rowconfigure(0, weight=1)

        addrst = IntVar()
        upcount = IntVar()
        downcount = IntVar()

        addrst_entry = ttk.Entry(subframe, width=7, textvariable=addrst)
        addrst_entry.grid(column=2, row=0, sticky=(W, E))

        ttk.Label(subframe, textvariable=addrst).grid(column=2, row=1, sticky=(W, E))
        ttk.Button(subframe, text="Start", command=goserial1).grid(column=1, row=2, sticky=W)
        ttk.Button(subframe, text="Clear Count", command=goserialclr1).grid(column=2, row=2, sticky=W)

        ttk.Label(subframe, text="Enter Axlecounter Address").grid(column=0, row=0, sticky=W)
        ttk.Label(subframe, text="Current Address:").grid(column=0, row=1, sticky=E)
        ttk.Label(subframe, text="upcount:").grid(column=0, row=3, sticky=E)
        ttk.Label(subframe, text="downcount").grid(column=0, row=4, sticky=E)
        ttk.Label(subframe, textvariable=upcount).grid(column=2, row=3, sticky=(W, E))
        ttk.Label(subframe, textvariable=downcount).grid(column=2, row=4, sticky=(W, E))

        for child in subframe.winfo_children(): child.grid_configure(padx=5, pady=5)

        addrst_entry.focus()
        parent.bind('<Return>', goserial1)


def creatediags(parent,wins):
    items = []
    comport = "COM6"    
    for x in range(wins):
        y = 1
        if x > 3 and x < 8:
            y = 2
            x = x - 4
        if x > 7:
            y = 3
            x = x - 8
        items.append(acframe(parent,x,y,"COM6"))


class setupwindow:
        def __init__(self,master):
                self.master = master
                self.qtyAC = IntVar()        

                def buttonpress():
                        self.QtyAC = self.qtyAC.get()
                        print(self.QtyAC)
                        creatediags(self.master,self.qtyAC.get())
                        setupframe.destroy()
                        
                setupwin = Toplevel(master,takefocus=True)
                setupframe = ttk.Frame(setupwin, padding="3 3 12 12", borderwidth=1, relief=SUNKEN)
                setupframe.pack()

                #retrieve the parameters and variables from axlecounter here
                HED1 = "1"
                ttk.Label(setupframe, text="HED1=").grid(column=0, row=0)
                ttk.Label(setupframe, text="COM1").grid(column=1, row=0)
                #pdb.set_trace()
                NoOfCounters = Entry(setupframe, width=7, textvariable=self.qtyAC)
                NoOfCounters.grid(column=0,row=1)
                ttk.Label(setupframe, text="Enter Number of Counters:").grid(column=0, row=2, sticky=E)
                ttk.Button(setupframe, text="OK", command=buttonpress).grid(column=1, row=2, sticky=W)

                print("herenow")

                ttk.Label(setupframe, text="Com port:").grid(column=0, row=0, sticky=E)
                listbox = Listbox(setupframe, selectmode = SINGLE, height=1)
                listbox.grid(column=2, row=0, sticky=(W, E))
                for n in comportlist:
                    listbox.insert(END, n)

                print(self.qtyAC.get())



           
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


