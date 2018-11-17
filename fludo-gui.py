#!/usr/bin/env python

import sys
import tkinter as tk
from tkinter import ttk

sys.path.append('..')
import fludo

root = tk.Tk()

class Component:
    def __init__(self, nic=0, pg=50, aroma=None):
        self.update(nic, pg, aroma)
    
    def update(self, nic=0, pg=50, aroma=None):
        if not aroma:
            self.nic = nic
            self.aroma = None
        else:
            self.nic = None
            self.aroma = aroma
        self.pg = pg
        self.vg = 100 - pg
    
    def pour(self, ml):
        pass


class Components:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.grid_columnconfigure(1, minsize=150)

        self.lb_fill = ttk.Label(self.frame, text='Fill')
        self.lb_fill.grid(row=0, column=2, padx=5, sticky=tk.E)

        self.lb_ml = ttk.Label(self.frame, text='Vol')
        self.lb_ml.grid(row=0, column=3, padx=5, sticky=tk.E)

class ComponentRow:
    def __init__(self, parent, type_name):
        self.parent = parent
        self.row = self.parent.grid_size()[1]

        self.type = ttk.Label(self.parent, text=type_name)
        self.type.grid(row=self.row, column=0, padx=10, sticky=tk.E)

        self.ml_scale = ttk.Scale(self.parent, orient=tk.HORIZONTAL, length=150)
        self.ml_fill = ttk.Label(self.parent, text='(Top Up)')
        self.ml_scale.grid(row=self.row, column=1, sticky=tk.E)

        self.fill = ttk.Button(self.parent, text='', width=2)
        self.fill.grid(row=self.row, column=2, padx=5, sticky=tk.E)

        self.ml = ttk.Entry(self.parent, width=3)
        self.ml.grid(row=self.row, column=3, padx=5, sticky=tk.E)

        self.pg = ttk.Entry(self.parent, width=2)
        self.pg.grid(row=self.row, column=4, padx=5, sticky=tk.E)

        self.vg = ttk.Entry(self.parent, width=2)
        self.vg.grid(row=self.row, column=5, padx=5, sticky=tk.E)
    
    def unset_fill(self):
        self.ml_fill.grid_forget()
        self.ml_scale.grid(row=self.row, column=1)
        self.ml.configure(state='normal')

    def set_fill(self):
        self.ml_scale.grid_forget()
        self.ml_fill.grid(row=self.row, column=1)
        self.ml.configure(state='readonly')

components = Components(root)


a = ComponentRow(components.frame, 'Base')
a.set_fill()
b = ComponentRow(components.frame, 'NicBase')
c = ComponentRow(components.frame, 'Aroma: AG Banana')

components.frame.grid(padx=10, pady=10)
root.mainloop()