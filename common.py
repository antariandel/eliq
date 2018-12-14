#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk


def float_or_zero(value):
    try:
        return float(value)
    except ValueError:
        return float(0)


def center(toplevel):
    toplevel.nametowidget('.').eval('tk::PlaceWindow %s center' % toplevel.winfo_toplevel())


class CreateToolTip(object):
    # Source: https://stackoverflow.com/questions/3221956/how-do-i-display-tooltips-in-tkinter
    """
    create a tooltip for a given widget
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = y = 0
        x, y, cx, cy = self.widget.bbox("insert") # pylint: disable=W0612
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.hidetip() # added this as a comment suggested
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw= None
        if tw:
            tw.destroy()

class YesNoToplevel:
    # tkinter dialogs are ugly
    def __init__(self, root, callback, window_title, text, destroy_on_close=True):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title('Fludo | %s' % window_title)
        self.toplevel.resizable(False, False)
        self.toplevel.bind('<Return>', lambda event: self.close(True))
        self.toplevel.protocol("WM_DELETE_WINDOW", lambda: self.close(False))
        self.toplevel.focus()

        self.callback = callback

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(padx=20, pady=5)

        self.label = ttk.Label(self.frame, text=text)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        self.yes_button = ttk.Button(self.frame, text='Yes', width=10,
            command=lambda: self.close(True))
        self.yes_button.grid(row=1, column=0, pady=10)
        
        self.no_button = ttk.Button(self.frame, text='No', width=10,
            command=lambda: self.close(False))
        self.no_button.grid(row=1, column=1, pady=10)

        self.destroy_on_close = destroy_on_close

        center(self.toplevel)
    
    def close(self, yes_clicked=False):
        self.callback(yes_clicked)

        if self.destroy_on_close:
            self.toplevel.destroy()
        else:
            self.toplevel.withdraw()


class FloatEntryToplevel:
    # tkinter dialogs are ugly
    def __init__(self, root, callback, window_title, text, default_value=0,
        min_value=0, max_value=100, destroy_on_close=True):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title('Fludo | %s' % window_title)
        self.toplevel.resizable(False, False)
        self.toplevel.bind('<Return>', lambda event: self.close(True))
        self.toplevel.protocol("WM_DELETE_WINDOW", lambda: self.close(False))

        self.callback = callback

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(padx=20, pady=5)

        self.label = ttk.Label(self.frame, text=text)
        self.label.grid(row=0, column=0, columnspan=2, pady=10)

        self.entry_value = tk.StringVar()
        self.entry_value.set(default_value)
        self.entry = ttk.Entry(self.frame, textvariable=self.entry_value)
        self.entry_validator = self.entry.register(self._validate_entry)
        self.entry.configure(
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        self.entry.grid(row=1, columnspan=2, pady=10)
        self.entry.focus()

        self.yes_button = ttk.Button(self.frame, text='OK', width=10,
            command=lambda: self.close(True))
        self.yes_button.grid(row=2, column=0, pady=10)
        
        self.no_button = ttk.Button(self.frame, text='Cancel', width=10,
            command=lambda: self.close(False))
        self.no_button.grid(row=2, column=1, pady=10)

        self.destroy_on_close = destroy_on_close
        self.min_value = min_value
        self.max_value = max_value

        center(self.toplevel)
    
    def _validate_entry(self, action, value, widget_name):
        if action == '-1': # focus change
            if not value or float_or_zero(value) < self.min_value:
                self.entry_value.set(self.min_value)
        
        if value:
            try:
                float(value)
                if float(value) > self.max_value:
                     return False
                else:
                    return True
                return True
            except (TypeError, ValueError):
                return False
        else:
            return True # allow empty string
    
    def close(self, ok_clicked=False):
        if ok_clicked:
            self.callback(float_or_zero(self.entry_value.get()))
        
        if self.destroy_on_close:
            self.toplevel.destroy()
        else:
            self.toplevel.withdraw()