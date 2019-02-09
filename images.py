import os

import tkinter as tk

# This script is a quick and dirty way to load all icons and graphics from directories 

icon_directories = [
    'resources/feather',
    'resources/icons',
]

graphics_directories = [
    'resources/graphics'
]

def set_icon(widget, icon_path, compound=tk.LEFT):
    widget.image = tk.PhotoImage(file=icon_path)
    widget.configure(compound=compound, image=widget.image)

def load_images(directory_list):
    images = {}
    for directory in directory_list:
        for filename in os.listdir(directory):
            if '.png' in filename:
                images[filename.partition('.png')[0]] = os.path.join(directory, filename)
            if 'app-icon' in filename:
                images['app-icon'] = os.path.join(directory, filename)
    return images

icons = load_images(icon_directories)
graphics = load_images(graphics_directories)