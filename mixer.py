import tkinter as tk
from tkinter import ttk

import types
from typing import List, Optional, Union

import fludo

from common import (float_or_zero, round_digits, center_toplevel, CreateToolTip, YesNoDialog,
    FloatEntryDialog, FloatValidator, BaseDialog, StringDialog, VerticalScrolledFrame, TextDialog)
from images import icons, set_icon

import const

const.CONTAINER_MIN = 10
const.CONTAINER_MAX = 10000
const.MAX_INGREDIENTS = 20
# TODO Limit the max number of ingredients allowed when adding, by disabling the Add button.
const.MAX_MIXTURE_NAME_LENGTH = 30
#const.MAX_NOTES_LENGTH = 2000
const.MAX_NIC_CONCENTRATION = 1000
const.DEFAULT_MIXTURE_NAME = 'My Mixture'
const.DEFAULT_INGREDIENT_NAME = 'Unnamed Ingredient'
const.DEFAULT_NOTES_CONTENT = 'No notes added yet.'

class NewIngredientDialog(BaseDialog):
    '''
    With this dialog the user can define a liquid. It will pass a fludo.Liquid to the callback.
    '''

    def configure_widgets(self, **kwargs):
        self.name = tk.StringVar()
        self.name.set(const.DEFAULT_INGREDIENT_NAME \
            if not 'liquid' in kwargs else kwargs['liquid'].name)

        self.pg = tk.StringVar()
        self.pg.set('0' if not 'liquid' in kwargs else kwargs['liquid'].pg)
        self.pg.trace_add('write', self._recalc_water)
        self.vg = tk.StringVar()
        self.vg.set('0' if not 'liquid' in kwargs else kwargs['liquid'].vg)
        self.vg.trace_add('write', self._recalc_water)
        self.nic = tk.StringVar()
        self.nic.set('0' if not 'liquid' in kwargs else kwargs['liquid'].nic)
        self.cost = tk.StringVar()
        self.cost.set('0' if not 'liquid' in kwargs else kwargs['liquid'].cost_per_ml)
        self.water = tk.StringVar()
        self.water.set('0' if not 'liquid' in kwargs else 100 - (kwargs['liquid'].pg + kwargs['liquid'].vg))

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
        
        self.water_label = ttk.Label(self.frame, text='Water (% vol.):')
        self.water_value = ttk.Label(self.frame, textvariable=self.water)
        
        self.nic_label = ttk.Label(self.frame, text='Nicotine (mg/ml):')
        self.nic_entry = ttk.Entry(self.frame, name='nic_entry_%s' % id(self), width=25,
            textvariable=self.nic,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.cost_label = ttk.Label(self.frame, text='Cost/ml:')
        self.cost_entry = ttk.Entry(self.frame, name='cost_entry_%s' % id(self), width=25,
            textvariable=self.cost,
            validate='all', validatecommand=(self.entry_validator, '%d', '%P', '%W'))
        
        self.allow_water = tk.IntVar()
        self.allow_water_checkbox = ttk.Checkbutton(self.frame, text='Allow Water',
            variable=self.allow_water, command=self._water_fix)

        self.ok_button.configure(text=str(kwargs['button_text']), width=15)
        self.cancel_button = ttk.Button(self.frame, text='Cancel', width=15,
            command=lambda: self.close(False))

        self.name_label.grid(
            row=1, column=0, sticky=tk.E, padx=5, pady=5)
        self.pg_label.grid(
            row=2, column=0, sticky=tk.E, padx=5, pady=5)
        self.vg_label.grid(
            row=3, column=0, sticky=tk.E, padx=5, pady=5)
        self.water_label.grid(
            row=4, column=0, sticky=tk.E, padx=5, pady=5)
        self.nic_label.grid(
            row=5, column=0, sticky=tk.E, padx=5, pady=5)
        self.cost_label.grid(
            row=6, column=0, sticky=tk.E, padx=5, pady=5)
        
        self.name_entry.grid(
            row=1, column=1, sticky=tk.E)
        self.pg_entry.grid(
            row=2, column=1, sticky=tk.E)
        self.vg_entry.grid(
            row=3, column=1, sticky=tk.E)
        self.water_value.grid(
            row=4, column=1, sticky=tk.W)
        self.nic_entry.grid(
            row=5, column=1, sticky=tk.E)
        self.cost_entry.grid(
            row=6, column=1, sticky=tk.E)
        self.allow_water_checkbox.grid(
            row=7, column=1, sticky=tk.W)

        self.cancel_button.grid(row=10, column=1, padx=16, sticky=tk.E)
        self.ok_button.grid(row=10, column=0, padx=16, sticky=tk.W)

        center_toplevel(self.toplevel)
    
    def _recalc_water(self, *args):
        self.water.set(100 - (float_or_zero(self.pg.get()) + float_or_zero(self.vg.get())))
    
    def _water_fix(self):
        if not self.allow_water.get():
            self.vg.set(100-float_or_zero(self.pg.get()))
    
    def _validate_entries(self, action, value, widget_name):
        ''' Validator for all entry fields. '''

        if 'name_entry' in widget_name:
            if action == '-1': # focus change
                if not value:
                    self.name.set(const.DEFAULT_INGREDIENT_NAME)
                elif self.name.get() == const.DEFAULT_INGREDIENT_NAME:
                    self.name.set('')
            if len(value) < 30:
                return True
            else:
                return False
        
        if 'pg_entry' in widget_name:
            if float_or_zero(value) > 100:
                return False
            
            if not self.allow_water.get():
                self.vg.set(100-float_or_zero(value))
                return True
            elif (float_or_zero(value) + float_or_zero(self.vg.get())) > 100:
                self.vg.set(100-float_or_zero(value))
            
            if action == '-1': #focus change
                if not value:
                    self.pg.set(0)
        
        if 'vg_entry' in widget_name:
            if float_or_zero(value) > 100:
                return False
            
            if not self.allow_water.get():
                self.pg.set(100-float_or_zero(value))
                return True
            elif (float_or_zero(value) + float_or_zero(self.pg.get())) > 100:
                self.pg.set(100-float_or_zero(value))
            
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
        
        if 'nic_entry' in widget_name or 'cost_entry' in widget_name:
            if action == '-1': #focus change
                if not value:
                    self.nic.set(0)
            
            if value:
                try:
                    float(value)
                    if float(value) < 0 or float(value) > const.MAX_NIC_CONCENTRATION:
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
        self.cost.set(liquid.cost_per_ml)
    
    def close(self, ok_clicked, **kwargs):
        ''' Close and return the fludo.Liquid if ok_button is clicked. Otherwise just close. '''

        if ok_clicked:
            self.callback(fludo.Liquid(
                name=const.DEFAULT_INGREDIENT_NAME if not self.name.get() else self.name.get(),
                pg=float_or_zero(self.pg.get()),
                vg=float_or_zero(self.vg.get()),
                nic=float_or_zero(self.nic.get()),
                cost_per_ml=float_or_zero(self.cost.get())
            ))
        
        super().close()


class Mixer:
    '''
    This is the main class of Mixer. It creates the Liquid Mixer toplevel window and manages its
    MixerIngredientController objects (the ingredients of the mixture).
    '''

    def __init__(self, parent: tk.Widget=None, mixture_name: str=const.DEFAULT_MIXTURE_NAME,
        save_callback: types.FunctionType=None, save_callback_args: list=[],
        discard_callback: types.FunctionType=None, discard_callback_args: list=[]):

        if parent is None:
            # assume that we need to be Tk root
            self.parent = None
            self.toplevel = tk.Tk()
        else:
            self.parent = parent
            self.toplevel = tk.Toplevel(self.parent)
        self.root = self.toplevel.nametowidget('.')
        
        self.toplevel.withdraw()
        
        self.name = tk.StringVar()
        self.name.set(mixture_name)

        self.toplevel.title('Fludo | Liquid Mixer')
        self.toplevel.iconbitmap(icons['app-icon'])
        self.toplevel.minsize(0, 280)
        self.toplevel.resizable(False, True)
        self.toplevel.grid_columnconfigure(0, weight=1)
        self.toplevel.grid_rowconfigure(3, weight=1)

        self.name_frame = ttk.Frame(self.toplevel)
        self.name_entry = ttk.Entry(self.name_frame, textvariable=self.name)
        self.name_entry.configure(font=('Arial', 19))
        self._name_entry_validator = self.name_entry.register(self.validate_name_entry)
        self.name_entry.configure(validate='all',
            validatecommand=(self._name_entry_validator, '%d', '%P'))
        self.name_entry.grid(row=0, column=0, padx=10, sticky=tk.EW)
        self.name_frame.grid_columnconfigure(0, weight=1)
        self.name_frame.grid(row=1, column=0, padx=10, pady=10, sticky=tk.EW)

        self.frame = VerticalScrolledFrame(self.toplevel)
        self.frame.interior.grid_columnconfigure(1, weight=1)
        self.frame.interior.grid_columnconfigure(2, minsize=80)
        self.frame.grid(row=3, column=0, sticky=tk.EW+tk.NS)

        self.labels_frame = ttk.Frame(self.toplevel)

        self.max_label = ttk.Label(self.labels_frame, text='Max. (ml)')
        self.max_label.grid(row=0, column=0, padx=5)
        self.labels_frame.columnconfigure(1, minsize=45)

        self.ml_label = ttk.Label(self.labels_frame, text='Vol. (ml)')
        self.ml_label.grid(row=0, column=2, padx=5)
        self.labels_frame.columnconfigure(3, minsize=118)

        self.statusbar_frame = ttk.Frame(self.toplevel)
        self.statusbar_frame.grid(row=999, column=0, sticky=tk.EW)
        self.statusbar_frame.grid_columnconfigure(2, weight=1)
        
        self.liquid_volume = tk.StringVar()
        self.total_label = ttk.Label(self.statusbar_frame, textvariable=self.liquid_volume)
        self.total_label.configure(font=('Arial', 11))
        self.total_label.grid(row=0, column=1, pady=2, sticky=tk.W)

        self.mixture_description = tk.StringVar()
        self.mixture_description_label = ttk.Label(self.statusbar_frame,
            textvariable=self.mixture_description)
        self.mixture_description_label.configure(font=('Arial', 11, 'bold'))
        self.mixture_description_label.grid(row=0, column=0, pady=3, padx=5, sticky=tk.W)

        self.start_label = ttk.Label(self.frame.interior,
            text='Add some ingredients to your mixture:')
        self.start_label.grid(row=998, column=0, columnspan=6, sticky=tk.E)

        self.add_button = ttk.Button(self.frame.interior, text='', width=4,
            command=self.show_add_ingredient_dialog)
        self.add_button_ttip = CreateToolTip(self.add_button, 'Add new ingredient to the mixture.')
        set_icon(self.add_button, icons['plus'], compound=tk.NONE)
        self.add_button.grid(row=998, column=6, padx=14, pady=3)
        self.toplevel.bind('<Shift-A>', lambda event: self.show_add_ingredient_dialog())
        self.toplevel.bind('<Shift-a>', lambda event: self.show_add_ingredient_dialog())

        self.button_frame = ttk.Frame(self.toplevel)
        self.button_frame.grid(row=0, column=0, columnspan=2, sticky=tk.EW)

        self.change_bottle_button = ttk.Button(self.button_frame, text='Resize Bottle',
            width=22, command=self.show_change_bottle_dialog)
        self.change_bottle_button_ttip = CreateToolTip(self.change_bottle_button,
            'Resize the bottle preserving ingredient proportions.')
        set_icon(self.change_bottle_button, icons['bottle-icon-resize'])
        self.change_bottle_button.grid(row=0, column=0)

        self.view_bottle_button = ttk.Button(self.button_frame, text='View Bottle', width=22,
            state=tk.DISABLED)
        set_icon(self.view_bottle_button, icons['bottle-icon'])
        self.view_bottle_button.grid(row=0, column=1)
        
        self.add_notes_button = ttk.Button(self.button_frame, text='Add Notes', width=22,
            command=self.show_add_notes_dialog)
        set_icon(self.add_notes_button, icons['file'])
        self.add_notes_button.grid(row=0, column=2)

        self.save_button = ttk.Button(self.button_frame, text='Save & Close', width=22,
            command=lambda: self.close(True))
        set_icon(self.save_button, icons['save'])
        self.save_button.grid(row=0, column=3)

        self.discard_button = ttk.Button(self.button_frame, text='Discard & Close', width=22,
            command=self.show_discard_dialog)
        set_icon(self.discard_button, icons['x-square'])
        self.discard_button.grid(row=0, column=4)
 
        self.fill_set = False

        self._labels_shown = False
        self._ingredient_list = []
        self._bottle_vol = 100 # Default to 100ml
        self.total_cost = 0
        self.notes = const.DEFAULT_NOTES_CONTENT
        self.save_callback = save_callback
        self.save_callback_args = save_callback_args
        self.discard_callback = discard_callback
        self.discard_callback_args = discard_callback_args

        self.new_ingredient_dialog = None
        self.change_bottle_dialog = None
        self.add_notes_dialog = None
        self.discard_dialog = None

        center_toplevel(self.toplevel)
        self.toplevel.lift()
    
    def validate_name_entry(self, action: str, value: str) -> bool:
        # Update field to default name if unfocused when blank.
        if action == '-1': # focus change action
            if self.name.get() == const.DEFAULT_MIXTURE_NAME:
                self.name.set('')
            elif not self.name.get():
                self.name.set(const.DEFAULT_MIXTURE_NAME)
        
        # Allow names shorter than MAX_MIXTURE_NAME_LENGTH
        if value:
            if len(value) > const.MAX_MIXTURE_NAME_LENGTH:
                return False
            else:
                return True
        else:
            # Allow empty string, so we can delete the contents completely
            return True
    
    def set_bottle_volume(self, ml: Union[int, float]) -> None:
        ''' Updates the bottle volume (size). '''

        if ml > const.CONTAINER_MAX:
            raise Exception('Parameter ml larger than maximum allowed!')
        if ml < const.CONTAINER_MIN:
            raise Exception('Parameter ml smaller than minimum allowed!')
        
        ratio = ml / self._bottle_vol
        self._bottle_vol = ml

        # Recalc every ingredients volume to preserve ratio.
        for ingredient in self._ingredient_list:
            new_value = float_or_zero(ingredient.ml.get()) * ratio
            ingredient.ml_scale.configure(to=new_value+1) # dummy scale limit change
            ingredient.ml_scale.set(new_value) # so that we can update it
        
        self.update()
    
    def get_bottle_volume(self) -> Union[int, float]:
        ''' Returns the current volume (size) of the bottle in milliliters. '''

        try:
            return self._bottle_vol
        except AttributeError:
            self._bottle_vol = 10
            return 10
    
    def show_change_bottle_dialog(self) -> None:
        ''' Opens a dialog that lets the user resize the bottle. '''

        if self.change_bottle_dialog is None:
            self.change_bottle_dialog = FloatEntryDialog(self.toplevel,
                window_title='Change Bottle Size',
                text=('Enter new size in milliliters below.\n'
                      'Minimum size is {} ml, max. is {} ml.').format(const.CONTAINER_MIN,
                        const.CONTAINER_MAX),
                min_value=const.CONTAINER_MIN, max_value=const.CONTAINER_MAX,
                default_value=self._bottle_vol,
                callback=self.set_bottle_volume,
                destroy_on_close=False)
        self.change_bottle_dialog.toplevel.deiconify()
        self.change_bottle_dialog.entry.focus()
        self.change_bottle_dialog.entry.select_range(0, tk.END)
    
    def set_notes(self, notes: str) -> None:
        self.notes = notes
    
    def get_notes(self) -> str:
        return self.notes
    
    def show_add_notes_dialog(self) -> None:
        ''' Opens a dialog that lets the user add some notes to their mixture. '''

        if self.add_notes_dialog is None:
            self.add_notes_dialog = TextDialog(self.toplevel,
                window_title='Fludo | Add Notes | {}'.format(self.name.get()),
                text='Add your notes below:',
                text_content=self.get_notes(),
                default_value=const.DEFAULT_NOTES_CONTENT,
                callback=self.set_notes,
                destroy_on_close=False)
            self.add_notes_dialog.ok_button.configure(text='Save & Close')
        if self.get_notes():
            self.add_notes_dialog.text.delete('0.0', tk.END)
            self.add_notes_dialog.text.insert('0.0', self.get_notes())
        self.add_notes_dialog.toplevel.deiconify()
    
    def show_discard_dialog(self) -> None:
        ''' Asks the user one more time if they want to discard the mixture. '''

        def close_if_ok_clicked(ok_clicked):
            if ok_clicked:
                self.close(False)

        if self.discard_dialog is None:
            self.discard_dialog = YesNoDialog(self.toplevel,
                window_title='Are you sure?',
                text='Are you sure you wish to discard your edits to\n{}?'.format(self.name.get()),
                callback=close_if_ok_clicked,
                destroy_on_close=False)
        self.discard_dialog.toplevel.deiconify()
    
    def rename(self, new_name) -> None:
        if len(new_name) < const.MAX_MIXTURE_NAME_LENGTH:
            self.name.set(new_name)
        else:
            raise Exception('Name too long!')
    
    def add_ingredient(self,
        liquid_or_ingredient: Union[fludo.Liquid, 'MixtureIngredientController']) -> None:
        '''
        Adds an ingredient to the mixture. If liquid_or_ingredient is a fludo.Liquid (or descendant)
        it will create a MixtureIngredientController representing the liquid.
        If it's already a MixtureIngredientController, then it will be used as is.
        '''

        if liquid_or_ingredient is None:
            return

        if isinstance(liquid_or_ingredient, fludo.Liquid):
            ingredient = MixerIngredientController(self, liquid_or_ingredient, auto_add=False)
        elif isinstance(liquid_or_ingredient, MixerIngredientController):
            ingredient = liquid_or_ingredient
        else:
            raise TypeError('Paremeter liquid_or_ingredient isn\'t the right type.')

        self.frame.interior.grid_rowconfigure(self.get_ingredient_grid_row(ingredient), minsize=30)
        current_total_vol = sum([float_or_zero(row.ml.get()) for row in self._ingredient_list])
        remaining_vol = self._bottle_vol - current_total_vol
        ingredient.ml_scale.configure(to=remaining_vol)
        ingredient.ml_max.set(remaining_vol)

        self._ingredient_list.append(ingredient)
        self.update()

        # Hide start message
        if not self._labels_shown:
            self.labels_frame.grid(row=2, column=0, sticky=tk.E)
            self.start_label.grid_forget()
    
    def show_add_ingredient_dialog(self) -> None:
        ''' Opens the dialog that lets the user add a new ingredient to the mixture. '''

        if self.new_ingredient_dialog is None:
            self.new_ingredient_dialog = NewIngredientDialog(self.toplevel, self.add_ingredient,
                window_title='Add Ingredient', destroy_on_close=False, button_text='Add',
                text='Fill in the ingredient\'s properties below:')
        self.new_ingredient_dialog.toplevel.deiconify()
        self.new_ingredient_dialog.name.set(const.DEFAULT_INGREDIENT_NAME)
        self.new_ingredient_dialog.pg.set(50)
        self.new_ingredient_dialog.vg.set(50)
        self.new_ingredient_dialog.nic.set(0)
        self.new_ingredient_dialog.name_entry.focus()
    
    def get_ingredient(self, ingredient_idx: int) -> 'MixerIngredientController':
        ''' Returns an ingredient object with given index. '''

        return self._ingredient_list[ingredient_idx]
    
    def get_ingredient_idx(self, ingredient: 'MixerIngredientController') -> int:
        ''' Returns the ingredient's index. '''

        for idx, ingred in enumerate(self._ingredient_list):
            if ingred == ingredient:
                return idx
    
    def remove_ingredient(self, ingredient_or_idx: Union['MixerIngredientController', int]) -> None:
        ''' Remove an ingredient either by index or ingredient instance. '''

        if ingredient_or_idx is None:
            return
        
        if isinstance(ingredient_or_idx, MixerIngredientController):
            grid_row_idx = self.get_ingredient_grid_row(ingredient_or_idx)
            ingredient = ingredient_or_idx
        else:
            grid_row_idx = self.get_ingredient_grid_row(self.get_ingredient(ingredient_or_idx))
            ingredient = self.get_ingredient(ingredient_or_idx)

        if ingredient.fill_set:
            self.toggle_fill(ingredient)
        
        for widget in self.frame.interior.grid_slaves():
            try:
                if widget.grid_info()['row'] == grid_row_idx:
                    widget.grid_forget()
                    widget.destroy()
            except KeyError:
                # Already deleted by a parent widget while iterating
                pass
        self._ingredient_list.remove(ingredient_or_idx)
        self.frame.interior.grid_rowconfigure(grid_row_idx, minsize=0) # Hide row
        self.update()

        # Show start message if there are no rows left
        if self.get_last_grid_row() == 0:
            self.labels_frame.grid_forget()
            self.start_label.grid(row=998, column=0, columnspan=6, sticky=tk.E)
            self._labels_shown = False

        # FIXME Grid row recycle, so we don't count up with grid rows indefinitely
        # It isn't likely to cause issues any time soon, though
    
    def get_mixture(self) -> Union[fludo.Mixture, None]:
        ''' Returns a fludo.Mixture that results from mixing every ingredient. '''

        if len(self._ingredient_list) > 0:
            return fludo.Mixture(*[ingredient.liquid for ingredient in self._ingredient_list])
        else:
            return None
    
    def number_of_ingredients(self) -> int:
        ''' Returns the number of ingredients currently in the Mixer. '''

        return len(self._ingredient_list)
    
    def get_last_grid_row(self) -> int:
        ''' Returns the last grid row that doesn't have an ingredient's widgets. '''

        last_row = -1
        for row in self._ingredient_list:
            grid_row_idx = row.name_label.grid_info()['row']
            if grid_row_idx > last_row:
                last_row = grid_row_idx
        return last_row+1
    
    def get_ingredient_grid_row(self,
        ingredient_or_idx: Union['MixerIngredientController', int]) -> int:
        ''' Returns the grid row the ingredient resides in. '''

        if isinstance(ingredient_or_idx, int):
            return self.get_ingredient(ingredient_or_idx).name_label.grid_info()['row']
        else:
            return ingredient_or_idx.name_label.grid_info()['row']
    
    def toggle_fill(self, ingredient: 'MixerIngredientController') -> None:
        ''' Toggles the fill behaviour on the ingredients. '''

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
    
    def get_filler_idx(self) -> Union[int, None]:
        '''
        Returns the index of the ingredient that has the fill flag set. Returns None if the fill
        flag is not set on any of the ingredients.
        '''

        for idx, row in enumerate(self._ingredient_list):
            if row.fill_set:
                return idx
        return None
    
    def load(self, loadable_dict) -> None:
        '''
        Throws away any ingredient in the Mixer and reloads ingredients from a loadable dict, so
        it be used to pre-populate ingredients for example when opening a previously saved mixture.
        Mixer.get_loadable() returns a loadable dict, which looks like this:

        loadable_dict = {
            'ingredients': [fludo.Liquid, ...],
            'name': str,
            'notes': str,
            'filler_idx': Optional[int],
            'bottle_vol': int,
        }
        '''

        if not loadable_dict:
            return
        
        if ('ingredients' not in loadable_dict or
            'filler_idx' not in loadable_dict or
            'bottle_vol' not in loadable_dict):
            raise Exception('ingredients, filler_idx and bottle_vol '
                'are expected keys in loadable_dict')

        ingredients_max_vol = sum([liquid.ml for liquid in loadable_dict['ingredients']])
        if ingredients_max_vol > loadable_dict['bottle_vol']:
            raise Exception('Ingredients volume exceeds bottle volume.')
        
        if loadable_dict['bottle_vol'] < const.CONTAINER_MIN:
            raise ValueError('Bottle volume is lesser than minimum allowed!')
        if loadable_dict['bottle_vol'] > const.CONTAINER_MAX:
            raise ValueError('Bottle volume is greater than maximum allowed!')
        if len(loadable_dict['ingredients']) > const.MAX_INGREDIENTS:
            raise ValueError('Number of ingredients exceeds the maximum allowed!')

        # Seems okay, purge and load:

        for ingredient in self._ingredient_list:
            self.remove_ingredient(ingredient)
        
        self.set_bottle_volume(loadable_dict['bottle_vol'])

        for liquid in loadable_dict['ingredients']:
            self.add_ingredient(liquid)
        
        if loadable_dict['filler_idx'] is not None:
            self.toggle_fill(self._ingredient_list[loadable_dict['filler_idx']])
        
        if 'name' in loadable_dict:
            self.rename(loadable_dict['name'])
        else:
            self.rename(const.DEFAULT_MIXTURE_NAME)
        
        if 'notes' in loadable_dict:
            self.set_notes(loadable_dict['notes'])
        else:
            self.set_notes(const.DEFAULT_NOTES_CONTENT)
        
        self.update()
        center_toplevel(self.toplevel)
    
    def dump(self) -> dict:
        '''
        Returns all ingredients, the bottle volume, the filler ingredient's index and the name
        of the mixture in a dict. The returned dict can be passed to Mixer.load to load it up.
        '''

        return {
            'ingredients': [ingredient.get_liquid() for ingredient in self._ingredient_list],
            'bottle_vol': self.get_bottle_volume(),
            'filler_idx': self.get_filler_idx(),
            'name': self.name.get(),
            'notes': self.get_notes()
        }
    
    def update(self, skip_limiting_ingredient: Optional['MixerIngredientController']=None) -> None:
        '''
        Updates the Mixer. Called whenever a MixerIngredientController is changed.
        This method updates every MixerIngredientController instance as well, limiting their
        possible maximum volume that can be entered.
        Because the limit is constantly recalculated, to avoid rounding errors on the instance
        that's currently changed by the user, the changing instance can be skipped from limiting.
        '''

        # The ingredient which is currently calling this update when using it's scale should be
        # skipped from the limit calculation.

        # Calc current total volume of ingredients (skipping ingredient that has the fill flag).
        current_total_vol = sum([float_or_zero(ingredient.ml.get()) \
            for ingredient in self._ingredient_list if not ingredient.fill_set])
        
        # Calc free volume within the bottle
        free_volume = self._bottle_vol - current_total_vol

        new_total_cost = 0
        for ingredient in self._ingredient_list:
            # Clac ingredients possible max volume rounded to 1 digits of precision
            ingredient_max = int((float_or_zero(ingredient.ml.get()) + free_volume) * 10) / 10

            # Limit the scale and set the max label
            if ingredient != skip_limiting_ingredient:
                ingredient.ml_scale.configure(to=ingredient_max)
                ingredient.ml_max.set(ingredient_max)
            
            # If the remaining volume is smaller than the rounding error, set max label to 'Full'
            if free_volume < 0.1:
                ingredient.ml_max.set('Full')
            else:
                ingredient.ml_max.set(ingredient.ml_scale['to'])
            
            # If fill is set for an ingredient, clear the max label
            if ingredient.fill_set:
                ingredient.ml_max.set('')

            # Update the volume of the liquid represented by the ingredient instance.
            # This propagates the change of the ml variable to the liquid object.
            ingredient.liquid.update_ml(float_or_zero(ingredient.ml.get()))
            new_total_cost = ingredient.liquid.get_cost()
        
        self.total_cost = new_total_cost
        
        # Update the status bar message
        if self.fill_set or free_volume < 0.1:
            self.liquid_volume.set(' |  Vol. %(limit).1f ml (bottle full)' % {
                'limit': self._bottle_vol})
        else:
            self.liquid_volume.set(' |  Vol. %(vol).1f ml (in %(limit).1f ml. bottle)' % {
                'vol': sum([float_or_zero(ingredient.ml.get()) \
                    for ingredient in self._ingredient_list]),
                'limit': self._bottle_vol })
        
        mixture = self.get_mixture()

        if mixture:
            self.mixture_description.set('%d%% PG / %d%% VG, Nic. %.1f mg/ml, Cost: %.1f' % (
                mixture.pg, mixture.vg, mixture.nic, mixture.get_cost()))
        else:
            self.mixture_description.set('Nothing to mix. |')
    
    def close(self, save: bool=False) -> None:
        '''
        Optionally calls the save callback then closes the mixer.
        '''

        if save and self.save_callback:
            self.save_callback(self.dump(), *self.save_callback_args)
        else:
            self.discard_callback(*self.discard_callback_args)
        self.toplevel.destroy()


class MixerIngredientController(FloatValidator):
    '''
    Class of ingredient instances residing in a Mixer. It will add it's own widgets to Mixer's
    frame. When auto_add is true, it will also call Mixer's add_ingredient method, this is what
    normally happens if MixerIngredientController is instantiated independently from Mixer.

    When it's instantiated from Mixer's add_ingredient, auto_add must be False, so it doesn't call
    the add_ingredient method a second time.

    The sole purpose of this class is to control a single fludo.Liquid's properties.
    '''

    def __init__(self, mixer: Mixer, liquid: fludo.Liquid, auto_add: bool=True):
        if not isinstance(mixer, Mixer):
            raise Exception('Mixer parameter not instance of Mixer class.')
        if not isinstance(liquid, fludo.Liquid):
            raise Exception('Liquid parameter not instance of fludo.Liquid class.')
        
        self.mixer = mixer
        self.liquid = liquid

        self.ml = tk.StringVar()
        self.ml.set(float(self.liquid.ml))
        self._ml_traceid = self.ml.trace('w', lambda var, idx, op:
            self.mixer.update(self))

        self.name = tk.StringVar()
        self.name.set(self.liquid.name)
        self.name_label = ttk.Label(self.mixer.frame.interior, textvariable=self.name)
        self.name_label_ttip = CreateToolTip(self.name_label,
            '%(pg)dPG/%(vg)dVG, Nic. %(nic).1f' % {
                'pg': self.liquid.pg,
                'vg': self.liquid.vg,
                'nic': self.liquid.nic })

        self.ml_scale = ttk.Scale(self.mixer.frame.interior, orient=tk.HORIZONTAL, length=250,
            to=mixer.get_bottle_volume(),
            variable=self.ml,
            command=lambda value:
                self.ml.set(round_digits(self.ml_scale.get(), 1)))
        self.ml_scale_ttip = CreateToolTip(self.ml_scale, 'Adjust amount')

        self.ml_max = tk.StringVar()
        self.ml_max_label = ttk.Label(self.mixer.frame.interior, textvariable=self.ml_max)
        self.ml_max_label_ttip = CreateToolTip(self.ml_max_label,
            'Max possible amount\nfor the ingredient.')

        self.ml_entry = ttk.Entry(self.mixer.frame.interior, width=7, textvariable=self.ml)
        self.ml_entry_validator = self.ml_entry.register(self.validate_float_entry) # FloatValidator

        # This function always returns the max volume possible for the ingredient, so that the
        # validator follows the changes in the max possible volume
        self.get_max_ml = lambda: self.ml_scale.cget('to')

        self.ml_entry.configure(validate='all',
            validatecommand=(self.ml_entry_validator, '%d','%P', 'ml_entry', 0, 'get_max_ml'))
        
        # Shown instead of the scale if fill is selected for the component
        self.fill_label = ttk.Label(self.mixer.frame.interior, text='(will fill bottle)')

        self.fill_button = ttk.Button(self.mixer.frame.interior, width=32,
            command=lambda: self.mixer.toggle_fill(self))
        set_icon(self.fill_button, icons['bottle-icon-fill'], compound=tk.NONE)
        self.fill_button_ttip = CreateToolTip(self.fill_button, 'Fill bottle')

        self.edit_button = ttk.Button(self.mixer.frame.interior, width=32,
            command=lambda: self.show_editor_dialog())
        set_icon(self.edit_button, icons['edit-2'], compound=tk.NONE)
        self.edit_button_ttip = CreateToolTip(self.edit_button, 'Edit ingredient')

        self.destroy_button = ttk.Button(self.mixer.frame.interior, width=4,
            command=lambda: self.show_remove_dialog())
        set_icon(self.destroy_button, icons['minus'], compound=tk.NONE)
        self.destroy_button_ttip = CreateToolTip(self.destroy_button, 'Remove ingredient')

        grid_row_idx = self.mixer.get_last_grid_row() # Grid row number within Mixer frame

        self.name_label.grid(
            row=grid_row_idx, column=0, padx=10, sticky=tk.E)
        self.ml_scale.grid(
            row=grid_row_idx, column=1, sticky=tk.EW)
        self.ml_max_label.grid(
            row=grid_row_idx, column=2, padx=17)
        self.fill_button.grid(
            row=grid_row_idx, column=3, padx=5)
        self.ml_entry.grid(
            row=grid_row_idx, column=4, padx=5)
        self.edit_button.grid(
            row=grid_row_idx, column=5, padx=5)
        self.destroy_button.grid(
            row=grid_row_idx, column=6, padx=14)
        
        self.fill_set = False
        self.editor_dialog = None
        self.remove_dialog = None

        # Add self to Mixer if auto_add is True.
        if auto_add:
            self.mixer.add_ingredient(self)
    
    def _unset_fill(self) -> None:
        ''' Only Mixer must call this when toggling the fill. '''

        self.fill_label.grid_forget()
        self.ml_scale.grid(row=self.mixer.get_ingredient_grid_row(self), column=1, sticky=tk.EW)
        self.ml_entry.configure(state='normal')
    
        try:
            self.ml_max.trace_vdelete('w', self._fill_traceid)
            del(self._fill_traceid)
        except (AttributeError, tk._tkinter.TclError):
            # not set
            pass
        
        try:
            self._ml_traceid
        except AttributeError:
            self._ml_traceid = self.ml.trace('w', lambda var, idx, op:
                self.mixer.update(self))
        
        self.mixer.update(self)
        set_icon(self.fill_button, icons['bottle-icon-fill'], compound=tk.NONE)
        self.fill_set = False

    def _set_fill(self) -> None:
        ''' Only Mixer must call this when toggling the fill. '''

        self.ml_scale.grid_forget()
        self.fill_label.grid(row=self.mixer.get_ingredient_grid_row(self), column=1)
        self.ml_entry.configure(state='readonly')

        try:
            self.ml.trace_vdelete('w', self._ml_traceid)
            del(self._ml_traceid)
        except (AttributeError, tk._tkinter.TclError):
            # not set
            pass

        try:
            self._fill_traceid
        except AttributeError:
            self._fill_traceid = self.ml_max.trace('w', lambda var, idx, op:
                self.ml.set(
                    int( (self.mixer.get_bottle_volume() - sum([float_or_zero(ingr.ml.get()) \
                        for ingr in self.mixer._ingredient_list if ingr != self])) * 10 ) / 10
                ))
        
        self.mixer.update(self)
        set_icon(self.fill_button, icons['bottle-icon-filled'], compound=tk.NONE)
        self.fill_set = True

    def show_editor_dialog(self) -> None:
        ''' Opens an editor so the liquid's properties can be changed. '''

        if self.editor_dialog is None:
            self.editor_dialog = NewIngredientDialog(self.mixer.toplevel, self.set_liquid,
                window_title='Edit Ingredient', button_text='OK', liquid=self.liquid,
                destroy_on_close=False, text='Fill in the liquid\'s properties below:')
        
        self.editor_dialog.set_liquid(self.liquid)
        self.editor_dialog.name_entry.focus()
        self.editor_dialog.toplevel.deiconify()
    
    def show_remove_dialog(self) -> None:
        ''' Asks the user if they are sure to remove the ingredient from Mixer. '''

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

    def set_liquid(self, liquid: fludo.Liquid) -> None:
        ''' Sets the liquid the controller represents. '''

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
    
    def get_liquid(self) -> fludo.Liquid:
        ''' Returns the represented liquid. '''

        return self.liquid
