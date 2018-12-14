#!/usr/bin/env python3

import sys
import sqlite3

import tkinter as tk

from fludo import Liquid

from mixer import MixerToplevel

ingredients = [
    Liquid(ml=42.5, name='Base', pg=50, vg=50),
    Liquid(ml=2.5, name='NicBase', nic=20, pg=50, vg=50),
    Liquid(ml=5, name='Banana', pg=100, vg=0)
]


if __name__ == '__main__':
    tk_root = tk.Tk()
    tk_root.title('Fludo')

    # TODO Create main window with recipe list

    mixer = MixerToplevel(tk_root)
    mixer.load_mixture(ingredients, 50, fill_toggled_row_index=0)

    tk_root.mainloop()
