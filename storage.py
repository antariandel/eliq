#!/usr/bin/env python

import pickle
import sqlite3

import fludo


class LibraryStorage:
    def __init__(self, sqlite_db_path: str):
        self.sqlite_db_path = sqlite_db_path
        self.open_conn()
        
        self.sqlite_cursor.execute('CREATE TABLE IF NOT EXISTS mixture_list '
                                   '(id INTEGER PRIMARY KEY ASC, name TEXT, mixture BLOB)')
        
        self.sqlite_cursor.execute('SELECT id, name, mixture FROM mixture_list')

        self.mixtures_dict = {}

        mixture_list_row = self.sqlite_cursor.fetchone()

        while mixture_list_row is not None:
            loadable_ingredients_dict = pickle.loads(mixture_list_row[2])

            self.mixtures_dict[mixture_list_row[0]] = {
                'name': mixture_list_row[1],
                'loadable_ingredients': loadable_ingredients_dict,
                'mixture': fludo.Mixture(*[liquid
                    for liquid in loadable_ingredients_dict['ingrediets']])
            }

            mixture_list_row = self.sqlite_cursor.fetchone()
    
    def open_conn(self) -> None:
        self.sqlite_connection = sqlite3.connect(self.sqlite_db_path)
        self.sqlite_cursor = self.sqlite_connection.cursor()
    
    def close_conn(self) -> None:
        self.sqlite_connection.close()
        
    def get_library(self) -> dict:
        return self.mixtures_dict
