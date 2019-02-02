#!/usr/bin/env python3

import sys
import sqlite3

import tkinter as tk

from fludo import Liquid

from mixer import Mixer
from library import Library
from storage import ObjectStorage


if __name__ == '__main__':
    # mixer = Mixer(parent=None, mixture_name='Unsaved Mixture')
    # mixer.load(ingredients)
    # mixer.root.mainloop()

    library = Library()
    library.root.mainloop()
