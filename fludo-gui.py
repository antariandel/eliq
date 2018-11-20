#!/usr/bin/env python

import sys
import re
import random
import math
import tkinter as tk
from tkinter import ttk

sys.path.append('..') # TODO: Remove this as fludo becomes a package
import fludo


_tk_root = tk.Tk()

_tk_root.title('Fludo | Liquid Mixer')


def _float_or_zero(value):
        try:
            return float(value)
        except ValueError:
            return 0


class Component:
    def __init__(self, mixer, name):
        self.mixer = mixer
        self.row = len(mixer.rows)+1 # Row number within Mixer table

        # --- Volume (ml) Variable ---
        self.ml = tk.StringVar()
        self.ml.set(0.0)
        self.ml.trace('w', lambda var, idx, op:
            self.mixer.update(self))
        self.ml_remain = tk.StringVar()

        # --- Component Name Label ---
        self.name = ttk.Label(self.mixer.frame, text=name)

        # --- Volume (ml) Entry Field ---
        # Linked to self.ml and the volume validation method.
        # Validation: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/entry-validation.html

        self.ml_entry = ttk.Entry(self.mixer.frame, width=6, textvariable=self.ml)
        self.ml_entry_validator = self.ml_entry.register(self._validate_ml_entry)

        # --- Volume (ml) Scale ---
        # ttk.Scale has no resolution, so we have to update through a command
        # to round to a lower precision floating point.

        self.ml_scale = ttk.Scale(self.mixer.frame, orient=tk.HORIZONTAL, length=200,
            to=mixer.liquid_limit,
            variable=self.ml,
            command=lambda value:
                 self._update_var_from_scale(self.ml_scale, self.ml, digits=1))
        self.ml_entry.configure(validate='all',
            validatecommand=(self.ml_entry_validator, '%d','%P'))
        self.ml_remain_label = ttk.Label(self.mixer.frame, textvariable=self.ml_remain)
        
        # --- Fill Label ---
        # Shown instead of the scale if fill is selected for the component

        self.ml_fill = ttk.Label(self.mixer.frame, text='')

        # --- Fill Select Button ---
        self.fill = ttk.Button(self.mixer.frame, text='', width=3, command=lambda:
            self.mixer.set_fill(self))
        
        # --- Destroy Button ---
        self.destroy = ttk.Button(self.mixer.frame, text='', width=3, command=lambda:
            self.mixer.destroy_row(self))

        # --- Widget Placements ---
        self.name.grid(
            row=self.row, column=0, padx=10, sticky=tk.E)
        self.ml_scale.grid(
            row=self.row, column=1)
        self.ml_remain_label.grid(
            row=self.row, column=2, padx=5)
        self.fill.grid(
            row=self.row, column=3, padx=5)
        self.ml_entry.grid(
            row=self.row, column=4, padx=5)
        self.destroy.grid(
            row=self.row, column=5, padx=5)
        
        self.fill_set = False
        self.mixer._create_row(self)
    
    def _update_var_from_scale(self, scale, variable, digits=1):
        value = int(float(scale.get()) * pow(10, digits)) / pow(10, digits)
        self.ml.set(value)

    def _validate_ml_entry(self, action, value):
        # Validation: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/entry-validation.html
        # Example for entry field configuration:
        #   field = Entry()
        #   validator = field.register(_validate_ml_entry)
        #   field.configure(validate='all', validatecommand=(validator, '%d','%P'))

        min_value = 0
        max_value = self.ml_scale['to']

        # Update field to 0 if unfocused while left blank
        if action == '-1': # focus in/out action
            if not value:
                self.ml_entry.delete(0, tk.END)
                self.ml_entry.insert(0, '0.0')

        # Return validation result
        # Will only let changes to the entry field that still result in a float.
        # Furthermore, the number has to be within min/max bounds.
        if value:
            try:
                float(value)
                if ((float(value) > float(max_value)) or
                    (float(value) < float(min_value))):
                    return False
                else:
                    return True
            except (TypeError, ValueError):
                return False
        else:
            return True # allow empty string
    
    def _unset_fill(self):
        self.ml_fill.grid_forget()
        self.ml_scale.grid(row=self.row, column=1)
        self.ml_entry.configure(state='normal')
        try:
            self.ml_remain.trace_vdelete('w', self._fill_traceid)
            del(self._fill_traceid)
        except (AttributeError, tk._tkinter.TclError):
            # not set
            pass
        self.mixer.update(self)
        self.fill.configure(text='')
        self.fill_set = False

    def _set_fill(self):
        self.ml_scale.grid_forget()
        self.ml_fill.grid(row=self.row, column=1)
        self.ml_entry.configure(state='readonly')
        self._fill_traceid = self.ml_remain.trace('w', lambda var, idx, op:
            self.ml.set(
                int( (mixer.liquid_limit - sum([_float_or_zero(row.ml.get()) for row in mixer.rows if row != self])) * 10 ) / 10
            ))
        self.mixer.update(self)
        self.fill.configure(text='Fill')
        self.fill_set = True


class Mixer:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.grid_columnconfigure(1, minsize=200)
        self.frame.grid_columnconfigure(0, minsize=250)

        self.lb_max = ttk.Label(self.frame, text='Max. (ml)')
        self.lb_max.grid(row=0, column=2, padx=5)

        self.lb_fill = ttk.Label(self.frame, text='Fill')
        self.lb_fill.grid(row=0, column=3, padx=5)

        self.lb_ml = ttk.Label(self.frame, text='Vol. (ml)')
        self.lb_ml.grid(row=0, column=4, padx=5)


        self.liquid_limit = 30 # Default to 30ml
        
        self.liquid_volume = tk.StringVar()
        self.liquid_volume.set('Total: 0.0 ml')

        self.lb_total = ttk.Label(self.frame, textvariable=self.liquid_volume)
        self.lb_total.grid(row=999, column=2, columnspan=3, padx=5, sticky=tk.E)

        self.bt_add = ttk.Button(self.frame, width=3, text='+', command=self.add_row)
        self.bt_add.grid(row=0, column=5)

        self.rows = []
        self.fill_set = False
    
    def _create_row(self, controlling_row):
        self.rows.append(controlling_row)
        self.frame.grid_rowconfigure(controlling_row.row, minsize=30)
        current_total_vol = sum([_float_or_zero(row.ml.get()) for row in self.rows])
        remaining_vol = self.liquid_limit - current_total_vol
        controlling_row.ml_scale.configure(to=remaining_vol)
        controlling_row.ml_remain.set(remaining_vol)

    def set_liquid_limit(self, ml):
        '''Updates the container size the current mixture will fill.'''
        # Preserves current mixture ratio

        ratio = ml / self.liquid_limit
        self.liquid_limit = ml

        for row in self.rows:
            new_value = _float_or_zero(row.ml.get()) * ratio
            row.ml_scale.configure(to=new_value+1) # dummy scale limit change
            row.ml_scale.set(new_value) # so that we can update it
        
        self.update()

    def update(self, controlling_row=None):
        current_total_vol = sum([_float_or_zero(row.ml.get()) for row in self.rows if not row.fill_set])
        remaining_vol = self.liquid_limit - current_total_vol

        for row in self.rows:
            row_max = int((_float_or_zero(row.ml.get())+remaining_vol) * 10) / 10
            if row != controlling_row:
                row.ml_scale.configure(to=row_max)
                row.ml_remain.set(row_max)
            if remaining_vol < 0.1:
                row.ml_remain.set('Full')
            else:
                row.ml_remain.set(row.ml_scale['to'])
            if row.fill_set:
                row.ml_remain.set('')
            row.ml_limit = row_max
        
        if self.fill_set:
            self.liquid_volume.set('Total: %.1f ml' % self.liquid_limit)
        else:
            self.liquid_volume.set('Total: %.1f ml' % sum([_float_or_zero(row.ml.get()) for row in self.rows]))
    
    def add_row(self):
        # TODO: Select from a list of already created liquids
        name = 'Liquid %s' % random.randint(100, 999)
        Component(self, name)
        self.update()
    
    def destroy_row(self, controlling_row):
        for widget in self.frame.grid_slaves():
            try:
                if widget.grid_info()['row'] == controlling_row.row:
                    widget.grid_forget()
                    widget.destroy()
            except KeyError:
                # already deleted
                pass
        self.rows.remove(controlling_row)
        self.frame.grid_rowconfigure(controlling_row.row, minsize=0)
        del(controlling_row)
        self.update()
    
    def set_fill(self, controlling_row):
        for row in self.rows:
            if row == controlling_row:
                if controlling_row.fill_set:
                    row._unset_fill()
                    continue
                row._set_fill()
            else:
                row._unset_fill()
        if [row for row in self.rows if row.fill_set]:
            self.fill_set = True
        else:
            self.fill_set = False
        self.update(controlling_row)


mixer = Mixer(_tk_root)

a = Component(mixer, 'Base')
b = Component(mixer, 'NicBase')
c = Component(mixer, 'Aroma: AG Grapes')
mixer.set_liquid_limit(50)

mixer.frame.grid(padx=10, pady=10)

_tk_root.mainloop()
