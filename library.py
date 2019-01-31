import time
import uuid

import tkinter as tk
from tkinter import ttk

import fludo

from common import center_toplevel, round_digits
from storage import ObjectStorage
from mixer import Mixer


class Library:
    def __init__(self, parent: tk.Widget=None, library_db_file: str='library.db',
        library_table_name: str='recipes'):
        if parent is None:
            # assume that we need to be Tk root
            self.parent = None
            self.toplevel = tk.Tk()
        else:
            self.parent = parent
            self.toplevel = tk.Toplevel(self.parent)
        self.root = self.toplevel.nametowidget('.')
        
        self.toplevel.withdraw()
        self.toplevel.rowconfigure(1, weight=1)
        self.toplevel.columnconfigure(0, weight=1)
        
        self.library_db_file = library_db_file
        self.library_table_name = library_table_name
        
        self.toplevel.title('Fludo | Library')
        self.toplevel.iconbitmap('icon.ico')
        self.toplevel.resizable(True, True)
        self.toplevel.minsize(530, 200)

        self.button_frame = ttk.Frame(self.toplevel)
        self.button_frame.grid(row=0, column=0, sticky=tk.EW)

        self.create_button = ttk.Button(self.button_frame, text='Create New Mixture', width=20,
            command=lambda: self.open_mixture(str(uuid.uuid4()), create_new=True))
        self.create_button.grid(row=0, column=0)

        self.modify_button = ttk.Button(self.button_frame, text='Modify Selected', width=20,
            command=lambda: self.open_mixture(self.treeview.focus()))
        self.modify_button.grid(row=0, column=1)

        self.delete_button = ttk.Button(self.button_frame, text='Delete Selected', width=20,
            command=lambda: self.delete_mixture(self.treeview.focus()))
        self.delete_button.grid(row=0, column=2)

        self.view_button = ttk.Button(self.button_frame, text='View Selected', width=20,
            state=tk.DISABLED)
        self.view_button.grid(row=0, column=3)

        self.duplicate_button = ttk.Button(self.button_frame, text='Duplicate Selected', width=20,
            state=tk.DISABLED)
        self.duplicate_button.grid(row=0, column=4)

        self.treeview_frame = ttk.Frame(self.toplevel, borderwidth=5, relief=tk.RAISED)
        self.treeview_frame.columnconfigure(0, weight=1)
        self.treeview_frame.rowconfigure(0, weight=1)
        self.treeview_frame.grid(column=0, row=1, sticky=tk.EW+tk.NS)

        self.treeview = ttk.Treeview(self.treeview_frame, selectmode='browse')
        self.treeview.configure(columns=('pgvg', 'nic', 'ml'))
        self.treeview.column('#0', width=400, anchor=tk.W)
        self.treeview.column('pgvg', width=100, stretch=False, anchor=tk.CENTER)
        self.treeview.column('nic',width=80, stretch=False, anchor=tk.CENTER)
        self.treeview.column('ml', width=70, stretch=False, anchor=tk.CENTER)
        self.treeview.heading('#0', text='Name')
        self.treeview.heading('pgvg', text='PG / VG %')
        self.treeview.heading('nic', text='Nic. (mg/ml)')
        self.treeview.heading('ml', text='Vol.')
        self.treeview.tag_configure('ingredient', background='#E4EBF7')
        self.treeview.tag_configure('edit', background='green')
        self.treeview_vscroll = ttk.Scrollbar(self.treeview_frame, orient=tk.VERTICAL,
            command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.treeview_vscroll.set)
        self.treeview.grid(row=0, column=0, sticky=tk.EW+tk.NS)
        self.treeview_vscroll.grid(row=0, column=1, sticky=tk.NS)
        self.treeview.bind('<Double-1>', self.doubleclick_wrapper)
        self.treeview.bind('<Button-1>', self.inhibit_column_resize)

        self.mixtures = None
        self.opened_mixers = {}
        self.reload_treeview()

        center_toplevel(self.toplevel)
    
    def inhibit_column_resize(self, event):
        if self.treeview.identify_region(event.x, event.y) == "separator":
            return "break"
    
    def doubleclick_wrapper(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        self.open_mixture(item, False)

        # Return 'break' to not propagate the event to other bindings
        # This prevents expanding the item on double-click
        return 'break'
    
    def save_mixture_callback(self, mixture_dump, mixture_identifier):
        storage = ObjectStorage(self.library_db_file, self.library_table_name)
        storage.delete(mixture_identifier)
        storage.store(mixture_identifier, mixture_dump)
        self.close_mixture(mixture_identifier)
        self.reload_treeview()
    
    def delete_mixture(self, mixture_identifier):
        ObjectStorage(self.library_db_file, self.library_table_name).delete(mixture_identifier)
        self.reload_treeview()
    
    def close_mixture(self, mixture_identifier):
        self.opened_mixers[mixture_identifier].toplevel.destroy()
        del self.opened_mixers[mixture_identifier]
    
    def open_mixture(self, mixture_identifier, create_new=False):
        if mixture_identifier in self.mixtures or create_new:
            if mixture_identifier not in self.opened_mixers:
                self.opened_mixers[mixture_identifier] = Mixer(self.toplevel,
                    save_callback=self.save_mixture_callback,
                    save_callback_args=[mixture_identifier],
                    discard_callback=self.close_mixture,
                    discard_callback_args=[mixture_identifier])
                if not create_new: # Load existing
                    self.opened_mixers[mixture_identifier].load(self.mixtures[mixture_identifier])
                self.opened_mixers[mixture_identifier].toplevel.protocol('WM_DELETE_WINDOW',
                    lambda: self.close_mixture(mixture_identifier))
            else:
                self.opened_mixers[mixture_identifier].toplevel.deiconify()
    
    def reload_treeview(self) -> None:
        self.mixtures = ObjectStorage(self.library_db_file, self.library_table_name).get_all()
        self.treeview.delete(*self.treeview.get_children())

        for mixture_key in self.mixtures:
            mixture = fludo.Mixture(*self.mixtures[mixture_key]['ingredients'])
            mx_id = self.treeview.insert('', tk.END, id=mixture_key,
                text=self.mixtures[mixture_key]['name'],
                values=(
                    '{} / {}'.format(int(mixture.pg), int(mixture.vg)),
                    '{} mg'.format(round_digits(mixture.nic, 1)),
                    '{} ml'.format(round_digits(mixture.ml, 1))))
            for liquid in self.mixtures[mixture_key]['ingredients']:
                self.treeview.insert(mx_id, tk.END, text=liquid.name, tags=('ingredient'),
                    values=(
                        '{} / {}'.format(int(liquid.pg), int(liquid.vg)),
                        '{} mg'.format(round_digits(liquid.nic, 1)),
                        '{} ml'.format(round_digits(liquid.ml, 1))))
