import os

import tkinter as tk

def set_icon(widget, icon_path, compound=tk.LEFT):
    widget.image = tk.PhotoImage(file=icon_path)
    widget.configure(compound=compound, image=widget.image)

icon_directories = [
    'feather-icons',
    'fludo-icons'
]

icons = {}

for directory in icon_directories:
    for icon_file in os.listdir(directory):
        if '.png' in icon_file:
            icons[icon_file.partition('.png')[0]] = os.path.join(directory, icon_file)
        if 'app-icon' in icon_file:
            icons['app-icon'] = os.path.join(directory, icon_file)