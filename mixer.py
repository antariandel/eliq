#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk

import types
from typing import List, Optional, Union

import fludo

from common import (float_or_zero, center_toplevel, CreateToolTip, YesNoDialog, FloatEntryDialog,
    FloatValidator, BaseDialog)


class NewIngredientDialog(BaseDialog):
    def configure_widgets(self, **kwargs):
        self.name = tk.StringVar()
        self.name.set('Unnamed Ingredient' if not 'liquid' in kwargs else kwargs['liquid'].name)

        self.pg = tk.StringVar()
        self.pg.set('0' if not 'liquid' in kwargs else kwargs['liquid'].pg)
        self.vg = tk.StringVar()
        self.vg.set('0' if not 'liquid' in kwargs else kwargs['liquid'].vg)
        self.nic = tk.StringVar()
        self.nic.set('0' if not 'liquid' in kwargs else kwargs['liquid'].nic)

        self.entry_validator = self.frame.register(self._validate_entries)

        self.name_label = ttk.Label(self.frame, text='Ingredient Name:')
        self.name_entry = ttk.Entry(self.frame, name='name_entry_%s' % id(self), width=25,
            textvariable=self.name,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        self.name_entry.focus()
        
        self.pg_label = ttk.Label(self.frame, text='PG (% vol.):')
        self.pg_entry = ttk.Entry(self.frame, name='pg_entry_%s' % id(self), width=25,
            textvariable=self.pg,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.vg_label = ttk.Label(self.frame, text='VG (% vol.):')
        self.vg_entry = ttk.Entry(self.frame, name='vg_entry_%s' % id(self), width=25,
            textvariable=self.vg,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.nic_label = ttk.Label(self.frame, text='Nicotine (mg/ml):')
        self.nic_entry = ttk.Entry(self.frame, name='nic_entry_%s' % id(self), width=25,
            textvariable=self.nic,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))

        self.hint_label = ttk.Label(self.frame,
            text=('Give your ingredient a name, PG, VG and Nicotine\n'
                  'concentration. If PG and VG don\'t add up to 100%,\n'
                  'the rest is considered water. Use 0PG/0VG to add\n'
                  'pure water. Use 0 nic. mg/ml for nic-free bases,\n'
                  'aromas and water.'))# You can turn this hint off in\n'
                 #'the settings.\n'))
        # TODO Make setting to turn this off

        self.ok_button.configure(text=str(kwargs['button_text']), width=15)
        self.cancel_button = ttk.Button(self.frame, text='Cancel', width=15,
            command=lambda: self.close(False))

        self.name_label.grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=5)
        self.pg_label.grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=5)
        self.vg_label.grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=5)
        self.nic_label.grid(
            row=4, column=0, sticky=tk.E, padx=5, pady=5)
        
        self.name_entry.grid(
            row=1, column=1, sticky=tk.E)
        self.pg_entry.grid(
            row=2, column=1, sticky=tk.E)
        self.vg_entry.grid(
            row=3, column=1, sticky=tk.E)
        self.nic_entry.grid(
            row=4, column=1, sticky=tk.E)
        
        self.hint_label.grid(row=5, column=0, columnspan=2, sticky=tk.N, pady=10)

        self.cancel_button.grid(row=10, column=1, padx=16, sticky=tk.E)
        self.ok_button.grid(row=10, column=0, padx=16, sticky=tk.W)

        center_toplevel(self.toplevel)
    
    def _validate_entries(self, action, value, widget_name):
        if 'name_entry' in widget_name:
            if action == '-1': # focus change
                if not value:
                    self.name.set('Unnamed Ingredient')
                elif self.name.get() == 'Unnamed Ingredient':
                    self.name.set('')
            if len(value) < 30:
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
    
    def set_liquid(self, liquid: fludo.Liquid):
        ''' Loads liquid properties into the dialog, for example if opened for editing. '''
        self.name.set(liquid.name)
        self.pg.set(liquid.pg)
        self.vg.set(liquid.vg)
        self.nic.set(liquid.nic)
    
    def close(self, ok_clicked, **kwargs):
        if ok_clicked:
            self.callback(fludo.Liquid(
                name='Unnamed Ingredient' if not self.name.get() else self.name.get(),
                pg=float_or_zero(self.pg.get()),
                vg=float_or_zero(self.vg.get()),
                nic=float_or_zero(self.nic.get())
            ))
        
        super().close()


class Mixer:
    '''
    This is the main class of Mixer. It creates the Liquid Mixer toplevel window and manages its
    MixerIngredientController objects (the ingredients of the mixture).
    '''
    def __init__(self, parent: tk.Widget):
        self.parent = parent

        self.toplevel = tk.Toplevel(self.parent)
        self.toplevel.title('Fludo | Liquid Mixer')
        self.toplevel.resizable(False, False)

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid(row=0, column=0, sticky=tk.W+tk.E+tk.N+tk.S)
        self.frame.grid_rowconfigure(0, minsize=32)
        self.frame.grid_columnconfigure(0, minsize=150)
        self.frame.grid_columnconfigure(1, minsize=250)
        self.frame.grid_columnconfigure(2, minsize=60)

        self.labels_frame = ttk.Frame(self.frame)
        self.labels_frame.grid_columnconfigure(5, minsize=40)
        self.labels_frame.grid_columnconfigure(3, minsize=33)

        self.max_label = ttk.Label(self.labels_frame, text='Max. (ml)')
        self.max_label.grid(row=0, column=2, padx=5)

        self.ml_label = ttk.Label(self.labels_frame, text='Vol. (ml)')
        self.ml_label.grid(row=0, column=4, padx=5)

        self.statusbar_frame = ttk.Frame(self.frame, borderwidth=1, relief=tk.GROOVE)
        self.frame.grid_rowconfigure(999, minsize=32)
        self.statusbar_frame.grid(row=999, columnspan=7, sticky=tk.W+tk.E+tk.S)
        
        self.liquid_volume = tk.StringVar()
        self.total_label = ttk.Label(self.statusbar_frame, textvariable=self.liquid_volume)
        self.total_label.grid(row=0, column=1, pady=2, sticky=tk.W)

        self.mixture_description = tk.StringVar()
        self.mixture_description_label = ttk.Label(self.statusbar_frame,
            textvariable=self.mixture_description)
        self.mixture_description_label.grid(row=0, column=0, pady=3, padx=5, sticky=tk.W)

        self.start_label = ttk.Label(self.frame, text='Start by adding an ingredient.')
        self.start_label.grid(row=997, column=0, columnspan=6)

        self.button_frame = ttk.Frame(self.frame)
        self.button_frame.grid(row=998, columnspan=6, pady=10)

        self.add_button = ttk.Button(self.button_frame, text='Add Ingredient', width=20,
            command=self.show_add_ingredient_dialog)
        self.add_button.bind('<Return>', lambda event: self.show_add_ingredient_dialog())
        
        # Ctrl+A
        self.toplevel.bind('<Control-Key-a>', lambda event: self.show_add_ingredient_dialog())
        self.add_button.grid(row=998, column=0, padx=5)

        self.change_container_button = ttk.Button(self.button_frame, text='Change Container Size',
            width=20, command=self.show_change_container_dialog)
        self.change_container_button.grid(row=998, column=1, padx=5)

        self.fill_set = False
        self.ask_remove = True

        self._labels_shown = False
        self._ingredient_list = []
        self._container_vol = 100 # Default to 100ml

        self.new_ingredient_dialog = None
        self.change_container_dialog = None

        center_toplevel(self.toplevel)
        self.toplevel.lift()
    
    def show_change_container_dialog(self) -> None:
        ''' Opens a dialog that lets the user resize the container. '''

        if self.change_container_dialog is None:
            self.change_container_dialog = FloatEntryDialog(self.toplevel,
                window_title='Change Container Size',
                text=('Enter new size in milliliters below.\n'
                      'Minimum size is 10 ml, max. is 10,000 ml.'),
                min_value=10, max_value=10000,
                default_value=self._container_vol,
                callback=self.set_container_volume,
                destroy_on_close=False)
        self.change_container_dialog.toplevel.deiconify()
        self.change_container_dialog.entry.focus()

    def set_container_volume(self, ml: Union[int, float]) -> None:
        ''' Updates the container volume (size). '''
        
        ratio = ml / self._container_vol
        self._container_vol = ml

        for row in self._ingredient_list:
            new_value = float_or_zero(row.ml.get()) * ratio
            row.ml_scale.configure(to=new_value+1) # dummy scale limit change
            row.ml_scale.set(new_value) # so that we can update it
        
        self.update()
    
    def get_container_volume(self) -> Union[int, float]:
        ''' Returns the current volume (size) of the container in milliliters. '''
        try:
            return self._container_vol
        except AttributeError:
            self._container_vol = 10
            return 10
    
    def get_mixture(self) -> fludo.Liquid:
        ''' Returns a fludo.Liquid that results from mixing every ingredient. '''
        if len(self._ingredient_list) > 1:
            return fludo.Mixture(*[row.liquid for row in self._ingredient_list])
        elif len(self._ingredient_list) == 1:
            return self._ingredient_list[0].liquid
        else:
            return fludo.Liquid(ml=0, pg=0, vg=0, nic=0)

    def update(self, skip_limiting_ingredient: Optional['MixerIngredientController']=None) -> None:
        '''
        Updates the Mixer. Called whenever a MixerIngredientController is changed.
        This method updates every MixerIngredientController instance as well, limiting their
        possible maximum volume that can be entered.
        Because the limit is constantly recalculated, to avoid rounding errors on the instance
        that's currently changed by the user, the changing instance can be skipped from limiting.
        '''
        # The ingredient which is currently calling this update when using it's scale should be
        # skipped from the remaining vol calculation.

        # Calc current total volume of ingredients (skipping ingredient that has the fill flag).
        current_total_vol = sum([float_or_zero(ingredient.ml.get()) \
            for ingredient in self._ingredient_list if not ingredient.fill_set])
        
        # Calc free volume within the container
        free_volume = self._container_vol - current_total_vol

        for ingredient in self._ingredient_list:
            # Clac ingredients possible max volume rounded to 1 digits of precision
            row_max = int((float_or_zero(ingredient.ml.get()) + free_volume) * 10) / 10

            # Limit the scale and set the max label
            if ingredient != skip_limiting_ingredient:
                ingredient.ml_scale.configure(to=row_max)
                ingredient.ml_remain.set(row_max)
            
            # If the remaining volume is smaller than the rounding error, set max label to 'Full'
            if free_volume < 0.1:
                ingredient.ml_remain.set('Full')
            else:
                ingredient.ml_remain.set(ingredient.ml_scale['to'])
            
            # If fill is set for an ingredient, clear the max label
            if ingredient.fill_set:
                ingredient.ml_remain.set('')
            
            # Set limit attribute on the ingredient
            ingredient.ml_limit = row_max

            # Update the volume of the liquid represented by the ingredient instance.
            # This propagates the change of the ml variable to the liquid object.
            ingredient.liquid.update_ml(float_or_zero(ingredient.ml.get()))
        
        # Update the status bar message
        if self.fill_set or free_volume < 0.1:
            self.liquid_volume.set('Vol. %(limit).1f (container full)' % {
                'limit': self._container_vol})
        else:
            self.liquid_volume.set('Vol. %(vol).1f ml (in %(limit).1f ml. container)' % {
                'vol': sum([float_or_zero(ingredient.ml.get()) for ingredient in self._ingredient_list]),
                'limit': self._container_vol })
        
        mixture = self.get_mixture()
        self.mixture_description.set('%dPG / %dVG, nic. %.1f mg/ml.   |' % (
            mixture.pg, mixture.vg, mixture.nic))
    
    def show_add_ingredient_dialog(self) -> None:
        ''' Opens the dialog that lets the user add a new ingredient to the mixture. '''
        if self.new_ingredient_dialog is None:
            self.new_ingredient_dialog = NewIngredientDialog(self.toplevel, self.add_ingredient,
                window_title='Add Ingredient', destroy_on_close=False, button_text='Add',
                text='Fill in the liquid\'s properties below:')
        self.new_ingredient_dialog.toplevel.deiconify()
        self.new_ingredient_dialog.name.set('Unnamed Ingredient')
        self.new_ingredient_dialog.pg.set(0)
        self.new_ingredient_dialog.vg.set(0)
        self.new_ingredient_dialog.nic.set(0)
        self.new_ingredient_dialog.name_entry.focus()
    
    def add_ingredient(self,
        liquid_or_ingredient: Union[fludo.Liquid, 'MixtureIngredientController']) -> None:
        '''
        Adds an ingredient to the mixture. If liquid_or_ingredient is a fludo.Liquid (or descendant)
        it will create a MixtureIngredientController representing the liquid.
        If it's already a MixtureIngredientController, then it will be used.
        '''
        if liquid_or_ingredient is None:
            return

        if isinstance(liquid_or_ingredient, fludo.Liquid):
            ingredient = MixerIngredientController(self, liquid_or_ingredient)
        elif isinstance(liquid_or_ingredient, MixerIngredientController):
            ingredient = liquid_or_ingredient
        else:
            raise Exception('Paremeter liquid_or_ingredient isn\'t either.')
        
        if not self._labels_shown:
            self.labels_frame.grid(row=0, column=0, columnspan=6, sticky=tk.E)
            self.start_label.grid_forget()

        self.frame.grid_rowconfigure(self.get_grid_row_idx(ingredient), minsize=30)
        current_total_vol = sum([float_or_zero(row.ml.get()) for row in self._ingredient_list])
        remaining_vol = self._container_vol - current_total_vol
        ingredient.ml_scale.configure(to=remaining_vol)
        ingredient.ml_remain.set(remaining_vol)

        self._ingredient_list.append(ingredient)
        self.update()
    
    def get_ingredient(self, ingredient_idx: int) -> 'MixerIngredientController':
        ''' Returns an ingredient object. '''
        return self._ingredient_list[ingredient_idx]
    
    def load_ingredients(self, ingredients_dict) -> None:
        '''
        Throws away any ingredient in the mixture and reloads ingredients from a dict.
        Can be used to pre-populate ingredients for example when opening a previously saved mixture.
        '''
        if not ingredients_dict:
            return

        ingredients_max_vol = sum([liquid.ml for liquid in ingredients_dict['ingredients']])
        if ingredients_max_vol > ingredients_dict['container_vol']:
            raise Exception('Ingredients volume exceeds container volume.')

        for ingredient in self._ingredient_list:
            self.remove_ingredient(ingredient)
        
        self.set_container_volume(ingredients_dict['container_vol'])

        for liquid in ingredients_dict['ingredients']:
            self.add_ingredient(liquid)
        
        if ingredients_dict['filler_idx'] is not None:
            self.toggle_fill(self._ingredient_list[ingredients_dict['filler_idx']])
        
        self.update()
    
    def get_filler_idx(self) -> Optional[int]:
        '''
        Returns the index of the ingredient that has the fill flag set. Returns None if the fill
        flag is not set on any of the ingredients.
        '''
        for idx, row in enumerate(self._ingredient_list):
            if row.fill_set:
                return idx
        return None
    
    def get_ingredients(self):
        return {
            'ingredients': [ingredient.get_liquid() for ingredient in self._ingredient_list],
            'container_vol': self.get_container_volume(),
            'filler_idx': self.get_filler_idx()
        }
    
    def remove_ingredient(self, ingredient_or_idx):
        if ingredient_or_idx is None:
            return
        
        if isinstance(ingredient_or_idx, MixerIngredientController):
            row_idx = self.get_grid_row_idx(ingredient_or_idx)
            ingredient = ingredient_or_idx
        else:
            row_idx = self.get_grid_row_idx(self.get_ingredient(ingredient_or_idx))
            ingredient = self.get_ingredient(ingredient_or_idx)

        if ingredient.fill_set:
            self.toggle_fill(ingredient)
        
        for widget in self.frame.grid_slaves():
            try:
                if widget.grid_info()['row'] == row_idx:
                    widget.grid_forget()
                    widget.destroy()
            except KeyError:
                # Already deleted by a parent widget while iterating
                pass
        self._ingredient_list.remove(ingredient_or_idx)
        self.frame.grid_rowconfigure(row_idx, minsize=0) # Hide row
        self.update()

        # Show start message if there are no rows left
        if self.get_last_grid_row_idx() == 1:
            self.labels_frame.grid_forget()
            self.start_label.grid(row=997, column=0, columnspan=6)
            self._labels_shown = False

        # FIXME Grid row recycle, so we don't count up indefinitely
        # It isn't likely to cause issues any time soon, though
    
    def get_last_grid_row_idx(self):
        last_row = 1
        for row in self._ingredient_list:
            row_idx = row.name_label.grid_info()['row']
            if row_idx > last_row:
                last_row = row_idx
        return last_row
    
    def get_grid_row_idx(self, ingredient: 'MixerIngredientController'):
        return ingredient.name_label.grid_info()['row']
    
    def get_ingredient_idx(self, ingredient: 'MixerIngredientController'):
        for ingredient, idx in enumerate(self._ingredient_list):
            if ingredient == ingredient:
                return idx
    
    def toggle_fill(self, ingredient: 'MixerIngredientController'):
        for row in self._ingredient_list:
            if row == ingredient:
                if ingredient.fill_set:
                    row._unset_fill()
                    self.fill_set = False
                    continue
                row._set_fill()
                self.fill_set = True
            else:
                row._unset_fill()
            
        self.update(skip_limiting_ingredient=ingredient)


class MixerIngredientController(FloatValidator):
    def __init__(self, mixer: Mixer, liquid: fludo.Liquid):
        if not isinstance(mixer, Mixer):
            raise Exception('Mixer parameter not instance of Mixer class.')
        if not isinstance(liquid, fludo.Liquid):
            raise Exception('Liquid parameter not instance of fludo.Liquid class.')
        
        self.mixer = mixer
        self.liquid = liquid

        self.ml = tk.StringVar()
        self.ml.set(float(self.liquid.ml))
        self.ml.trace('w', lambda var, idx, op:
            self.mixer.update(self))

        self.name = tk.StringVar()
        self.name.set(self.liquid.name)
        self.name_label = ttk.Label(self.mixer.frame, textvariable=self.name)
        self.name_label_ttip = CreateToolTip(self.name_label,
            '%(pg)dPG/%(vg)dVG, Nic. %(nic).1f' % {
                'pg': self.liquid.pg,
                'vg': self.liquid.vg,
                'nic': self.liquid.nic })

        self.ml_scale = ttk.Scale(self.mixer.frame, orient=tk.HORIZONTAL, length=250,
            to=mixer.get_container_volume(),
            variable=self.ml,
            command=lambda value:
                 self._update_var_from_scale(self.ml_scale, self.ml, digits=1))
        self.ml_scale_ttip = CreateToolTip(self.ml_scale, 'Adjust amount')

        self.ml_remain = tk.StringVar()
        self.ml_remain_label = ttk.Label(self.mixer.frame, textvariable=self.ml_remain)
        self.ml_remain_label_ttip = CreateToolTip(self.ml_remain_label,
            'Max possible amount\nfor the ingredient.')

        self.ml_entry = ttk.Entry(self.mixer.frame, width=7, textvariable=self.ml)
        self.ml_entry_validator = self.ml_entry.register(self.validate_float_entry)
        self.ml_scale_remain = lambda: self.ml_scale.cget('to')
        self.ml_entry.configure(validate='all',
            validatecommand=(self.ml_entry_validator, '%d','%P', 'ml_entry', 0, 'ml_scale_remain'))
        
        # Shown instead of the scale if fill is selected for the component
        self.fill_label = ttk.Label(self.mixer.frame, text='(will fill container)')

        self.fill_button = ttk.Button(self.mixer.frame, text='⚪', width=3, command=lambda:
            self.mixer.toggle_fill(self))
        self.fill_button_ttip = CreateToolTip(self.fill_button, 'Fill container')

        self.edit_button = ttk.Button(self.mixer.frame, text='✎', width=3, command=lambda:
            self.show_editor_dialog())
        self.edit_button_ttip = CreateToolTip(self.edit_button, 'Edit ingredient')

        self.destroy_button = ttk.Button(self.mixer.frame, text='❌', width=3, command=lambda:
            self.show_remove_dialog())
        self.destroy_button_ttip = CreateToolTip(self.destroy_button, 'Remove ingredient')

        row_idx = self.mixer.get_last_grid_row_idx() + 1 # Row number within Mixer table

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
        self.editor_dialog = None
        self.remove_dialog = None
    
    def _update_var_from_scale(self, scale, variable, digits=1):
        value = int(float(scale.get()) * pow(10, digits)) / pow(10, digits)
        variable.set(value)
    
    def _unset_fill(self):
        self.fill_label.grid_forget()
        self.ml_scale.grid(row=self.mixer.get_grid_row_idx(self), column=1)
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
        self.fill_label.grid(row=self.mixer.get_grid_row_idx(self), column=1)
        self.ml_entry.configure(state='readonly')
        self._fill_traceid = self.ml_remain.trace('w', lambda var, idx, op:
            self.ml.set(
                int( (self.mixer.get_container_volume() - sum([float_or_zero(ingredient.ml.get()) \
                    for ingredient in self.mixer._ingredient_list if ingredient != self])) * 10 ) / 10
            ))
        self.mixer.update(self)
        self.fill_button.configure(text='⚫')
        self.fill_set = True

    def show_editor_dialog(self):
        if self.editor_dialog is None:
            self.editor_dialog = NewIngredientDialog(self.mixer.toplevel, self.set_liquid,
                window_title='Edit Ingredient', button_text='OK', liquid=self.liquid,
                destroy_on_close=False, text='Fill in the liquid\'s properties below:')
        
        self.editor_dialog.set_liquid(self.liquid)
        self.editor_dialog.name_entry.focus()
        self.editor_dialog.toplevel.deiconify()
    
    def show_remove_dialog(self):
        if self.mixer.ask_remove:
            if self.remove_dialog is None:
                self.remove_dialog = YesNoDialog(self.mixer.toplevel,
                    callback=lambda ok_clicked, ingredient:
                        self.mixer.remove_ingredient(ingredient if ok_clicked else None),
                    ingredient=self,
                    window_title='Remove Ingredient',
                    text='',
                    destroy_on_close=False)
            self.remove_dialog.label.configure(
                text=('Are you sure you wish to remove\n'
                      '%(name)s, %(pg)dPG/%(vg)dVG, nic. %(nic).1f mg/ml?') % {
                'name': self.liquid.name,
                'pg': self.liquid.pg,
                'vg': self.liquid.vg,
                'nic': self.liquid.nic })
            self.remove_dialog.ok_button.focus()
            self.remove_dialog.toplevel.deiconify()

    def set_liquid(self, liquid):
        self.liquid = liquid
        if self.liquid.ml > 0:
            self.ml.set(self.liquid.ml)
        self.name.set(self.liquid.name)
        self.name_label_ttip = CreateToolTip(self.name_label,
            '%(pg)dPG/%(vg)dVG, Nic. %(nic).1f' % {
                'pg': self.liquid.pg,
                'vg': self.liquid.vg,
                'nic': self.liquid.nic })
        self.mixer.update()
    
    def get_liquid(self):
        return self.liquid