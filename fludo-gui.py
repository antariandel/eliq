#!/usr/bin/env python

import sys
import sqlite3
import re
import random
import tkinter as tk
from tkinter import ttk

sys.path.append('..')
import fludo

UPDATE = '-2'


root = tk.Tk()


class Mixer:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.grid_columnconfigure(1, minsize=150)

        self.lb_fill = ttk.Label(self.frame, text='Set Fill')
        self.lb_fill.grid(row=0, column=2, padx=5, sticky=tk.E)

        self.lb_ml = ttk.Label(self.frame, text='Vol')
        self.lb_ml.grid(row=0, column=3, padx=5, sticky=tk.E)

        self.liquid_amount = 30 # Default to 30ml
    
    def get_widget(self, widget_name):
        '''Gets one of mixer's child widgets of the given name.'''
        for widget in self.frame.winfo_children():
            if widget_name in str(widget):
                return widget

    def set_liquid_amount(self, ml):
        self.liquid_amount = ml

        for child_widget in self.frame.winfo_children():
            if type(child_widget) == ttk.Scale:
                if 'ml_scale' in str(child_widget):
                    child_widget.configure(to=self.liquid_amount)


class Component:
    def __init__(self, mixer, name):
        self.mixer = mixer
        self.row = self.mixer.frame.grid_size()[1] # Row number within Mixer table

        # --- Volume (ml) Variable ---
        self.ml = tk.DoubleVar()
        #self.ml.trace('w', lambda var, idx, op:
        #    )

        # --- Component Name Label ---
        self.name = ttk.Label(self.mixer.frame, text=name)

        # --- Volume (ml) Entry Field ---
        # Linked to self.ml and the volume validation method.
        # Validation: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/entry-validation.html
        # Numeric display precision is set within the entry's name.

        self.ml_entry = ttk.Entry(self.mixer.frame, width=6,
            textvariable=self.ml,
            name='ml_entry_1prec_%s' % id(self))
        ml_entry_validator = self.ml_entry.register(self._validate_numeric_entry)
        self.ml_entry.configure(validate='all', validatecommand=(ml_entry_validator, '%d','%P', '%W', 0, mixer.liquid_amount))
        self._validate_numeric_entry(UPDATE, '', self.ml_entry._name, 0, mixer.liquid_amount) # display 0 or 0.0 at start

        # --- Volume (ml) Scale ---
        # The scale updates the entry through the same validation method with action set to UPDATE
        # This is so that the number of digits of precision is respected for the entry field
        # when updated through the scale.

        self.ml_scale = ttk.Scale(self.mixer.frame, orient=tk.HORIZONTAL, length=150,
            to=mixer.liquid_amount,
            variable=self.ml,
            command=lambda value: self._validate_numeric_entry(UPDATE, value, self.ml_entry._name, 0, mixer.liquid_amount),
            name='ml_scale_%s' % id(self))
        
        # --- (Top Up) Label ---
        # Shown instead of the scale if fill is selected for the component

        self.ml_fill = ttk.Label(self.mixer.frame, text='(Top Up)')

        # --- Fill Select Button ---
        self.fill = ttk.Button(self.mixer.frame, text='', width=3)

        # --- Widget Placements ---
        self.name.grid(
            row=self.row, column=0, padx=10, sticky=tk.E)
        self.ml_scale.grid(
            row=self.row, column=1, sticky=tk.E)
        self.fill.grid(
            row=self.row, column=2, padx=5)
        self.ml_entry.grid(
            row=self.row, column=3, padx=5, sticky=tk.E)

    def _validate_numeric_entry(self, action, value, widget_name, min_value, max_value):
        # Validation: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/entry-validation.html
        # Example for entry field configuration:
        #   field = Entry(name='my_field_2prec') #<-- display 2 digits of precision
        #   validator = field.register(validate_numeric_entry)
        #   field.configure(validate='all', validatecommand=(validator, '%d','%P', '%W', 0, 100))
        # Based on linked documentation this method should be called also when the textvariable
        # changes, but it isn't. To solve this, we have to call this validation method with action
        # set to update whenever the textvariable changes.

        # Update field display
        if int(action) < 0: # External Update to Field
            widget = self.mixer.get_widget(widget_name)
            format_pattern = re.compile(r'([0-9]+)prec')

            if action == UPDATE:
                # Set variable if action is UPDATE
                widget.setvar(value)
            
            if value == '':
                # Set to 0 if left blank when unfocused
                widget.delete(0, tk.END)
                try:
                    digits = int(format_pattern.search(widget_name).group(1))
                    if digits > 0:
                        widget.insert(0, '0.0')
                    else:
                        widget.insert(0, '0')
                except (TypeError, ValueError, AttributeError):
                    widget.insert(0, '0')

            else:
                # If not blank, format to number of precision digits indicated in
                # the entry name
                try:
                    digits = int(format_pattern.search(widget_name).group(1))
                    if digits > 0:
                        widget.delete(0, tk.END)
                        widget.insert(0, int(float(value) * pow(10, digits)) / pow(10, digits))
                    else:
                        widget.delete(0, tk.END)
                        widget.insert(0, int(float(value)))
                except (TypeError, ValueError, AttributeError):
                    # no need to round or textvariable not formatted correctly
                    pass

        # Return validation result
        if value:
            try:
                float(value)
                if (float(value) > float(max_value)) or (float(value) < float(min_value)):
                    return False
                else:
                    return True
            except (TypeError, ValueError):
                return False
        else:
            return True
    
    def unset_fill(self):
        self.ml_fill.grid_forget()
        self.ml_scale.grid(row=self.row, column=1)
        self.ml_entry.configure(state='normal')

    def set_fill(self):
        self.ml_scale.grid_forget()
        self.ml_fill.grid(row=self.row, column=1)
        self.ml_entry.configure(state='readonly')

mixer = Mixer(root)

a = Component(mixer, 'Base')
a.set_fill()
b = Component(mixer, 'NicBase')
c = Component(mixer, 'Aroma: AG Banana')
mixer.set_liquid_amount(30)

mixer.frame.grid(padx=10, pady=10)
root.mainloop()