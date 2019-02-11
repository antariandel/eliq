import os
import sys

import tkinter as tk

# This script is a quick and dirty way to load all icons and graphics from directories

icon_directories = [
    'res/feather',
    'res/icons',
]

graphics_directories = [
    'res/graphics'
]


def resource_path(relative_path):
    ''' Get absolute path to resource, works for dev and for PyInstaller '''
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS  # pylint: disable=no-member
    except Exception:
        base_path = os.path.abspath('.')

    return os.path.join(base_path, relative_path)


def set_icon(widget, icon_path, compound=tk.LEFT):
    widget.image = tk.PhotoImage(file=icon_path)
    widget.configure(compound=compound, image=widget.image)


def load_images(directory_list):
    images = {}
    for directory in directory_list:
        for filename in os.listdir(resource_path(directory)):
            if '.png' in filename:
                images[filename.partition('.png')[0]] = \
                    os.path.join(resource_path(directory), filename)
            if 'app-icon' in filename:
                images['app-icon'] = os.path.join(resource_path(directory), filename)
    return images


icons = load_images(icon_directories)
graphics = load_images(graphics_directories)
