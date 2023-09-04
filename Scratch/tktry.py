from tkinter import *
class Demo:
   def __init__(self, top):
      self.name=""
      frame_e = Frame(top)
      frame_e.pack()
      self.t_name = StringVar()
      text = Entry(frame_e, textvariable=self.t_name, bg="white")
      text.pack()
      text.focus_force()
      nameButton = Button(frame_e, text="Accept", command=self.Naming)
      nameButton.pack(side=BOTTOM, anchor=S)
   def Naming(self):
      self.name = self.t_name.get()
      print(self.name)
      root.destroy()
root = Tk()
root.geometry=("100x100+100+50")
D=Demo(root)
root.mainloop()
print("name retrieved was", D.name)
