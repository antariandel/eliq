import uuid
import copy

import tkinter as tk
from tkinter import ttk

import fludo

from common import center_toplevel, round_digits, YesNoDialog
from storage import ObjectStorage
from mixer import Mixer
from viewer import BottleViewer
from images import icons, set_icon
from version import VERSION


class Library:
    def __init__(self, parent: tk.Widget = None, library_db_file: str = 'library.db',
                 library_table_name: str = 'recipes'):
        if parent is None:
            # assume that we need to be Tk root
            self.parent = None
            self.toplevel = tk.Tk()
        else:
            self.parent = parent
            self.toplevel = tk.Toplevel(self.parent)
        self.root = self.toplevel.nametowidget('.')
        
        self.toplevel.protocol('WM_DELETE_WINDOW', self.close)
        self.toplevel.withdraw()

        self.toplevel.rowconfigure(1, weight=1)
        self.toplevel.columnconfigure(0, weight=1)
        
        self.library_db_file = library_db_file
        self.library_table_name = library_table_name
        
        self.toplevel.title('Eliq {} | Library'.format(VERSION))
        self.toplevel.iconbitmap(icons['app-icon'])
        self.toplevel.minsize(0, 300)
        self.toplevel.resizable(False, True)

        self.button_frame = ttk.Frame(self.toplevel)
        self.button_frame.grid(row=0, column=0, sticky=tk.EW)

        self.create_button = ttk.Button(self.button_frame, text='Create New Mixture', width=20,
            command=lambda: self.open_mixture(str(uuid.uuid4()), create_new=True))
        set_icon(self.create_button, icons['plus'])
        self.create_button.grid(row=0, column=0)

        self.modify_button = ttk.Button(self.button_frame, text='Modify Selected', width=20,
            command=lambda: self.open_mixture(self.treeview.focus()))
        set_icon(self.modify_button, icons['edit'])
        self.modify_button.grid(row=0, column=1)

        self.destroy_button = ttk.Button(self.button_frame, text='Delete Selected', width=20,
            command=lambda: self.show_remove_dialog(self.treeview.focus()))
        set_icon(self.destroy_button, icons['trash-2'])
        self.destroy_button.grid(row=0, column=2)

        self.view_button = ttk.Button(self.button_frame, text='View Selected', width=20,
            command=lambda: self.view_bottle(self.treeview.focus()))
        set_icon(self.view_button, icons['bottle-icon'])
        self.view_button.grid(row=0, column=3)

        self.duplicate_button = ttk.Button(self.button_frame, text='Duplicate Selected', width=20,
            command=lambda: self.duplicate_mixture(self.treeview.focus()))
        set_icon(self.duplicate_button, icons['copy'])
        self.duplicate_button.grid(row=0, column=4)

        self.treeview_frame = ttk.Frame(self.toplevel, borderwidth=5, relief=tk.RAISED)
        self.treeview_frame.columnconfigure(0, weight=1)
        self.treeview_frame.rowconfigure(0, weight=1)
        self.treeview_frame.grid(column=0, row=1, sticky=tk.EW + tk.NS)

        style = ttk.Style()
        style.configure('mystyle.Treeview', highlightthickness=0, border=0, font=('Calibri', 11))
        style.configure('mystyle.Treeview.Heading', font=('Calibri', 11, 'bold'))
        style.layout('mystyle.Treeview', [('mystyle.Treeview.treearea', {'sticky': 'nswe'})])

        self.treeview = ttk.Treeview(self.treeview_frame, selectmode='browse',
            style='mystyle.Treeview')
        self.treeview.configure(columns=('pgvg', 'nic', 'ml'))
        self.treeview.column('#0', width=350, anchor=tk.W)
        self.treeview.column('pgvg', width=90, stretch=False, anchor=tk.CENTER)
        self.treeview.column('nic', width=90, stretch=False, anchor=tk.CENTER)
        self.treeview.column('ml', width=70, stretch=False, anchor=tk.CENTER)
        self.treeview.heading('#0', text='Mixture Name')
        self.treeview.heading('pgvg', text='PG / VG %')
        self.treeview.heading('nic', text='Nic. (mg/ml)')
        self.treeview.heading('ml', text='Amount')
        self.treeview.tag_configure('ingredient', background='#ededed')
        self.treeview_vscroll = ttk.Scrollbar(self.treeview_frame, orient=tk.VERTICAL,
            command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.treeview_vscroll.set)
        self.treeview.grid(row=0, column=0, sticky=tk.EW + tk.NS)
        self.treeview_vscroll.grid(row=0, column=1, sticky=tk.NS)
        self.treeview.bind('<Double-1>', self.open_wrapper)
        self.treeview.bind('<Return>', self.open_wrapper)
        self.treeview.bind('<Button-1>', self.inhibit_column_resize)
        self.treeview.bind('<Delete>', lambda event: self.show_remove_dialog(self.treeview.focus()))

        self.mixtures = None
        self.opened_mixers = {}
        self.opened_viewers = {}
        self.reload_treeview()

        self.close_dialog = None

        center_toplevel(self.toplevel)
    
    def close(self):
        def close_if_ok_clicked(ok_clicked):
            if ok_clicked:
                self.toplevel.destroy()
                
        if self.opened_mixers:
            if self.close_dialog is None:
                self.close_dialog = YesNoDialog(self.toplevel,
                    window_title='Are you sure?',
                    text='',
                    callback=close_if_ok_clicked,
                    destroy_on_close=False)
            self.close_dialog.label.configure(text=('You have mixers open.\n'
                                                    'Are you sure you wish to close\n'
                                                    'them all without saving?'))
            self.close_dialog.toplevel.deiconify()
        else:
            self.toplevel.destroy()
    
    def inhibit_column_resize(self, event):
        if self.treeview.identify_region(event.x, event.y) == 'separator':
            # Return 'break' to not propagate the event to other bindings
            return 'break'
    
    def save_mixture_callback(self, mixture_dict, mixture_identifier):
        storage = ObjectStorage(self.library_db_file, self.library_table_name)
        storage.delete(mixture_identifier)
        storage.store(mixture_identifier, mixture_dict)
        self.close_window(mixture_identifier, self.opened_mixers)
        self.reload_treeview()
    
    def show_remove_dialog(self, mixture_identifier) -> None:
        ''' Asks the user if they are sure to remove the mixture from the Library. '''

        if not mixture_identifier:
            return

        remove_dialog = YesNoDialog(self.toplevel,
            callback=lambda ok_clicked, mixture_identifier:
                self.delete_mixture(mixture_identifier if ok_clicked else None),
            mixture_identifier=mixture_identifier,
            window_title='Remove Ingredient',
            text='',
            destroy_on_close=False)
        remove_dialog.label.configure(
            text=('Are you sure you wish to remove\n'
                  '{}?').format(self.mixtures[mixture_identifier]['name']))
        remove_dialog.ok_button.focus()
        remove_dialog.toplevel.deiconify()

    def delete_mixture(self, mixture_identifier):
        if mixture_identifier is not None:
            ObjectStorage(self.library_db_file, self.library_table_name).delete(mixture_identifier)
            self.reload_treeview()
        if mixture_identifier in self.opened_mixers:
            self.close_window(mixture_identifier, self.opened_mixers)
        if mixture_identifier in self.opened_viewers:
            self.close_window(mixture_identifier, self.opened_viewers)
    
    def duplicate_mixture(self, mixture_identifier):
        storage = ObjectStorage(self.library_db_file, self.library_table_name)
        mixture_dict = self.mixtures[mixture_identifier]
        mixture_dict['name'] = 'Copy of {}'.format(mixture_dict['name'])
        storage.store(str(uuid.uuid4()), mixture_dict)
        self.reload_treeview()
    
    def close_window(self, window_key, opened_windows_dict):
        opened_windows_dict[window_key].toplevel.destroy()
        del opened_windows_dict[window_key]
    
    def open_mixture(self, mixture_identifier, create_new=False):
        if mixture_identifier in self.mixtures or create_new:
            if mixture_identifier not in self.opened_mixers:
                self.opened_mixers[mixture_identifier] = Mixer(self.toplevel,
                    save_callback=self.save_mixture_callback,
                    save_callback_args=[mixture_identifier],
                    discard_callback=self.close_window,
                    discard_callback_args=[mixture_identifier, self.opened_mixers])
                if not create_new:  # Load existing
                    self.opened_mixers[mixture_identifier].load(
                        copy.deepcopy(self.mixtures[mixture_identifier]))
                self.opened_mixers[mixture_identifier].toplevel.protocol('WM_DELETE_WINDOW',
                    self.opened_mixers[mixture_identifier].show_discard_dialog)
                if mixture_identifier in self.opened_viewers:
                    self.close_window(mixture_identifier, self.opened_viewers)
                    self.opened_mixers[mixture_identifier].show_bottle_viewer()
            else:
                self.opened_mixers[mixture_identifier].toplevel.deiconify()
    
    def view_bottle(self, mixture_identifier):
        if mixture_identifier not in self.opened_mixers:
            if mixture_identifier in self.mixtures:
                if mixture_identifier not in self.opened_viewers:
                    viewer = BottleViewer(self.toplevel)
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
