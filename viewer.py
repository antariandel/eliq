import tkinter as tk
from random import randint
from typing import List

from fludo import Liquid

from images import icons, set_icon, graphics

class BottleViewer:
    def __init__(self, parent: tk.Widget=None, bottle_size=100):
        if parent is None:
            # assume that we need to be Tk root
            self.parent = None
            self.toplevel = tk.Tk()
        else:
            self.parent = parent
            self.toplevel = tk.Toplevel(self.parent)
        self.root = self.toplevel.nametowidget('.')

        self.canvas = tk.Canvas(self.toplevel, width=600, height=650)
        self.canvas.grid(row=0, column=0, padx=10, pady=10, sticky=tk.EW + tk.NS)

        self.ingredients = []
        self.ingredient_rectangles = []
        self.bottle_size = bottle_size

        self.redraw()

        self.toplevel.bind('<Return>', self.test_randomize) # For testing
    
    def test_randomize(self, *args):
        self.bottle_size = 300
        ingredients = [Liquid(ml=999)]
        names = [
            'Funky Aroma',
            'Funkety Funk',
            'Punk 77',
            'Aro Maro',
            'Base 56',
            'Route 69',
            'Awesomest Liquid',
            'Nico Boost 2000',
            'Eco Nico',
            'Mix THIS',
            'Flavour Bester',
            'Basis Evo',
            'The Base',
            'Basey Nicey',
            'Bestest',
            'Friend Zone',
        ]

        while sum([liquid.ml for liquid in ingredients]) > self.bottle_size:
            ingredients = []
            for count in range(20): #pylint: disable=W0612
                ingredients.append(Liquid(
                    ml=randint(10, 20),
                    nic=5 if randint(0, 5) == 0 else 0,
                    pg=randint(0, 100),
                    name=names[randint(0, 15)]
                ))
        self.set_ingredients(ingredients)
        self.redraw()
    
    def set_ingredients(self, ingredients: List[Liquid]=[]):
        self.ingredients = ingredients
        self.ingredients.sort(key=lambda liquid: liquid.ml, reverse=False)
    
    def redraw(self):
        self.canvas.delete(tk.ALL)
    
        # Draw ingredients
        bottom_left_position = (15, 435)
        width = 94

        self.ingredient_rectangles = []

        # Create rectangles
        for ingredient in self.ingredients: #pylint: disable=W0612
            self.ingredient_rectangles.append(self.canvas.create_rectangle(
                bottom_left_position,
                (bottom_left_position[0] + width, bottom_left_position[1]),
                outline='black'
            ))
        
        # Resize rectangles
        increment = 0
        for index, rectangle in enumerate(self.ingredient_rectangles[::-1]):
            x0, y0, x1, y1 = self.canvas.coords(rectangle)
            increment = int(increment + (self.ingredients[index].ml / self.bottle_size) * 319)
            y1 = y0 - increment
            self.canvas.coords(rectangle, (x0, y0, x1, y1))
            
            fill_color = '#%02x%02x%02x' % (
                int((self.ingredients[index].pg + self.ingredients[index].vg)/4) +
                    200*(1 if self.ingredients[index].nic > 0 else 0),
                int(100 + (self.ingredients[index].pg*2)/1.5),
                int(100 + (self.ingredients[index].pg+self.ingredients[index].vg)/1.5)
            )

            self.canvas.itemconfig(rectangle,
                fill=fill_color,)
        
        # Draw the bottle
        if 'bottle' not in dir(self):
            self.bottle_image = tk.PhotoImage(file=graphics['bottle'])
        self.canvas.create_image((60, 230), image=self.bottle_image)
        
        # Draw ingredient names
        if len(self.ingredients) <= 10:
            self.canvas.create_text((170, 20), font=('Calibri', 12), anchor=tk.NW,
                text='\n\n'.join(['{}\n{}PG / {}VG, {} mg/ml'.format(liquid.name, liquid.pg, liquid.vg, liquid.nic) for liquid in self.ingredients[::-1]]))
        else:
            self.canvas.create_text((170, 20), font=('Calibri', 12), anchor=tk.NW,
                text='\n\n'.join(['{}, {}PG / {}VG, {} mg/ml'.format(liquid.name, liquid.pg, liquid.vg, liquid.nic) for liquid in self.ingredients[::-1]]))


