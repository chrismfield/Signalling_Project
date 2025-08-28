from tkinter import *
import serial.tools.list_ports

def comm_selector(master):
        mycomlist = ([comport.device for comport in serial.tools.list_ports.comports()])

        commwindow = Toplevel(master,takefocus=True)
        listbox = Listbox(commwindow)
        listbox.pack()
        
        for item in mycomlist:
            listbox.insert(END, item)

        def callback():
            global ChosenPort
            ChosenPort = listbox.get(listbox.curselection())
            commwindow.destroy()
            return ChosenPort

        b = Button(commwindow, text="OK", command=callback)
        b.pack()


if __name__ == '__main__':

#    master = Tk()

    f = comm_selector(master)
    mainloop()
    print(f)

#print("I am here now")

