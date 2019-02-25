import uuid
import copy

import tkinter as tk
from tkinter import ttk

import fludo

from common import center_toplevel, round_digits, YesNoDialog
from common_ui import CommonUI
from library_ui import LibraryUI
from storage import ObjectStorage
from mixer import Mixer
from viewer import BottleViewer
from images import icons, set_icon
from version import VERSION


class Library:
    def __init__(self, library_ui = LibraryUI(None), mixer = Mixer, viewer = BottleViewer,
                library_db_file: str = 'library.db',  library_table_name: str = 'recipes'):
        
        self.ui = library_ui
        self.ui.refresh_mixture_list()

        self.mixer = mixer
        self.viewer = viewer

        self.mixtures = None
        self.opened_mixers = {}
        self.opened_viewers = {}
    
    def close(self):
        if self.opened_mixers:
            self.ui.show_close_dialog()
        else:
            self.ui.close()
    
    def save_mixture_callback(self, mixture_dict, mixture_identifier):
        storage = ObjectStorage(self.library_db_file, self.library_table_name)
        storage.delete(mixture_identifier)
        storage.store(mixture_identifier, mixture_dict)
        self.close_window(mixture_identifier, self.opened_mixers)

        self.ui.refresh_mixture_list()
    
    def show_remove_dialog(self, mixture_identifier) -> None:
        ''' Asks the user if they are sure to remove the mixture from the Library. '''

        if not mixture_identifier:
            return
        else:
            self.ui.show_remove_dialog(callback=lambda ok_clicked, **kwargs:
                self.delete_mixture(kwargs[mix_id] if ok_clicked else None),
                callback_kwargs={'mix_id': mixture_identifier})

    def delete_mixture(self, mixture_identifier):
        if mixture_identifier is not None:
            ObjectStorage(self.library_db_file, self.library_table_name).delete(mixture_identifier)
        
        if mixture_identifier in self.opened_mixers:
            self.close_window(mixture_identifier, self.opened_mixers)
        if mixture_identifier in self.opened_viewers:
            self.close_window(mixture_identifier, self.opened_viewers)
        
        self.ui.refresh_mixture_list()
    
    def duplicate_mixture(self, mixture_identifier):
        storage = ObjectStorage(self.library_db_file, self.library_table_name)
        mixture_dict = self.mixtures[mixture_identifier]
        mixture_dict['name'] = 'Copy of {}'.format(mixture_dict['name'])
        storage.store(str(uuid.uuid4()), mixture_dict)

        self.ui.refresh_mixture_list()
    
    def close_window(self, window_key, opened_windows_dict):
        # TODO: Replace with .ui.close() when Mixer's UI is decoupled as well
        opened_windows_dict[window_key].toplevel.destroy()
        del opened_windows_dict[window_key]
    
    def open_mixture(self, mixture_identifier, create_new=False):
        if mixture_identifier in self.mixtures or create_new:
            if mixture_identifier not in self.opened_mixers:
                self.opened_mixers[mixture_identifier] = self.mixer(
                    parent=self.toplevel, # TODO: Replace with just self once Mixer is decoupled
                    save_callback=self.save_mixture_callback,
                    save_callback_args=[mixture_identifier],
                    discard_callback=self.close_window,
                    discard_callback_args=[mixture_identifier, self.opened_mixers])
                if not create_new:  # Load existing
                    self.opened_mixers[mixture_identifier].load(
                        copy.deepcopy(self.mixtures[mixture_identifier]))
                
                # TODO: Replace with .ui.on_close_callback() once Mixer is decoupled
                self.opened_mixers[mixture_identifier].toplevel.protocol('WM_DELETE_WINDOW',
                    self.opened_mixers[mixture_identifier].show_discard_dialog)
                
                if mixture_identifier in self.opened_viewers:
                    self.close_window(mixture_identifier, self.opened_viewers)
                    self.opened_mixers[mixture_identifier].show_bottle_viewer()
            else:
                # TODO: Replace with .ui.bring_forward() once Mixer is decoupled
                self.opened_mixers[mixture_identifier].toplevel.deiconify()
    
    # TODO: Continue decoupling HERE ---
    
    def view_bottle(self, mixture_identifier):
        if mixture_identifier not in self.opened_mixers:
            if mixture_identifier in self.mixtures:
                if mixture_identifier not in self.opened_viewers:
                    viewer = self.viewer(self.toplevel)
                    mixture = copy.deepcopy(self.mixtures[mixture_identifier])
                    viewer.set_name(mixture['name'])
                    viewer.set_bottle_size(mixture['bottle_vol'])
                    viewer.set_ingredients(mixture['ingredients'])
                    viewer.set_notes(mixture['notes'])
                    self.opened_viewers[mixture_identifier] = viewer
                    self.opened_viewers[mixture_identifier].toplevel.protocol('WM_DELETE_WINDOW',
                        lambda: self.close_window(mixture_identifier, self.opened_viewers))
                else:
                    self.opened_viewers[mixture_identifier].toplevel.deiconify()
        else:
            self.opened_mixers[mixture_identifier].show_bottle_viewer()
    
    def open_wrapper(self, event):
        self.open_mixture(self.treeview.focus(), False)

        # Return 'break' to not propagate the event to other bindings
        # This prevents expanding the item on double-click
        return 'break'
    
    def reload_treeview(self) -> None:
        self.mixtures = ObjectStorage(self.library_db_file, self.library_table_name).get_all()
        self.treeview.delete(*self.treeview.get_children())

        for mixture_identifier in self.mixtures:
            mixture = fludo.Mixture(*self.mixtures[mixture_identifier]['ingredients'])
            mx_id = self.treeview.insert('', tk.END, id=mixture_identifier,
                text=self.mixtures[mixture_identifier]['name'],
                values=(
                    '{} / {}'.format(int(mixture.pg), int(mixture.vg)),
                    '{} mg'.format(round_digits(mixture.nic, 1)),
                    '{} ml'.format(round_digits(mixture.ml, 1))))
            for liquid in self.mixtures[mixture_identifier]['ingredients']:
                self.treeview.insert(mx_id, tk.END, text=liquid.name, tags=('ingredient'),
                    values=(
                        '{} / {}'.format(int(liquid.pg), int(liquid.vg)),
                        '{} mg'.format(round_digits(liquid.nic, 1)),
                        '{} ml'.format(round_digits(liquid.ml, 1))))
