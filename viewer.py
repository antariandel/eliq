import tkinter as tk
from tkinter import ttk

import platform
from typing import List

from fludo import Liquid, Mixture

from images import icons, graphics
from common import round_digits


class BottleViewer:
    def __init__(self, parent: tk.Widget = None):
        if parent is None:
            # assume that we need to be Tk root
            self.parent = None
            self.toplevel = tk.Tk()
        else:
            self.parent = parent
            self.toplevel = tk.Toplevel(self.parent)
        self.root = self.toplevel.nametowidget('.')

        self.toplevel.withdraw()

        self.toplevel.title('Eliq | Bottle')
        self.toplevel.iconbitmap(icons['titlebar'])
        self.toplevel.minsize(660, 500)
        self.toplevel.resizable(False, True)
        self.toplevel.grid_rowconfigure(0, weight=1)
        self.toplevel.configure(background='white')

        self.frame = tk.Frame(self.toplevel)
        self.frame.grid_rowconfigure(0, weight=1)
        self.frame.grid(row=0, column=0, sticky=tk.EW + tk.NS)
        self.frame.configure(background='white')

        self.scrollbar = ttk.Scrollbar(self.frame, orient=tk.VERTICAL)
        self.scrollbar.grid(row=0, column=1, sticky=tk.NS)

        self.canvas = tk.Canvas(self.frame, width=660, height=500,
            yscrollcommand=self.scrollbar.set, borderwidth=0, highlightthickness=0)
        self.canvas.grid(row=0, column=0, padx=10, sticky=tk.EW + tk.NS)
        self.canvas.configure(background='white')

        self.scrollbar.config(command=self.canvas.yview)

        self.ingredients = []
        self.ingredient_rectangles = []
        self.bottle_size = 100
        self.notes = ''
        self.name = ''

        self.redraw()
        self.toplevel.deiconify()

        def _bound_to_mousewheel(event):
            if platform.system() != 'Linux':
                self.canvas.bind_all('<MouseWheel>', _on_mousewheel)
            else:
                self.canvas.bind_all('<Button-4>', _on_mousewheel)
                self.canvas.bind_all('<Button-5>', _on_mousewheel)
        self.canvas.bind('<Enter>', _bound_to_mousewheel)

        def _unbound_to_mousewheel(event):
            if platform.system() != 'Linux':
                self.canvas.unbind_all('<MouseWheel>')
            else:
                self.canvas.bind_all('<Button-4>', _on_mousewheel)
                self.canvas.bind_all('<Button-5>', _on_mousewheel)
        self.canvas.bind('<Leave>', _unbound_to_mousewheel)

        def _on_mousewheel(event):
            if platform.system() != 'Darwin':
                self.canvas.yview_scroll(int(-1 * (event.delta / 120)), 'units')
            else:
                self.canvas.yview_scroll(int(-1 * event.delta), 'units')
    
    def set_name(self, name):
        self.name = name
        self.toplevel.title('Eliq | Bottle of {}'.format(name))
        self.redraw()
    
    def set_notes(self, notes):
        self.notes = notes
        self.redraw()
    
    def set_bottle_size(self, volume):
        self.bottle_size = volume
        self.redraw()
    
    def set_ingredients(self, ingredients: List[Liquid] = []):
        self.ingredients = ingredients
        self.ingredients.sort(key=lambda liquid: liquid.ml, reverse=False)
        self.redraw()
    
    def redraw(self):
        self.canvas.delete(tk.ALL)

        # Draw Mixture name
        self.canvas.create_text((330, 5), font=('Calibri', 18), anchor=tk.N, text=self.name)

        # Draw ingredients
        bottom_left_position = (57, 460)
        width = 96

        self.ingredient_rectangles = []

        # Create rectangles
        for ingredient in self.ingredients:  # pylint: disable=W0612
            self.ingredient_rectangles.append(self.canvas.create_rectangle(
                bottom_left_position,
                (bottom_left_position[0] + width, bottom_left_position[1]),
                outline='black'
            ))
        
        # Resize rectangles
        increment = 0
        bottle_line_heights = []
        for index, rectangle in enumerate(self.ingredient_rectangles[::-1]):
            x0, y0, x1, y1 = self.canvas.coords(rectangle)
            increment = int(increment + (self.ingredients[index].ml / self.bottle_size) * 319)
            y1 = y0 - increment
            self.canvas.coords(rectangle, (x0, y0, x1, y1))
            
            fill_color = '#%02x%02x%02x' % (
                int(180 - 80 * (self.ingredients[index].pg + self.ingredients[index].vg) / 100 +
                    50 * (1 if self.ingredients[index].nic else 0)),
                int(240 - self.ingredients[index].pg -
                    110 * (1 if self.ingredients[index].nic else 0)),
                int(240 - self.ingredients[index].vg -
                    110 * (1 if self.ingredients[index].nic else 0))
            )

            self.canvas.itemconfig(rectangle,
                fill=fill_color,)
            
            # Draw line
            ingr_bottom = y1 + (self.ingredients[index].ml / self.bottle_size) * 319
            ingr_top = y1
            line_y = (ingr_bottom + ingr_top) / 2
            bottle_line_heights.append(line_y)

            self.canvas.create_line((160, line_y, 165, line_y))
        
        # Draw the bottle
        if 'bottle' not in dir(self):
            self.bottle_image = tk.PhotoImage(file=graphics['bottle'])
        self.canvas.create_image((80, 462), image=self.bottle_image, anchor=tk.S)
        
        # Draw ingredient names
        ingredient_line_heights = []
        for index, liquid in enumerate(self.ingredients[::-1]):
            self.canvas.create_text((260, 60 + 45 * index), font=('Calibri', 13), anchor=tk.W,
                text='{}ml'.format(liquid.ml))
            self.canvas.create_text((330, 60 + 45 * index), font=('Calibri', 12), anchor=tk.W,
                text='{}\n{}% PG / {}% VG, {} mg/ml'.format(
                    liquid.name,
                    liquid.pg,
                    liquid.vg,
                    liquid.nic))
            
            # Draw line
            line_y = 60 + 45 * index
            ingredient_line_heights.append(line_y)

            self.canvas.create_line((250, line_y, 255, line_y))
        
        # Draw line connectors
        for index, bottle_line_y in enumerate(bottle_line_heights[::-1]):
            self.canvas.create_line(165, bottle_line_y, 250, ingredient_line_heights[index])
        
        # Draw bottle size
        self.canvas.create_text((107, 470), font=('Calibri', 10), anchor=tk.CENTER,
            text='{} ml bottle'.format(self.bottle_size))
        
        # Draw mixture properties
        mixture = Mixture(*self.ingredients)
        self.canvas.create_text((106, 180), font=('Calibri', 12, 'bold'), anchor=tk.N,
            justify=tk.CENTER, text='{} ml'.format(round_digits(mixture.ml, 1)))
        self.canvas.create_text((87, 218), font=('Calibri', 12, 'bold'), anchor=tk.N,
            justify=tk.CENTER, text='{}%'.format(int(mixture.pg)))
        self.canvas.create_text((127, 218), font=('Calibri', 12, 'bold'), anchor=tk.N,
            justify=tk.CENTER, text='{}%'.format(int(mixture.vg)))
        self.canvas.create_text((106, 241), font=('Calibri', 14, 'bold'), anchor=tk.N,
            justify=tk.CENTER, text='{}'.format(round_digits(mixture.nic, 1)))
        
        bottom = 60 + 45 * len(self.ingredients)

        # Draw notes:
        if self.notes:
            self.canvas.create_line((260, bottom - 8, 660, bottom - 8))
            notes = self.canvas.create_text((260, bottom), font=('Calibri', 12), anchor=tk.NW,
                justify=tk.LEFT, width=400, text=self.notes)

            x0, y0, x1, y1 = self.canvas.bbox(notes)
            bottom += y1 - y0 + 10

        min_bottom = 450
        
        self.canvas.configure(scrollregion=(0, 0, 0, min_bottom if bottom < min_bottom else bottom))
