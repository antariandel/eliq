#!/usr/bin/env python3

import sys
import sqlite3

import tkinter as tk

from fludo import Liquid

from mixer import Mixer


ingredients = {
    'ingredients': [
        Liquid(ml=42.5, name='Base', pg=50, vg=50),
        Liquid(ml=2.5, name='NicBase', nic=20, pg=50, vg=50),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=42.5, name='Base', pg=50, vg=50),
        Liquid(ml=2.5, name='NicBase', nic=20, pg=50, vg=50),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
        Liquid(ml=5, name='Aroma', pg=100, vg=0),
    ],
    'filler_idx': 0,
    'container_vol': 200
}


if __name__ == '__main__':
    tk_root = tk.Tk()
    tk_root.title('Fludo')

    # Will open library here as main window instead of Mixer

    mixer = Mixer(tk_root, 'Unsaved Mixture')
    mixer.load_ingredients(ingredients)

    tk_root.mainloop()
