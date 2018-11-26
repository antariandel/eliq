#!/usr/bin/env python

import sys

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox, simpledialog

# TODO: Remove this as fludo becomes a package
sys.path.append('../fludo')

import fludo


def float_or_zero(value):
        try:
            return float(value)
        except ValueError:
            return float(0)


def center(toplevel):
    # TODO: Make tk_root an attribute rather than reference to global
    tk_root.eval('tk::PlaceWindow %s center' % toplevel.winfo_toplevel())


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


class MixerIngredient:
    def __init__(self, mixer, liquid):
        self.mixer = mixer
        self.liquid = liquid

        # --- Volume (ml) Variable ---
        self.ml = tk.StringVar()
        self.ml.set(float(self.liquid.ml))
        self.ml.trace('w', lambda var, idx, op:
            self.mixer.update(self))
        self.ml_remain = tk.StringVar()

        # --- Component Name Label ---
        self.name = tk.StringVar()
        self.name.set(self.liquid.name)
        self.name_label = ttk.Label(self.mixer.frame, textvariable=self.name)
        self.name_label_ttip = CreateToolTip(self.name_label, '%(pg)dPG/%(vg)dVG, Nic. %(nic).1f' %{
            'pg': self.liquid.pg,
            'vg': self.liquid.vg,
            'nic': self.liquid.nic })

        # --- Volume (ml) Entry Field ---
        # Linked to self.ml and the volume validation method.
        # Validation: http://infohost.nmt.edu/tcc/help/pubs/tkinter/web/entry-validation.html

        self.ml_entry = ttk.Entry(self.mixer.frame, width=7, textvariable=self.ml)
        self.ml_entry_validator = self.ml_entry.register(self._validate_ml_entry)
        self.ml_entry.configure(validate='all',
            validatecommand=(self.ml_entry_validator, '%d','%P'))

        # --- Volume (ml) Scale ---
        # ttk.Scale has no resolution, so we have to update through a command
        # to round to a lower precision floating point.

        self.ml_scale = ttk.Scale(self.mixer.frame, orient=tk.HORIZONTAL, length=200,
            to=mixer.liquid_limit,
            variable=self.ml,
            command=lambda value:
                 self._update_var_from_scale(self.ml_scale, self.ml, digits=1))
        self.ml_scale_ttip = CreateToolTip(self.ml_scale, 'Adjust amount')

        self.ml_remain_label = ttk.Label(self.mixer.frame, textvariable=self.ml_remain)
        self.ml_remain_label_ttip = CreateToolTip(self.ml_remain_label,
            'Max possible amount\nfor the ingredient.')
        
        # --- Fill Label ---
        # Shown instead of the scale if fill is selected for the component

        self.fill_label = ttk.Label(self.mixer.frame, text='(will fill container)')

        # --- Fill Select Button ---
        self.fill_button = ttk.Button(self.mixer.frame, text='⚪', width=3, command=lambda:
            self.mixer.toggle_fill(self))
        self.fill_button_ttip = CreateToolTip(self.fill_button, 'Fill container')

        # --- Edit Button ---
        self.edit_button = ttk.Button(self.mixer.frame, text='✎', width=3, command=lambda:
            self.show_editor_toplevel())
        self.edit_button_ttip = CreateToolTip(self.edit_button, 'Edit ingredient')
        
        # --- Destroy Button ---
        self.destroy_button = ttk.Button(self.mixer.frame, text='❌', width=3, command=lambda:
            self.show_remove_dialog())
        self.destroy_button_ttip = CreateToolTip(self.destroy_button, 'Remove ingredient')

        # --- Widget Placements ---
        row_idx = self.mixer.get_last_row_idx() + 1 # Row number within Mixer table
        self.name_label.grid(
            row=row_idx, column=0, padx=10, sticky=tk.E)
        self.ml_scale.grid(
            row=row_idx, column=1)
        self.ml_remain_label.grid(
            row=row_idx, column=2, padx=17)
        self.fill_button.grid(
            row=row_idx, column=3, padx=5)
        self.ml_entry.grid(
            row=row_idx, column=4, padx=5)
        self.edit_button.grid(
            row=row_idx, column=5, padx=5)
        self.destroy_button.grid(
            row=row_idx, column=6, padx=14)
        
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
                int( (self.mixer.liquid_limit - sum([float_or_zero(row.ml.get()) \
                    for row in self.mixer.rows if row != self])) * 10 ) / 10
            ))
        self.mixer.update(self)
        self.fill_button.configure(text='⚫')
        self.fill_set = True

    def show_editor_toplevel(self):
        # FIXME: Create editor instance (like add ingredient instance for mixertoplevel)
        NewIngredientToplevel(self.mixer.toplevel, self.set_liquid,
            window_title='Edit Ingredient', button_text='OK', liquid=self.liquid)
    
    def show_remove_dialog(self):
         # FIXME: Create remover instance (like add ingredient instance for mixertoplevel)
        if self.mixer.ask_remove:
            YesNoToplevel(self.mixer.toplevel,
                callback=lambda yes_clicked: self.mixer.destroy_row(self if yes_clicked else None),
                window_title='Remove Ingredient',
                text='''Are you sure you wish to remove
%(name)s, %(pg)dPG/%(vg)dVG, nic. %(nic).1f mg/ml?''' % {
                    'name': self.liquid.name,
                    'pg': self.liquid.pg,
                    'vg': self.liquid.vg,
                    'nic': self.liquid.nic })

    def set_liquid(self, liquid):
        self.liquid = liquid
        self.name.set(self.liquid.name)
        self.name_label_ttip = CreateToolTip(self.name_label, '%(pg)dPG/%(vg)dVG, Nic. %(nic).1f' %{
            'pg': self.liquid.pg,
            'vg': self.liquid.vg,
            'nic': self.liquid.nic })
        self.mixer.update()


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


class NewIngredientToplevel:
    def __init__(self, root, callback, window_title='New Ingredient',
        button_text='Add Ingredient', liquid=None):
        self.toplevel = tk.Toplevel(root)
        self.toplevel.title('Fludo | %s' % window_title)
        self.toplevel.resizable(False, False)
        self.toplevel.bind('<Return>', lambda event: self.create_and_close())
        self.toplevel.protocol("WM_DELETE_WINDOW", self.close)

        self.callback = callback

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(padx=10, pady=10)

        self.name = tk.StringVar()
        self.name.set('Unnamed Ingredient' if not liquid else liquid.name)
        self.pg = tk.StringVar()
        self.pg.set('0' if not liquid else liquid.pg)
        self.vg = tk.StringVar()
        self.vg.set('0' if not liquid else liquid.vg)
        self.nic = tk.StringVar()
        self.nic.set('0' if not liquid else liquid.nic)

        self.entry_validator = self.frame.register(self._validate_entry)

        self.name_label = ttk.Label(self.frame, text='Ingredient Name:')
        self.name_entry = ttk.Entry(self.frame, name='name_entry_%s' % id(self), width=30,
            textvariable=self.name,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        self.name_entry.focus()
        
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
pure water. Use 0 nic. mg/ml for nic-free bases,
aromas and water. You can turn this hint off in
the settings.\n''')
        # TODO: Make setting to turn this off

        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=5, column=0, columnspan=2)
        self.btn_create = ttk.Button(button_frame, text=str(button_text), width=20,
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

        center(self.toplevel)
    
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
            if (float_or_zero(value) + float_or_zero(self.vg.get())) > 100 or \
               float_or_zero(value) < 0:
                return False
            
            if action == '-1': #focus change
                if not value:
                    self.pg.set(0)
        
        if 'vg_entry' in widget_name:
            if (float_or_zero(value) + float_or_zero(self.pg.get())) > 100 or \
               float_or_zero(value) < 0:
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
    
    def create_and_close(self):
        self.callback(fludo.Liquid(
            name='Unnamed Ingredient' if not self.name.get() else self.name.get(),
            pg=float_or_zero(self.pg.get()),
            vg=float_or_zero(self.vg.get()),
            nic=float_or_zero(self.nic.get())
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
        self.labels_frame.grid_columnconfigure(5, minsize=40)
        self.labels_frame.grid_columnconfigure(3, minsize=33)

        self.lb_max = ttk.Label(self.labels_frame, text='Max. (ml)')
        self.lb_max.grid(row=0, column=2, padx=5)

        self.lb_ml = ttk.Label(self.labels_frame, text='Vol. (ml)')
        self.lb_ml.grid(row=0, column=4, padx=5)

        self.status_bar = ttk.Frame(self.frame, borderwidth=1, relief=tk.GROOVE)
        self.frame.grid_rowconfigure(999, minsize=32)
        self.status_bar.grid(row=999, columnspan=7, sticky=tk.W+tk.E+tk.S)
        
        self.liquid_volume = tk.StringVar()
        self.lb_total = ttk.Label(self.status_bar, textvariable=self.liquid_volume)
        self.lb_total.grid(row=0, column=1, pady=2, sticky=tk.W)

        self.mixture_description = tk.StringVar()
        self.lb_mixture_description = ttk.Label(self.status_bar,
            textvariable=self.mixture_description)
        self.lb_mixture_description.grid(row=0, column=0, pady=3, padx=5, sticky=tk.W)

        self.lb_start = ttk.Label(self.frame, text='Start by adding an ingredient.')
        self.lb_start.grid(row=997, column=0, columnspan=6)

        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.grid(row=998, columnspan=6, pady=10)

        self.bt_add = ttk.Button(self.button_frame, text='Add Ingredient', width=20,
            command=self.show_add_ingredient_toplevel)
        self.bt_add.grid(row=998, column=0, padx=5)

        self.bt_change_container = ttk.Button(self.button_frame, text='Change Container Size', width=20,
            command=self.show_change_container_dialog)
        self.bt_change_container.grid(row=998, column=1, padx=5)

        self.liquid_limit = 100 # Default to 100ml
        self.rows = []
        self.new_ingredient_toplevel = NewIngredientToplevel(self.toplevel, self.add_ingredient,
            window_title='Add Ingredient')
        self.new_ingredient_toplevel.toplevel.withdraw()

        self.fill_set = False
        self.labels_shown = False
        self.ask_remove = True

        center(self.toplevel)
        self.toplevel.lift()
    
    def _initialize_new_row(self, calling_row):
        # Called by the row from its __init__
        self.rows.append(calling_row)
        self.frame.grid_rowconfigure(self.get_row_idx(calling_row), minsize=30)
        current_total_vol = sum([float_or_zero(row.ml.get()) for row in self.rows])
        remaining_vol = self.liquid_limit - current_total_vol
        calling_row.ml_scale.configure(to=remaining_vol)
        calling_row.ml_remain.set(remaining_vol)
        self.update()
    
    def show_change_container_dialog(self):
        FloatEntryToplevel(self.toplevel,
            window_title='Change Container Size',
            text='''Enter new size in milliliters below.
Minimum size is 10 ml, max. is 10,000 ml.''',
            min_value=10, max_value=10000,
            default_value=self.liquid_limit,
            callback=self.set_liquid_limit)

    def set_liquid_limit(self, ml):
        '''Updates the container size.'''
        # Preserves current mixture ratio

        ratio = ml / self.liquid_limit
        self.liquid_limit = ml

        for row in self.rows:
            new_value = float_or_zero(row.ml.get()) * ratio
            row.ml_scale.configure(to=new_value+1) # dummy scale limit change
            row.ml_scale.set(new_value) # so that we can update it
        
        self.update()
    
    def get_mixture(self):
        if len(self.rows) > 1:
            return fludo.Mixture(*[row.liquid for row in self.rows])
        elif len(self.rows) == 1:
            return self.rows[0].liquid
        else:
            return fludo.Liquid(ml=0, pg=0, vg=0, nic=0)

    def update(self, skip_limiting_row=None):
        current_total_vol = sum([float_or_zero(row.ml.get()) \
            for row in self.rows if not row.fill_set])
        remaining_vol = self.liquid_limit - current_total_vol

        for row in self.rows:
            row_max = int((float_or_zero(row.ml.get())+remaining_vol) * 10) / 10
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
            row.liquid.update_ml(float_or_zero(row.ml.get()))
        
        if self.fill_set:
            self.liquid_volume.set('Vol. %(limit).1f ml (in %(limit).1f ml. container)' % {
                'limit': self.liquid_limit})
        else:
            self.liquid_volume.set('Vol. %(vol).1f ml (in %(limit).1f ml. container)' % {
                'vol': sum([float_or_zero(row.ml.get()) for row in self.rows]),
                'limit': self.liquid_limit })
        
        mixture = self.get_mixture()
        self.mixture_description.set('%dPG / %dVG, nic. %.1f mg/ml.   |' % (
            mixture.pg, mixture.vg, mixture.nic))
    
    def show_add_ingredient_toplevel(self):
        self.new_ingredient_toplevel.toplevel.deiconify()
        self.new_ingredient_toplevel.name_entry.focus()
    
    def add_ingredient(self, liquid):
        if not self.labels_shown:
            self.labels_frame.grid(row=0, column=0, columnspan=6, sticky=tk.E)
            self.lb_start.grid_forget()
        MixerIngredient(self, liquid)
    
    def destroy_row(self, row_instance):
        if not isinstance(row_instance, MixerIngredient):
            return
        
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
            self.lb_start.grid(row=997, column=0, columnspan=6)
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

tk_root.mainloop()
