#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk

import fludo

from common import center_toplevel, round_digits
from storage import ObjectStorage


class Library:
    def __init__(self, parent: tk.Widget=None, library_db_file: str='library.db',
        library_table_name: str='recipes'):
        if parent is None:
            # assume that we need to be Tk root
            self.parent = None
            self.toplevel = tk.Tk()
            self.root = self.toplevel.nametowidget('.')
        else:
            self.parent = parent
            self.toplevel = tk.Toplevel(self.parent)
            self.root = self.toplevel.nametowidget('.')
        
        self.toplevel.withdraw()
        
        self.library_db_file = library_db_file
        self.library_table_name = library_table_name
        
        self.toplevel.title('Fludo | Library')
        self.toplevel.iconbitmap('icon.ico')
        self.toplevel.resizable(False, False)

        self.frame = ttk.Frame(self.toplevel)
        self.frame.grid()
        self.treeview_frame = ttk.Frame(self.frame)
        self.treeview_frame.grid_columnconfigure(0, minsize=500)
        self.treeview_frame.grid_rowconfigure(0, minsize=200)
        self.treeview_frame.grid()

        self.treeview = ttk.Treeview(self.treeview_frame, selectmode='browse')
        self.treeview.configure(columns=('pg', 'vg', 'nic', 'ml'))
        self.treeview.column('#0', width=250, anchor=tk.W)
        self.treeview.column('pg', width=50, anchor=tk.CENTER)
        self.treeview.column('vg', width=50, anchor=tk.CENTER)
        self.treeview.column('nic', width=80, anchor=tk.CENTER)
        self.treeview.column('ml', width=70, anchor=tk.CENTER)
        self.treeview.heading('#0', text='Name')
        self.treeview.heading('pg', text='PG %')
        self.treeview.heading('vg', text='VG %')
        self.treeview.heading('nic', text='Nic. (mg/ml)')
        self.treeview.heading('ml', text='Vol. (ml)')
        self.treeview.tag_configure('ingredient', background='#E4EBF7')
        self.treeview_vscroll = ttk.Scrollbar(self.treeview_frame, orient=tk.VERTICAL,
            command=self.treeview.yview)
        self.treeview.configure(yscrollcommand=self.treeview_vscroll.set)
        self.treeview.grid(row=0, column=0)
        self.treeview_vscroll.grid(row=0, column=1, sticky=tk.N+tk.S)

        self.mixtures = None
        self.reload_tree()

        center_toplevel(self.toplevel)
    
    def reload_tree(self) -> None:
        self.mixtures = ObjectStorage(self.library_db_file, self.library_table_name).get_all()

        for mixture_key in self.mixtures:
            mixture = fludo.Mixture(*self.mixtures[mixture_key]['ingredients'])
            mx_id = self.treeview.insert('', tk.END, text=self.mixtures[mixture_key]['name'],
                values=(
                    int(mixture.pg),
                    int(mixture.vg),
                    round_digits(mixture.nic, 1),
                    round_digits(mixture.ml, 1)))
            for liquid in self.mixtures[mixture_key]['ingredients']:
                self.treeview.insert(mx_id, tk.END, text=liquid.name, tags=('ingredient'),
                    values=(
                        int(liquid.pg),
                        int(liquid.vg),
                        round_digits(liquid.nic, 1),
                        round_digits(liquid.ml, 1)))
