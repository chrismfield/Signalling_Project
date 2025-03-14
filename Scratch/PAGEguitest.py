#http://sebsauvage.net/python/gui/#loop

import tkinter

def vp_start_gui():
    '''Starting point when module is the main routine.'''
    global val, w, root
    root = tk()
    top = New_Toplevel (root)
    PAGEguitest_support.init(root, top)
    root.mainloop()

w = None
def create_New_Toplevel(root, *args, **kwargs):
    '''Starting point when module is imported by another program.'''
    global w, w_win, rt
    rt = root
    w = Toplevel (root)
    top = New_Toplevel (w)
    PAGEguitest_support.init(w, top, *args, **kwargs)
    return (w, top)

def destroy_New_Toplevel():
    global w
    w.destroy()
    w = None


class New_Toplevel:
    def __init__(self, top=None):
        '''This class configures and populates the toplevel window.
           top is the toplevel containing window.'''
        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85' 
        _ana2color = '#d9d9d9' # X11 color: 'gray85' 

        top.geometry("600x450+560+142")
        top.title("New Toplevel")
        top.configure(background="#d9d9d9")



        self.Scale1 = Scale(top)
        self.Scale1.place(relx=0.48, rely=0.24, relwidth=0.0, relheight=0.52
                , width=45)
        self.Scale1.configure(activebackground="#d9d9d9")
        self.Scale1.configure(background="#d9d9d9")
        self.Scale1.configure(font="TkTextFont")
        self.Scale1.configure(foreground="#000000")
        self.Scale1.configure(highlightbackground="#d9d9d9")
        self.Scale1.configure(highlightcolor="black")
        self.Scale1.configure(length="226")
        self.Scale1.configure(troughcolor="#d9d9d9")

        self.Label1 = Label(top)
        self.Label1.place(relx=0.18, rely=0.24, height=21, width=34)
        self.Label1.configure(background="#d9d9d9")
        self.Label1.configure(disabledforeground="#a3a3a3")
        self.Label1.configure(foreground="#000000")
        self.Label1.configure(text='''Label''')






if __name__ == '__main__':
    vp_start_gui()

