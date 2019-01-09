import time

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
        self.toplevel.rowconfigure(0, weight=1)
        self.toplevel.columnconfigure(0, weight=1)
        
        self.library_db_file = library_db_file
        self.library_table_name = library_table_name
        
        self.toplevel.title('Fludo | Library')
        self.toplevel.iconbitmap('icon.ico')
        self.toplevel.resizable(True, True)
        self.toplevel.minsize(530, 200)

        self.treeview_frame = ttk.Frame(self.toplevel, borderwidth=5, relief=tk.RAISED)
        self.treeview_frame.columnconfigure(0, weight=1)
        self.treeview_frame.rowconfigure(0, weight=1)
        self.treeview_frame.grid(column=0, row=0, sticky=tk.EW+tk.NS)

        self.treeview = ttk.Treeview(self.treeview_frame, selectmode='browse')
        self.treeview.configure(columns=('pg', 'vg', 'nic', 'ml'))
        self.treeview.column('#0', minwidth=250, anchor=tk.W)
        self.treeview.column('pg', minwidth=50, width=50, anchor=tk.CENTER)
        self.treeview.column('vg', minwidth=50, width=50, anchor=tk.CENTER)
        self.treeview.column('nic', minwidth=80, width=80, anchor=tk.CENTER)
        self.treeview.column('ml', minwidth=70, width=70, anchor=tk.CENTER)
        self.treeview.heading('#0', text='Name')
        self.treeview.heading('pg', text='PG %')
        self.treeview.heading('vg', text='VG %')
        self.treeview.heading('nic', text='Nic. (mg/ml)')
        self.treeview.heading('ml', text='Vol. (ml)')
        self.treeview.tag_configure('ingredient', background='#E4EBF7')
        self.treeview.tag_configure('edit', background='green')
        self.treeview_vscroll = ttk.Scrollbar(self.treeview_frame, orient=tk.VERTICAL,
            command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.treeview_vscroll.set)
        self.treeview.grid(row=0, column=0, sticky=tk.EW+tk.NS)
        self.treeview_vscroll.grid(row=0, column=1, sticky=tk.NS)
        self.treeview.bind("<Button-3>", self.open_context_menu)
        self.treeview.bind('<Double-1>', self.open_mixer)

        self.treeview_menu = tk.Menu(self.toplevel, tearoff=0)
        self.treeview_menu.add_command(label='Edit', command=lambda: print('Edit'))

        self.mixtures = None
        self.reload_tree()

        center_toplevel(self.toplevel)
    
    def open_mixer(self, event):
        item = self.treeview.identify('item', event.x, event.y)
        
        if item:
            Mixer(self.toplevel).load(self.mixtures[item])
        
        # Return 'break' to not propagate the event to other bindings
        # This prevents expanding the item on double-click
        return 'break'

    def open_context_menu(self, event):
        item = self.treeview.identify_row(event.y)

        if item:
            self.treeview.selection_set(item)
            self.treeview_menu.post(event.x_root, event.y_root)
    
    def reload_tree(self) -> None:
        self.mixtures = ObjectStorage(self.library_db_file, self.library_table_name).get_all()

        for mixture_key in self.mixtures:
            mixture = fludo.Mixture(*self.mixtures[mixture_key]['ingredients'])
            mx_id = self.treeview.insert('', tk.END, id=mixture_key,
                text=self.mixtures[mixture_key]['name'],
                values=(
                    int(mixture.pg),
                    int(mixture.vg),
                    round_digits(mixture.nic, 1),
                    round_digits(mixture.ml, 1), 'Edit', 'Del.'))
            for liquid in self.mixtures[mixture_key]['ingredients']:
                self.treeview.insert(mx_id, tk.END, text=liquid.name, tags=('ingredient'),
                    values=(
                        int(liquid.pg),
                        int(liquid.vg),
                        round_digits(liquid.nic, 1),
                        round_digits(liquid.ml, 1)))
