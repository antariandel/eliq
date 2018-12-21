#!/usr/bin/env python

import pickle
import sqlite3
from typing import Any


class ObjectStorage:
    '''
    Simple class that stores pickled python objects as tags in an sqlite database table.
    It can retrieve the stored objects by their tags as an unpickled python object.
    '''

    def __init__(self, sqlite_db_path: str, table_name: str):
        self.sqlite_db_path = sqlite_db_path
        self.table_name = ObjectStorage.scrub_table_name(table_name)

        self.sqlite_connection = sqlite3.connect(self.sqlite_db_path)
        self.sqlite_cursor = self.sqlite_connection.cursor()
        
        self.create_table()
    
    def __del__(self):
        self.sqlite_connection.close()
    
    @staticmethod
    def scrub_table_name(table_name):
        if ''.join( char for char in table_name if (char.isalnum() or char == '_' )) != table_name:
            raise Exception('Table name must only contain alphanumerics and underscore.')
        else:
            return table_name
    
    def create_table(self) -> None:
        self.sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS {0} (
            id INTEGER PRIMARY KEY ASC,
            tag TEXT UNIQUE,
            object BLOB
        )'''.format(ObjectStorage.scrub_table_name(self.table_name)))

    def store(self, tag: str, object_: Any) -> None:
        ''' Store one object in the sqlite table. '''

        self.sqlite_cursor.execute('''INSERT INTO {0} (tag, object) VALUES (?, ?)'''.format(
            ObjectStorage.scrub_table_name(self.table_name)),
            (tag, pickle.dumps(object_, pickle.HIGHEST_PROTOCOL)))
        self.sqlite_connection.commit()
    
    def get(self, tag: str) -> Any:
        self.sqlite_cursor.execute('SELECT id, tag, object FROM {0} WHERE tag=?'.format(
            ObjectStorage.scrub_table_name(self.table_name)), (tag, ))
        
        object_ = self.sqlite_cursor.fetchone()
        if object_:
            return pickle.loads(object_[2])
        else:
            return None
    
    def get_all(self) -> dict:
        self.sqlite_cursor.execute('SELECT id, tag, object FROM {0}'.format(
            ObjectStorage.scrub_table_name(self.table_name)))
        
        objects = dict()

        object_row = self.sqlite_cursor.fetchone()
        while object_row is not None:
            objects[object_row[1]] = pickle.loads(object_row[2])
            object_row = self.sqlite_cursor.fetchone()
        
        return objects
    
    def delete(self, tag: str) -> None:
        self.sqlite_cursor.execute('DELETE FROM {0} WHERE tag=?'.format(
            ObjectStorage.scrub_table_name(self.table_name)), (tag, ))
        self.sqlite_connection.commit()
    
    def delete_all(self) -> None:
        self.sqlite_cursor.execute('DROP TABLE IF EXISTS {0}'.format(
            ObjectStorage.scrub_table_name(self.table_name)))
        self.create_table()
