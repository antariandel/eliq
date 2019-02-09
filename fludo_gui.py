#!/usr/bin/env python3

import sys
import sqlite3

import tkinter as tk

from fludo import Liquid

from mixer import Mixer
from library import Library
from viewer import MixtureViewer
from storage import ObjectStorage


if __name__ == '__main__':
    app = MixtureViewer()
    app.root.mainloop()
