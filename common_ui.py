import tkinter as tk
from tkinter import ttk


class CommonUI:
    @staticmethod
    def create_toplevel(parent):
        if parent is None:
            # assume that we need to be Tk root
            toplevel = tk.Tk()
        else:
            toplevel = tk.Toplevel(self.parent)
        root = self.toplevel.nametowidget('.')
        return (root, parent, toplevel)