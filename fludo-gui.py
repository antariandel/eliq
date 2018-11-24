#!/usr/bin/env python

import sys
import random

import tkinter as tk
from tkinter import ttk

# TODO: Remove this as fludo becomes a package
sys.path.append('..')

import fludo


def _float_or_zero(value):
        try:
            return float(value)
        except ValueError:
            return 0


class MixerIngredient:
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

        self.ml_entry = ttk.Entry(self.mixer.frame, width=7, textvariable=self.ml)
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
        self.fill_button = ttk.Button(self.mixer.frame, text='⚪', width=3, command=lambda:
            self.mixer.toggle_fill(self))
        
        # --- Destroy Button ---
        self.destroy_button = ttk.Button(self.mixer.frame, text='⛝', width=3, command=lambda:
            self.mixer.destroy_row(self))

        # --- Widget Placements ---
        row_idx = self.mixer.get_last_row_idx() + 1 # Row number within Mixer table
        self.name_label.grid(
            row=row_idx, column=0, padx=10, sticky=tk.E)
        self.ml_scale.grid(
            row=row_idx, column=1)
        self.ml_remain_label.grid(
            row=row_idx, column=2, padx=17)
        self.fill_button.grid(
            row=row_idx, column=3, padx=1)
        self.ml_entry.grid(
            row=row_idx, column=4, padx=5)
        self.destroy_button.grid(
            row=row_idx, column=5, padx=14)
        
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
        self.fill_button.configure(text='⚪')
        self.fill_set = False

    def _set_fill(self):
        self.ml_scale.grid_forget()
        self.fill_label.grid(row=self.mixer.get_row_idx(self), column=1)
        self.ml_entry.configure(state='readonly')
        self._fill_traceid = self.ml_remain.trace('w', lambda var, idx, op:
            self.ml.set(
                int( (self.mixer.liquid_limit - sum([_float_or_zero(row.ml.get()) \
                    for row in self.mixer.rows if row != self])) * 10 ) / 10
            ))
        self.mixer.update(self)
        self.fill_button.configure(text='⚫')
        self.fill_set = True
    
    def set_liquid(self, liquid):
        self.liquid = liquid


class NewIngredientToplevel:
    def __init__(self, root, ingredients_parent):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title('Fludo | New Ingredient')
        self.toplevel.resizable(False, False)
        self.toplevel.bind('<Return>', self.create_and_close)

        self.ingredients_parent = ingredients_parent

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(padx=10, pady=10)

        self.name = tk.StringVar()
        self.name.set('Unnamed Ingredient')
        self.pg = tk.StringVar()
        self.pg.set('0')
        self.vg = tk.StringVar()
        self.vg.set('0')
        self.nic = tk.StringVar()
        self.nic.set('0')

        self.entry_validator = self.frame.register(self._validate_entry)

        self.name_label = ttk.Label(self.frame, text='Ingredient Name:')
        self.name_entry = ttk.Entry(self.frame, name='name_entry_%s' % id(self), width=30,
            textvariable=self.name,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.pg_label = ttk.Label(self.frame, text='PG (% vol.):')
        self.pg_entry = ttk.Entry(self.frame, name='pg_entry_%s' % id(self), width=30,
            textvariable=self.pg,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.vg_label = ttk.Label(self.frame, text='VG (% vol.):')
        self.vg_entry = ttk.Entry(self.frame, name='vg_entry_%s' % id(self), width=30,
            textvariable=self.vg,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.nic_label = ttk.Label(self.frame, text='Nicotine (mg/ml):')
        self.nic_entry = ttk.Entry(self.frame, name='nic_entry_%s' % id(self), width=30,
            textvariable=self.nic,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))

        self.lb_hint = ttk.Label(self.frame,
            text='''Give your ingredient a name, PG, VG and Nicotine
concentration. If PG and VG don't add up to 100%,
the rest is considered water. Use 0PG/0VG to add
pure water. Use 0 nic. mg/ml for nic-free bases
and aromas. You can turn this hint off in the
settings.\n''')
        # TODO: Make setting to turn this off

        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=5, column=0, columnspan=2)
        self.btn_create = ttk.Button(button_frame, text='Add Ingredient', width=20,
            command=self.create_and_close)
        self.btn_close = ttk.Button(button_frame, text='Cancel', width=20,
            command=self.close)

        self.name_label.grid(
            row=0, column=0, sticky=tk.E, padx=5, pady=5)
        self.pg_label.grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=5)
        self.vg_label.grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=5)
        self.nic_label.grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=5)
        
        self.name_entry.grid(
            row=0, column=1, sticky=tk.E)
        self.pg_entry.grid(
            row=1, column=1, sticky=tk.E)
        self.vg_entry.grid(
            row=2, column=1, sticky=tk.E)
        self.nic_entry.grid(
            row=3, column=1, sticky=tk.E)
        
        self.lb_hint.grid(row=4, column=0, columnspan=2, sticky=tk.N, pady=10)

        self.btn_create.grid(row=5, column=0, padx=16, sticky=tk.W+tk.E)
        self.btn_close.grid(row=5, column=1, padx=16, sticky=tk.W+tk.E)
    
    def _validate_entry(self, action, value, widget_name):
        if 'name_entry' in widget_name:
            if action == '-1': # focus change
                if not value:
                    self.name.set('Unnamed Ingredient')
                elif self.name.get() == 'Unnamed Ingredient':
                    self.name.set('')
            if len(value) < 240:
                return True
            else:
                return False
        
        if 'pg_entry' in widget_name:
            if (_float_or_zero(value) + _float_or_zero(self.vg.get())) > 100 or \
               _float_or_zero(value) < 0:
                return False
            
            if action == '-1': #focus change
                if not value:
                    self.pg.set(0)
        
        if 'vg_entry' in widget_name:
            if (_float_or_zero(value) + _float_or_zero(self.pg.get())) > 100 or \
               _float_or_zero(value) < 0:
                return False
            
            if action == '-1': #focus change
                if not value:
                    self.vg.set(0)

        if 'pg_entry' in widget_name or 'vg_entry' in widget_name:
            if value:
                try:
                    float(value)
                    return True
                except (TypeError, ValueError):
                    return False
            else:
                return True # allow empty string
        
        if 'nic_entry' in widget_name:
            if action == '-1': #focus change
                if not value:
                    self.nic.set(0)
            
            if value:
                try:
                    float(value)
                    if float(value) < 0:
                        return False
                    else:
                        return True
                except (TypeError, ValueError):
                    return False
            else:
                return True # allow empty string
    
    def create_and_close(self, event=None):
        self.ingredients_parent.add_ingredient(fludo.Liquid(
            name=self.name.get(),
            pg=_float_or_zero(self.pg.get()),
            vg=_float_or_zero(self.vg.get()),
            nic=_float_or_zero(self.nic.get())
        ))

        self.toplevel.withdraw()
    
    def close(self):
        self.toplevel.withdraw()


class MixerToplevel:
    def __init__(self, root):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title('Fludo | Liquid Mixer')
        self.toplevel.resizable(False, False)

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        self.frame.grid_rowconfigure(0, minsize=32)
        self.frame.grid_columnconfigure(0, minsize=250)
        self.frame.grid_columnconfigure(1, minsize=200)
        self.frame.grid_columnconfigure(2, minsize=60)

        self.labels_frame = ttk.Frame(self.frame)

        self.lb_max = ttk.Label(self.labels_frame, text='Max. (ml)')
        self.lb_max.grid(row=0, column=2, padx=5)

        self.lb_fill = ttk.Label(self.labels_frame, text='Fill')
        self.lb_fill.grid(row=0, column=3, padx=5)

        self.lb_ml = ttk.Label(self.labels_frame, text='Vol. (ml)')
        self.lb_ml.grid(row=0, column=4, padx=5)

        self.lb_destroy = ttk.Label(self.labels_frame, text='Remove')
        self.lb_destroy.grid(row=0, column=5, padx=5)

        self.status_bar = ttk.Frame(self.frame, borderwidth=1, relief=tk.GROOVE)
        self.frame.grid_rowconfigure(999, minsize=32)
        self.status_bar.grid(row=999, columnspan=6, sticky=tk.W+tk.E+tk.S)
        
        self.liquid_volume = tk.StringVar()
        self.lb_total = ttk.Label(self.status_bar, textvariable=self.liquid_volume)
        self.lb_total.grid(row=0, column=1, pady=2, sticky=tk.W)

        self.mixture_description = tk.StringVar()
        self.lb_mixture_description = ttk.Label(self.status_bar,
            textvariable=self.mixture_description)
        self.lb_mixture_description.grid(row=0, column=0, pady=2, sticky=tk.W)

        self.bt_add = ttk.Button(self.frame, text='Add Ingredient', width=20,
            command=self.add_ingredient_toplevel)
        self.bt_add.grid(row=998, column=0, columnspan=6)

        self.liquid_limit = 100 # Default to 100ml
        self.rows = []
        self.fill_set = False
        self.new_ingredient_toplevel = NewIngredientToplevel(self.toplevel, self)
        self.new_ingredient_toplevel.toplevel.withdraw()
        self.labels_shown = False
    
    def _initialize_new_row(self, calling_row):
        # Called by the row from its __init__
        self.rows.append(calling_row)
        self.frame.grid_rowconfigure(self.get_row_idx(calling_row), minsize=30)
        current_total_vol = sum([_float_or_zero(row.ml.get()) for row in self.rows])
        remaining_vol = self.liquid_limit - current_total_vol
        calling_row.ml_scale.configure(to=remaining_vol)
        calling_row.ml_remain.set(remaining_vol)
        self.update()

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
        current_total_vol = sum([_float_or_zero(row.ml.get()) \
            for row in self.rows if not row.fill_set])
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
            self.liquid_volume.set('Volume: %(limit).1f ml / %(limit).1f ml.' % {
                'limit': self.liquid_limit})
        else:
            self.liquid_volume.set('Volume: %(vol).1f ml / %(limit).1f ml.' % {
                'vol': sum([_float_or_zero(row.ml.get()) for row in self.rows]),
                'limit': self.liquid_limit })
        
        mixture = self.get_mixture()
        self.mixture_description.set('Mixture: %dPG / %dVG, nic. %.1f mg/ml.' % (
            mixture.pg, mixture.vg, mixture.nic))
    
    def add_ingredient_toplevel(self):
        self.new_ingredient_toplevel.toplevel.deiconify()
    
    def add_ingredient(self, liquid):
        if not self.labels_shown:
            self.labels_frame.grid(row=0, column=0, columnspan=6, sticky=tk.E)
        MixerIngredient(self, liquid)
    
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
        self.update()

        if self.get_last_row_idx() == 1:
            self.labels_frame.grid_forget()
            self.labels_shown = False

        # TODO: Grid row recycle, so we don't count up
    
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

# TODO: Create main window with recipe list

mixer = MixerToplevel(tk_root)

mixer.set_liquid_limit(30)
mixer.update()

tk_root.mainloop()
