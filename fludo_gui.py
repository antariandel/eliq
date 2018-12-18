#!/usr/bin/env python3

import sys
import sqlite3

import tkinter as tk

from fludo import Liquid

from mixer import Mixer, MixerIngredientController

ingredients = {
    'ingredients': [
        Liquid(ml=42.5, name='Base', pg=50, vg=50),
        Liquid(ml=2.5, name='NicBase', nic=20, pg=50, vg=50),
        Liquid(ml=5, name='Aroma', pg=100, vg=0)
    ],
    'filler_idx': 0,
    'container_vol': 50
}


if __name__ == '__main__':
    tk_root = tk.Tk()
    tk_root.title('Fludo')

    # TODO Create main window with recipe list

    mixer = Mixer(tk_root)
    mixer.load_ingredients(ingredients)

    tk_root.mainloop()
