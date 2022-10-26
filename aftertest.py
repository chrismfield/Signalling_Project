from tkinter import *

def myloop():
    print("hello")
    return

root = Tk()
root.after(1000, myloop)
root.mainloop()
