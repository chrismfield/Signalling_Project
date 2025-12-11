from tkinter import *
from tkinter import ttk
import minimalmodbus
import serial.tools.list_ports
import datetime
import time

import logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

#try:
comportlist = [comport.device for comport in serial.tools.list_ports.comports()]
comport = comportlist[0]
baud = 19200
#except:
#    pass


class ACFrame:  # axlecounter window class
    items = []  # list for containing instances of axlecounter frame

    def __init__(self, parent, posi, rowposi):  # posi arguments allow multiple instances to be tiled
        self.parent = parent
        self.posi = posi
        self.rowposi = rowposi
        self.address = 0
        self.active = False


        self.subframe = ttk.Frame(parent, padding="12 12 12 12", borderwidth=1, relief=SUNKEN)
        self.subframe.grid(column=posi, row=rowposi, sticky="N, W, E, S")
        self.subframe.columnconfigure(0, weight=1)
        self.subframe.rowconfigure(0, weight=1)

        self.addrst = IntVar()
        self.addrst.set(247)
        self.buttontext = StringVar()
        self.buttontext.set("Start")
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
        self.hall1live = IntVar()
        self.hall2live = IntVar()
        self.hall3live = IntVar()


        addrst_entry = ttk.Entry(self.subframe, width=7, textvariable=self.addrst, validate="focusout",
                                 validatecommand=lambda: print(self.addrst.get()))
        addrst_entry.grid(column=2, row=0, sticky="W, E")

        ttk.Label(self.subframe, textvariable=self.addrst).grid(column=2, row=1, sticky="W, E")
        ttk.Button(self.subframe, textvariable=self.buttontext, command=lambda: self.startbutton()).grid(columnspan=2, column=3, row=0,
                                                                                       sticky=W)
        ttk.Button(self.subframe, text="Board Setup", command=lambda: self.BoardSetupWindow(self.subframe, self.addrst.get())).grid(columnspan=2, column=3, row=1,
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
        if True:
            ttk.Label(self.subframe, text="Hall 1 Live Value:").grid(column=0, row=19, sticky=W)
            ttk.Label(self.subframe, text="Hall 2 Live Value:").grid(column=0, row=20, sticky=W)
            ttk.Label(self.subframe, text="Hall 3 Live Value:").grid(column=0, row=21, sticky=W)
            ttk.Label(self.subframe, textvariable=self.hall1live).grid(column=2, row=19, sticky="W, E")
            ttk.Label(self.subframe, textvariable=self.hall2live).grid(column=2, row=20, sticky="W, E")
            ttk.Label(self.subframe, textvariable=self.hall3live).grid(column=2, row=21, sticky="W, E")


        """Adjustment Buttons For Hall Sensitivity"""
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(201, -5, (self.addrst.get()))) \
            .grid(column=3, row=6, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(201, 5, (self.addrst.get()))) \
            .grid(column=4, row=6, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(202, -5, (self.addrst.get()))) \
            .grid(column=3, row=7, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(202, 5, (self.addrst.get()))) \
            .grid(column=4, row=7, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(203, -5, (self.addrst.get()))) \
            .grid(column=3, row=8, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(203, 5, (self.addrst.get()))) \
            .grid(column=4, row=8, sticky=W)
        """Adjustment Buttons For Hall Hysteresis"""
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(204, -5, (self.addrst.get()))) \
            .grid(column=3, row=9, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(204, 5, (self.addrst.get()))) \
            .grid(column=4, row=9, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(205, -5, (self.addrst.get()))) \
            .grid(column=3, row=10, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(205, 5, (self.addrst.get()))) \
            .grid(column=4, row=10, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(206, -5, (self.addrst.get()))) \
            .grid(column=3, row=11, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(206, 5, (self.addrst.get()))) \
            .grid(column=4, row=11, sticky=W)
        """Adjustment Buttons For Hall Duration"""
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(207, -1, (self.addrst.get()))) \
            .grid(column=3, row=12, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(207, 1, (self.addrst.get()))) \
            .grid(column=4, row=12, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(208, -1, (self.addrst.get()))) \
            .grid(column=3, row=13, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(208, 1, (self.addrst.get()))) \
            .grid(column=4, row=13, sticky=W)
        ttk.Button(self.subframe, text='<', width=2, command=lambda: self.adjustparameters(209, -1, (self.addrst.get()))) \
            .grid(column=3, row=14, sticky=W)
        ttk.Button(self.subframe, text='>', width=2, command=lambda: self.adjustparameters(209, 1, (self.addrst.get()))) \
            .grid(column=4, row=14, sticky=W)
        ttk.Button(self.subframe, text='Set Defaults', width=25, command=lambda: self.set_defaults(self.addrst.get())) \
            .grid(column=0, row=22, sticky=W)

        for child in self.subframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        addrst_entry.focus()
        parent.bind('<Return>', self.goserial1)
        self.addrst.trace_add('write', self.readparameters)

    def set_defaults(self, address):

        #set default hall-effect device thresholds
        self.writeRegValue(201, 100, address)
        self.writeRegValue(202, 100, address)
        self.writeRegValue(203, 100, address)
        self.writeRegValue(204, 50, address)
        self.writeRegValue(205, 50, address)
        self.writeRegValue(206, 50, address)
        self.writeRegValue(207, 0, address)
        self.writeRegValue(208, 0, address)
        self.writeRegValue(209, 0, address)
        #set to 19200 baud:
        self.writeRegValue(101, 1, address)
        #set loging off:
        self.writeRegValue(103, 0, address)


    def startbutton(self):
        self.active = not self.active
        self.readparameters()
        self.goserial1()
        if self.active:
            self.buttontext.set("Stop")
        else:
            self.buttontext.set("Start")

    def goserial1(self):
        if(self.paused):
            self.parent.after(500, self.goserial1)
            return
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.serial.timeout = 0.5
            axlecounter.serial.baudrate = baud
            axlecounter.debug = False
            self.upcount.set(axlecounter.read_register(13))  # Load 1 register from location 13 (upcount)
            time.sleep(0.002)
            self.downcount.set(axlecounter.read_register(14))
            time.sleep(0.002)
            self.hall1ssv.set(axlecounter.read_register(10))  # Load EMA values
            time.sleep(0.002)
            self.hall2ssv.set(axlecounter.read_register(11))
            time.sleep(0.002)
            self.hall3ssv.set(axlecounter.read_register(12))
            time.sleep(0.002)
            if True:
                self.hall1live.set(axlecounter.read_register(20))
                time.sleep(0.002)
                self.hall2live.set(axlecounter.read_register(21))
                time.sleep(0.002)
                self.hall3live.set(axlecounter.read_register(22))
                time.sleep(0.002)
        except Exception as e:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed (goserial1) with module address " + str(
                    self.addrst.get())+": " + str(e))
            except:
                pass
        if self.active:
            self.parent.after(500, self.goserial1)
        return

    def goserialclr1(self):
        if(self.paused):
            self.parent.after(500, self.goserialclr1)
            return
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.serial.timeout = 0.5
            axlecounter.serial.baudrate = baud
            axlecounter.debug = False
            axlecounter.write_register(13, 0, functioncode=6)
            axlecounter.write_register(14, 0, functioncode=6)
            self.upcount.set(axlecounter.read_register(13))  # Load 1 register from location 13 (upcount)
            time.sleep(0.002)
            self.downcount.set(axlecounter.read_register(14))
            time.sleep(0.002)
        except Exception as e:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed (goserialclr1) with module address " + str(
                    self.addrst.get())+": " + str(e))
            except:
                pass
        return

    def readparameters(self, *args):
        self.paused = True
        time.sleep(0.5)
        try:
            axlecounter = minimalmodbus.Instrument(comport, int(self.addrst.get()))  # update comport and slave address
            axlecounter.serial.timeout = 0.5
            axlecounter.serial.baudrate = baud
            axlecounter.debug = False
            time.sleep(0.002)
            self.hall1sens.set(axlecounter.read_register(201))  # Load 1 register from location 2 (hall1 sensitivity)
            time.sleep(0.002)
            self.hall2sens.set(axlecounter.read_register(202))
            time.sleep(0.002)
            self.hall3sens.set(axlecounter.read_register(203))
            time.sleep(0.002)
            self.hall1hys.set(axlecounter.read_register(204))  # Load 1 register from location 2 (hall1 hysteresis)
            time.sleep(0.002)
            self.hall2hys.set(axlecounter.read_register(205))
            time.sleep(0.002)
            self.hall3hys.set(axlecounter.read_register(206))
            time.sleep(0.002)
            self.hall1dur.set(axlecounter.read_register(207))  # Load 1 register from location 2 (hall1 duration)
            time.sleep(0.002)
            self.hall2dur.set(axlecounter.read_register(208))
            time.sleep(0.002)
            self.hall3dur.set(axlecounter.read_register(209))
            time.sleep(0.002)
            self.hall1ssv.set(axlecounter.read_register(10))  # Load 1 register from location 2 (hall1 static session value)
            time.sleep(0.002)
            self.hall2ssv.set(axlecounter.read_register(11))
            time.sleep(0.002)
            self.hall3ssv.set(axlecounter.read_register(12))
            if not self.active:
                self.goserial1()
        except Exception as e:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed (readparameters) with module address " + str(
                    self.addrst.get())+": " + str(e))
            except:
                pass
        self.paused = False

    def read_parameter(self, address, register):
        try:
            axlecounter = minimalmodbus.Instrument(comport, address)  # update comport and slave address
            axlecounter.serial.timeout = 0.5
            axlecounter.serial.baudrate = baud
            axlecounter.debug = False
            time.sleep(0.002)
            return axlecounter.read_register(register)
        except Exception as e:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed (adjustparameters) with module address " + str(
                    self.addrst.get())+": " + str(e))
            except:
                pass

    def adjustparameters(self, parameter, adjustment, address):
        self.paused = True
        time.sleep(0.5)
        try:
            axlecounter = minimalmodbus.Instrument(comport, address) # update comport and slave address
            axlecounter.debug = False
            axlecounter.serial.timeout = 0.5
            axlecounter.serial.baudrate = baud
            checkparameter = axlecounter.read_register(parameter)
            time.sleep(0.002)
            newValue = checkparameter + adjustment
            if newValue > 65535:
                newValue = 0
            if newValue < 0:
               newValue = 65535
            axlecounter.write_register(parameter, newValue, functioncode=6)
            self.readparameters()
            return True
        except Exception as e:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed (adjustparameters) with module address " + str(
                    self.addrst.get())+": " + str(e))
            except:
                pass
        self.paused = False
    
    def writeRegValue(self, parameter, newValue, address):
        self.paused = True
        time.sleep(0.5)
        try:
            axlecounter = minimalmodbus.Instrument(comport, address) # update comport and slave address
            axlecounter.debug = False
            axlecounter.serial.timeout = 0.5
            axlecounter.serial.baudrate = baud
            checkparameter = axlecounter.read_register(parameter)
            time.sleep(0.002)
            axlecounter.write_register(parameter, newValue, functioncode=6)
            self.readparameters()
            return True
        except Exception as e:
            try:
                print(datetime.datetime.now().strftime("%H:%M:%S") + " Comms failed (adjustparameters) with module address " + str(
                    self.addrst.get())+": " + str(e))
            except:
                pass
        self.paused = False


    #Window for changing board address, setting baud rate on board, configuring logging, and setting board type
    def BoardSetupWindow(self, parent, address):

            new_address = IntVar()

            def set_new_address(old_address, new_address):
                print("New address: " + str(new_address) + " - " + str(new_address * 1))
                if self.writeRegValue(100, new_address * 1, old_address):
                    board_setup_window.destroy()
                    self.addrst.set(new_address)

            board_setup_window = Toplevel(parent, takefocus=True)
            frame = ttk.Frame(board_setup_window, padding="3 3 12 12", borderwidth=2, relief=SUNKEN)

            ttk.Label(frame, text="Current Address").grid(column=0, row=0, sticky=E)
            ttk.Label(frame, text=address).grid(column=1, row=0, sticky=E)

            ttk.Label(frame, text="New Address").grid(column=0, row=1, sticky=E)
            ttk.Entry(frame, width=7, textvariable=new_address).grid(column=1, row=1, sticky="W, E")
            ttk.Button(frame, text="Set", command=lambda: set_new_address(address, new_address.get())).\
                grid(column=4, row=1, sticky=W)

# insert board type selection


            # baud selection
            baud_dict = {1:19200, 2:57600, 3:115200}
            baud_setting = IntVar()
            baud_setting.set(value=self.read_parameter(address, 101))

            def update_baud():
                self.writeRegValue(101, baud_setting.get(), address)

            ttk.Label(frame, text="Baud Rate").grid(column=0, row=2, sticky=E)
            for key, value in baud_dict.items():
                ttk.Radiobutton(frame, variable=baud_setting, value=key, text=value, command=update_baud).grid(column=key, row=2, sticky=W)


            logging_enabled = IntVar()
            logging_enabled.set(value=self.read_parameter(address, 103))

            def update_logging():
                self.writeRegValue(103, logging_enabled.get(), address)

            ttk.Label(frame, text="Enable Logging").grid(column=0, row=4, sticky=E)
            ttk.Checkbutton(frame, variable=logging_enabled, command=update_logging).grid(column=1, row=4, sticky=W)

            ttk.Button(frame, text="Close", command=lambda: board_setup_window.destroy()).\
                grid(column=4, row=6, sticky=W)

            for child in frame.winfo_children():
                child.grid_configure(padx=5, pady=5)



            frame.pack()

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
        ttk.Button(setupframe, text="OK", command=buttonpress).grid(column=1, row=3, sticky=E)

        # baud selection
        baud_dict = {1: 19200, 2: 57600, 3: 115200}
        baud_setting = IntVar()
        baud_setting.set([key for key, value in baud_dict.items() if value == baud][0])

        def update_baud():
            global baud
            baud = baud_dict[baud_setting.get()]

        ttk.Label(setupframe, text="Baud Rate").grid(column=0, row=2, sticky=E)
        for key, value in baud_dict.items():
            ttk.Radiobutton(setupframe, variable=baud_setting, value=key, text=value, command=update_baud).grid(column=key,
                                                                                                           row=2,
                                                                                                           sticky=W)
        for child in setupframe.winfo_children():
            child.grid_configure(padx=5, pady=5)

        setupframe.pack()



def main():
    root = Tk()
    mainwin = ttk.Frame(root)
    creatediags(mainwin, 1)
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
