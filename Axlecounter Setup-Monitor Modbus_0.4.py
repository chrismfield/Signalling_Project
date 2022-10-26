from tkinter import *
from tkinter import ttk
import minimalmodbus
import serial.tools.list_ports
import datetime

try:
    comportlist = [comport.device for comport in serial.tools.list_ports.comports()]
    comport = comportlist[-1]
except:
    pass


class ACFrame:  # axlecounter window class
    items = []  # list for containing instances of axlecounter frame

    def __init__(self, parent, posi, rowposi):  # posi arguments allow multiple instances to be tiled
        self.parent = parent
        self.posi = posi
        self.rowposi = rowposi
        self.address = 0

        self.subframe = ttk.Frame(parent, padding="12 12 12 12", borderwidth=1, relief=SUNKEN)
        self.subframe.grid(column=posi, row=rowposi, sticky="N, W, E, S")
        self.subframe.columnconfigure(0, weight=1)
        self.subframe.rowconfigure(0, weight=1)

        self.addrst = IntVar()
        self.upcount = IntVar()
        self.downcount = IntVar()
        self.hall1sens = IntVar()
        self.hall2sens = IntVar()
        self.hall3sens = IntVar()
        self.hall1hys = IntVar()
        self.hall2hys = IntVar()
        self.hall3hys = IntVar()
        self.hall1dur = IntVar()
        self.hall2dur = IntVar()
        self.hall3dur = IntVar()
        self.hall1ssv = IntVar()
        self.hall2ssv = IntVar()
        self.hall3ssv = IntVar()

        addrst_entry = ttk.Entry(self.subframe, width=7, textvariable=self.addrst, validate="focusout",
                                 validatecommand=lambda: print(self.addrst.get()))
        addrst_entry.grid(column=2, row=0, sticky="W, E")

        ttk.Label(self.subframe, textvariable=self.addrst).grid(column=2, row=1, sticky="W, E")
        ttk.Button(self.subframe, text="Start", command=lambda: self.goserial1()).grid(columnspan=2, column=3, row=0,
                                                                                       sticky=W)
        ttk.Button(self.subframe, text="Clear Count", command=self.goserialclr1).grid(columnspan=2, rowspan=2, column=3,
                                                                                      row=3, sticky=W)
        ttk.Separator(self.subframe, orient='horizontal').grid(sticky=EW, columnspan=5, column=0, row=2)
        ttk.Label(self.subframe, text="Enter Axlecounter Address:").grid(column=0, row=0, sticky=W)
        ttk.Label(self.subframe, text="Current Address:").grid(column=0, row=1, sticky=E)
        ttk.Label(self.subframe, text="upcount:").grid(column=0, row=3, sticky=E)
        ttk.Label(self.subframe, text="downcount").grid(column=0, row=4, sticky=E)
        ttk.Label(self.subframe, textvariable=self.upcount).grid(column=2, row=3, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.downcount).grid(column=2, row=4, sticky="W, E")
        ttk.Separator(self.subframe, orient='horizontal').grid(sticky=EW, columnspan=5, column=0, row=5)
        # Parameter Adjustment

        ttk.Label(self.subframe, text="Hall 1 Sensitivity:").grid(column=0, row=6, sticky=W)
        ttk.Label(self.subframe, text="Hall 2 Sensitivity:").grid(column=0, row=7, sticky=W)
        ttk.Label(self.subframe, text="Hall 3 Sensitivity:").grid(column=0, row=8, sticky=W)
        ttk.Label(self.subframe, textvariable=self.hall1sens).grid(column=2, row=6, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall2sens).grid(column=2, row=7, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall3sens).grid(column=2, row=8, sticky="W, E")
        ttk.Label(self.subframe, text="Hall 1 Hysteresis:").grid(column=0, row=9, sticky=W)
        ttk.Label(self.subframe, text="Hall 2 Hysteresis:").grid(column=0, row=10, sticky=W)
        ttk.Label(self.subframe, text="Hall 3 Hysteresis:").grid(column=0, row=11, sticky=W)
        ttk.Label(self.subframe, textvariable=self.hall1hys).grid(column=2, row=9, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall2hys).grid(column=2, row=10, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall3hys).grid(column=2, row=11, sticky="W, E")
        ttk.Label(self.subframe, text="Hall 1 Duration:").grid(column=0, row=12, sticky=W)
        ttk.Label(self.subframe, text="Hall 2 Duration:").grid(column=0, row=13, sticky=W)
        ttk.Label(self.subframe, text="Hall 3 Duration:").grid(column=0, row=14, sticky=W)
        ttk.Label(self.subframe, textvariable=self.hall1dur).grid(column=2, row=12, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall2dur).grid(column=2, row=13, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall3dur).grid(column=2, row=14, sticky="W, E")
        ttk.Label(self.subframe, text="Hall 1 Session Static Value:").grid(column=0, row=15, sticky=W)
        ttk.Label(self.subframe, text="Hall 2 Session Static Value:").grid(column=0, row=16, sticky=W)
        ttk.Label(self.subframe, text="Hall 3 Session Static Value:").grid(column=0, row=17, sticky=W)
        ttk.Label(self.subframe, textvariable=self.hall1ssv).grid(column=2, row=15, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall2ssv).grid(column=2, row=16, sticky="W, E")
        ttk.Label(self.subframe, textvariable=self.hall3ssv).grid(column=2, row=17, sticky="W, E")
        """Adjustment Buttons For Hall Sensitivity"""
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(1, -5)) \
            .grid(column=3, row=6, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(1, 5)) \
            .grid(column=4, row=6, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(2, -5)) \
            .grid(column=3, row=7, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(2, 5)) \
            .grid(column=4, row=7, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(3, -5)) \
            .grid(column=3, row=8, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(3, 5)) \
            .grid(column=4, row=8, sticky=W)
        """Adjustment Buttons For Hall Hysteresis"""
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(4, -5)) \
            .grid(column=3, row=9, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(4, 5)) \
            .grid(column=4, row=9, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(5, -5)) \
            .grid(column=3, row=10, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(5, 5)) \
            .grid(column=4, row=10, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(6, -5)) \
            .grid(column=3, row=11, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(6, 5)) \
            .grid(column=4, row=11, sticky=W)
        """Adjustment Buttons For Hall Duration"""
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(7, -1)) \
            .grid(column=3, row=12, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(7, 1)) \
            .grid(column=4, row=12, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(8, -1)) \
            .grid(column=3, row=13, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(8, 1)) \
            .grid(column=4, row=13, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(9, -1)) \
            .grid(column=3, row=14, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(9, 1)) \
            .grid(column=4, row=14, sticky=W)

        for child in self.subframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        addrst_entry.focus()
        parent.bind('<Return>', self.goserial1)
        self.addrst.trace_add('write', self.readparameters)

    def goserial1(self):
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.debug = False
            self.upcount.set(axlecounter.read_register(13))  # Load 1 register from location 13 (upcount)
            self.downcount.set(axlecounter.read_register(14))
        except:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed with module address " + str(
                    self.addrst.get()))
            except:
                pass
        self.parent.after(500, self.goserial1)
        return

    def goserialclr1(self):
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.debug = False
            axlecounter.write_register(13, 0, functioncode=6)
            axlecounter.write_register(14, 0, functioncode=6)
            self.upcount.set(axlecounter.read_register(13))  # Load 1 register from location 13 (upcount)
            self.downcount.set(axlecounter.read_register(14))
        except:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed with module address " + str(
                    self.addrst.get()))
            except:
                pass
        return

    def readparameters(self, *args):
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.debug = False
            self.hall1sens.set(axlecounter.read_register(1))  # Load 1 register from location 2 (hall1 sensitivity)
            self.hall2sens.set(axlecounter.read_register(2))
            self.hall3sens.set(axlecounter.read_register(3))
            self.hall1hys.set(axlecounter.read_register(4))  # Load 1 register from location 2 (hall1 hysteresis)
            self.hall2hys.set(axlecounter.read_register(5))
            self.hall3hys.set(axlecounter.read_register(6))
            self.hall1dur.set(axlecounter.read_register(7))  # Load 1 register from location 2 (hall1 duration)
            self.hall2dur.set(axlecounter.read_register(8))
            self.hall3dur.set(axlecounter.read_register(9))
            self.hall1ssv.set(
                axlecounter.read_register(10))  # Load 1 register from location 2 (hall1 static session value)
            self.hall2ssv.set(axlecounter.read_register(11))
            self.hall3ssv.set(axlecounter.read_register(12))
        except:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed with module address " + str(
                    self.addrst.get()))
            except:
                pass

    def adjustparameters(self, parameter, adjustment):
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.debug = False
            checkparameter = axlecounter.read_register(parameter)
            axlecounter.write_register(parameter, (checkparameter + adjustment), functioncode=6)
            self.readparameters()
        except:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed with module address " + str(
                    self.addrst.get()))
            except:
                pass


def creatediags(parent, wins):
    if wins < len(ACFrame.items):
        for i in range(len(ACFrame.items)):
            if (i + 1) > wins:
                ACFrame.items[-1].subframe.destroy()
                del ACFrame.items[-1]
    if wins > len(ACFrame.items):
        for x in range(wins):
            if (x + 1) > len(ACFrame.items):
                y = 1
                if x > 5:
                    pass
                else:
                    ACFrame.items.append(
                        ACFrame(parent, x, y))  # this just adds a class with the same name to the list.


class SetupWindow:  # need to change to have an add button and a remove button, and probably give each instace a unique
    # reference. Could use the address? But what if it is necessary to change the address? Then it all goes wrong.
    def __init__(self, master):
        self.master = master
        self.qtyAC = IntVar()
        global comport

        def buttonpress():
            global comport
            comport = combobox.get()
            print(comport)
            self.QtyAC = self.qtyAC.get()
            creatediags(self.master, self.qtyAC.get())
            setupwin.destroy()

        setupwin = Toplevel(master, takefocus=True)
        setupframe = ttk.Frame(setupwin, padding="3 3 12 12", borderwidth=2, relief=SUNKEN)
        # setupframe.columnconfigure(0, weight=1)
        # setupframe.rowconfigure(0, weight=1)

        ttk.Label(setupframe, text="Com port:").grid(column=0, row=0, sticky=E)
        combobox = ttk.Combobox(setupframe, values=comportlist)
        combobox.grid(column=1, row=0, sticky="W, E")
        combobox.set(comport)

        ttk.Label(setupframe, text="Enter Number of Counters:").grid(column=0, row=1, sticky=E)
        no_of_counters = Entry(setupframe, width=7, textvariable=self.qtyAC)
        no_of_counters.grid(column=1, row=1, sticky=W)
        no_of_counters.delete("0")
        no_of_counters.insert(0, str(len(ACFrame.items)))
        ttk.Button(setupframe, text="OK", command=buttonpress).grid(column=1, row=2, sticky=E)

        for child in setupframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        setupframe.pack()


def main():
    root = Tk()
    mainwin = ttk.Frame(root)
    creatediags(mainwin, 3)
    root.title("Axlecounter Comms")

    def setupmenu(parent):
        def cmdsetup():
            SetupWindow(parent)

        menubar = Menu(parent)
        menubar.add_command(label="Setup", command=cmdsetup)
        root.config(menu=menubar)

    setupmenu(mainwin)
    mainwin.pack()
    root.mainloop()

    # time.sleep(5.5)    # pause 5.5 seconds debugger


if __name__ == '__main__':
    main()
