#!/usr/bin/env python3

import sys
import sqlite3

import tkinter as tk

from fludo import Liquid

from mixer import Mixer
from library import Library
from storage import ObjectStorage


ingredients = {
    'ingredients': [
        Liquid(ml=42.5, name='Base', pg=50, vg=50),
        Liquid(ml=2.5, name='NicBase', nic=20, pg=50, vg=50),
        Liquid(ml=5, name='Aroma', pg=100, vg=0)
    ],
    'filler_idx': 0,
    'container_vol': 50,
    'name': 'My Awesome Mixture'
}


if __name__ == '__main__':
    # mixer = Mixer(parent=None, mixture_name='Unsaved Mixture')
    # mixer.load(ingredients)
    # mixer.root.mainloop()

    if not ObjectStorage('library.db', 'recipes').get_all():
        ObjectStorage('library.db', 'recipes').store('My_Awesome_Mixture_%s' % id(ingredients), ingredients)

    library = Library(parent=None)
    library.root.mainloop()
