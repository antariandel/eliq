#!/usr/bin/env python

import sys
import re
import random
import math
import tkinter as tk
from tkinter import ttk

sys.path.append('..') # TODO: Remove this as fludo becomes a package
import fludo


def _float_or_zero(value):
        try:
            return float(value)
        except ValueError:
            return 0


class Component:
    def __init__(self, mixer, liquid):
        self.mixer = mixer
        self.liquid = liquid

        # --- Volume (ml) Variable ---
        self.ml = tk.StringVar()
        self.ml.set(0.0)
        self.ml.trace('w', lambda var, idx, op:
            self.mixer.update(self))
        self.ml_remain = tk.StringVar()

        # --- Component Name Label ---
        self.name = tk.StringVar()
        self.name.set(self.liquid.name)
        self.name_label = ttk.Label(self.mixer.frame, textvariable=self.name)

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

        self.fill_label = ttk.Label(self.mixer.frame, text='Will fill remaining.')

        # --- Fill Select Button ---
        self.fill_button = ttk.Button(self.mixer.frame, text='', width=3, command=lambda:
            self.mixer.toggle_fill(self))
        
        # --- Destroy Button ---
        self.destroy_button = ttk.Button(self.mixer.frame, text='-', width=3, command=lambda:
            self.mixer.destroy_row(self))

        # --- Widget Placements ---
        row_idx = self.mixer.get_last_row_idx() + 1 # Row number within Mixer table
        self.name_label.grid(
            row=row_idx, column=0, padx=10, sticky=tk.E)
        self.ml_scale.grid(
            row=row_idx, column=1)
        self.ml_remain_label.grid(
            row=row_idx, column=2, padx=5)
        self.fill_button.grid(
            row=row_idx, column=3, padx=5)
        self.ml_entry.grid(
            row=row_idx, column=4, padx=5)
        self.destroy_button.grid(
            row=row_idx, column=5, padx=5)
        
        self.fill_set = False
        self.mixer._initialize_new_row(self)
    
    def _update_var_from_scale(self, scale, variable, digits=1):
        value = int(float(scale.get()) * pow(10, digits)) / pow(10, digits)
        variable.set(value)

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
        self.fill_label.grid_forget()
        self.ml_scale.grid(row=self.mixer.get_row_idx(self), column=1)
        self.ml_entry.configure(state='normal')
        try:
            self.ml_remain.trace_vdelete('w', self._fill_traceid)
            del(self._fill_traceid)
        except (AttributeError, tk._tkinter.TclError):
            # not set
            pass
        self.mixer.update(self)
        self.fill_button.configure(text='')
        self.fill_set = False

    def _set_fill(self):
        self.ml_scale.grid_forget()
        self.fill_label.grid(row=self.mixer.get_row_idx(self), column=1)
        self.ml_entry.configure(state='readonly')
        self._fill_traceid = self.ml_remain.trace('w', lambda var, idx, op:
            self.ml.set(
                int( (mixer.liquid_limit - sum([_float_or_zero(row.ml.get()) for row in mixer.rows if row != self])) * 10 ) / 10
            ))
        self.mixer.update(self)
        self.fill_button.configure(text='Fill')
        self.fill_set = True
    
    def set_liquid(self, liquid):
        self.liquid = liquid


class MixerToplevel:
    def __init__(self, root):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title('Fludo | Liquid Mixer')

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid_columnconfigure(1, minsize=200)
        self.frame.grid_columnconfigure(0, minsize=250)

        self.lb_max = ttk.Label(self.frame, text='Max. (ml)')
        self.lb_max.grid(row=0, column=2, padx=5)

        self.lb_fill = ttk.Label(self.frame, text='Fill')
        self.lb_fill.grid(row=0, column=3, padx=5)

        self.lb_ml = ttk.Label(self.frame, text='Vol. (ml)')
        self.lb_ml.grid(row=0, column=4, padx=5)

        self.status_bar = ttk.Frame(self.frame)
        self.status_bar.grid(row=999, columnspan=5)
        
        self.liquid_volume = tk.StringVar()
        self.liquid_volume.set('Total: 0.0 ml')
        self.lb_total = ttk.Label(self.frame, textvariable=self.liquid_volume)
        self.lb_total.grid(row=999, column=2, columnspan=3, padx=5, sticky=tk.E)

        self.mixture_description = tk.StringVar()
        self.lb_mixture_description = ttk.Label(self.frame, textvariable=self.mixture_description)
        self.lb_mixture_description.grid(row=999, column=0, sticky=tk.W)

        self.bt_add = ttk.Button(self.frame, width=3, text='+', command=self.add_row)
        self.bt_add.grid(row=0, column=5)

        self.liquid_limit = 100 # Default to 100ml
        self.rows = []
        self.fill_set = False
    
    def _initialize_new_row(self, calling_row):
        # Called by the row from its __init__ so that a new row can be added both
        # by Mixer.add_row(...) or just Component(mixer_instance, ...)
        self.rows.append(calling_row)
        self.frame.grid_rowconfigure(self.get_row_idx(calling_row), minsize=30)
        current_total_vol = sum([_float_or_zero(row.ml.get()) for row in self.rows])
        remaining_vol = self.liquid_limit - current_total_vol
        calling_row.ml_scale.configure(to=remaining_vol)
        calling_row.ml_remain.set(remaining_vol)

    def set_liquid_limit(self, ml):
        '''Updates the container size.'''
        # Preserves current mixture ratio

        ratio = ml / self.liquid_limit
        self.liquid_limit = ml

        for row in self.rows:
            new_value = _float_or_zero(row.ml.get()) * ratio
            row.ml_scale.configure(to=new_value+1) # dummy scale limit change
            row.ml_scale.set(new_value) # so that we can update it
        
        self.update()
    
    def get_mixture(self):
        return fludo.Mixture(*[row.liquid for row in self.rows])

    def update(self, skip_limiting_row=None):
        current_total_vol = sum([_float_or_zero(row.ml.get()) for row in self.rows if not row.fill_set])
        remaining_vol = self.liquid_limit - current_total_vol

        for row in self.rows:
            row_max = int((_float_or_zero(row.ml.get())+remaining_vol) * 10) / 10
            if row != skip_limiting_row:
                row.ml_scale.configure(to=row_max)
                row.ml_remain.set(row_max)
            if remaining_vol < 0.1:
                row.ml_remain.set('Full')
            else:
                row.ml_remain.set(row.ml_scale['to'])
            if row.fill_set:
                row.ml_remain.set('')
            row.ml_limit = row_max
            row.liquid.update_ml(_float_or_zero(row.ml.get()))
        
        if self.fill_set:
            self.liquid_volume.set('Volume: %(limit).1f ml / %(limit).1f ml' % {'limit': self.liquid_limit})
        else:
            self.liquid_volume.set('Volume: %(vol).1f ml / %(limit).1f ml' % {
                'vol': sum([_float_or_zero(row.ml.get()) for row in self.rows]),
                'limit': self.liquid_limit })
        
        mixture = self.get_mixture()
        self.mixture_description.set('Mixture: %dPG / %dVG, nic. %.1f mg/ml' % (
            mixture.pg, mixture.vg, mixture.nic))
    
    def add_row(self):
        # TODO: Create add window
        liquid = fludo.Liquid(name='Liquid %s' % random.randint(100, 999))
        Component(self, liquid)
        self.update()
    
    def destroy_row(self, row_instance):
        row_idx = self.get_row_idx(row_instance)

        if row_instance.fill_set:
            self.toggle_fill(row_instance)
        
        for widget in self.frame.grid_slaves():
            try:
                if widget.grid_info()['row'] == row_idx:
                    widget.grid_forget()
                    widget.destroy()
            except KeyError:
                # already deleted
                pass
        self.rows.remove(row_instance)
        self.frame.grid_rowconfigure(row_idx, minsize=0)
        del(row_instance)
        self.update()

        #TODO: Create grid row recycle
    
    def get_last_row_idx(self):
        last_row = 1
        for row in self.rows:
            row_idx = row.name_label.grid_info()['row']
            if row_idx > last_row:
                last_row = row_idx
        return last_row
    
    def get_row_idx(self, row_instance):
        return row_instance.name_label.grid_info()['row']
    
    def toggle_fill(self, row_instance):
        for row in self.rows:
            if row == row_instance:
                if row_instance.fill_set:
                    row._unset_fill()
                    self.fill_set = False
                    continue
                row._set_fill()
                self.fill_set = True
            else:
                row._unset_fill()
            
        self.update(skip_limiting_row=row_instance)


tk_root = tk.Tk()
tk_root.title('Fludo')

mixer = MixerToplevel(tk_root)

Component(mixer, fludo.Liquid(name='Base', pg=50))
Component(mixer, fludo.Liquid(name='NicBase', pg=50, nic=20))
Component(mixer, fludo.Liquid(name='Aroma: AG Grapes', pg=50))

mixer.frame.grid(padx=10, pady=10)

tk_root.mainloop()
