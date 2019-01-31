import pickle
import sqlite3
from typing import Any


class ObjectStorage:
    '''
    Simple class that stores pickled (serialized) python objects as in an sqlite database table.
    It can retrieve the stored objects by their tags directly as python objects.
    Objects are referenced with unique tags.
    '''

    def __init__(self, sqlite_db_path: str, table_name: str):
        self.sqlite_db_path = sqlite_db_path
        self.table_name = ObjectStorage._scrub_table_name(table_name)

        self.sqlite_connection = sqlite3.connect(self.sqlite_db_path)
        self.sqlite_cursor = self.sqlite_connection.cursor()
        
        self.create_table()
    
    def __del__(self):
        self.sqlite_connection.close()
    
    @staticmethod
    def _scrub_table_name(table_name: str):
        ''' Allows only alphanumerics and underscore in the storage table name. '''

        if ''.join( char for char in table_name if (char.isalnum() or char == '_' )) != table_name:
            raise Exception('Table name must only contain alphanumerics and underscore.')
        else:
            return table_name
    
    @staticmethod
    def _scrub_tag(tag: str):
        ''' Allows only alphanumerics, underscore and hyphen in tags. '''

        if ''.join( char for char in tag if (char.isalnum() or char == '_' or char == '-' )) != tag:
            raise Exception('Tags must only contain alphanumerics, underscore and hyphen.')
        else:
            return tag
    
    def create_table(self) -> None:
        ''' Initializes the storage table. '''

        self.sqlite_cursor.execute('''CREATE TABLE IF NOT EXISTS {0} (
            id INTEGER PRIMARY KEY ASC,
            tag TEXT UNIQUE,
            object BLOB
        )'''.format(ObjectStorage._scrub_table_name(self.table_name)))

    def store(self, tag: str, object_: Any) -> None:
        ''' Store one object in the sqlite table with a given tag. '''

        try:
            self.sqlite_cursor.execute('''INSERT INTO {0} (tag, object) VALUES (?, ?)'''.format(
                ObjectStorage._scrub_table_name(self.table_name)),
                (ObjectStorage._scrub_tag(tag), pickle.dumps(object_, pickle.HIGHEST_PROTOCOL)))
            self.sqlite_connection.commit()
        except sqlite3.IntegrityError:
            print('Object with tag <{0}> exists in the database! Tags must be unique.'.format(tag))
            raise
    
    def get(self, tag: str) -> Any:
        ''' Get one object from the sqlite table with a given tag. Return None if doesn't exist. '''

        self.sqlite_cursor.execute('SELECT id, tag, object FROM {0} WHERE tag=?'.format(
            ObjectStorage._scrub_table_name(self.table_name)), (tag, ))
        
        object_ = self.sqlite_cursor.fetchone()
        if object_:
            return pickle.loads(object_[2])
        else:
            return None
    
    def get_all(self) -> dict:
        ''' Return all stored objects in a dict with their tags as keys. '''

        self.sqlite_cursor.execute('SELECT id, tag, object FROM {0}'.format(
            ObjectStorage._scrub_table_name(self.table_name)))
        
        objects = dict()

        object_row = self.sqlite_cursor.fetchone()
        while object_row is not None:
            objects[object_row[1]] = pickle.loads(object_row[2])
            object_row = self.sqlite_cursor.fetchone()
        
        return objects
    
    def delete(self, tag: str) -> None:
        ''' Delete one object from storage with the given tag. '''

        self.sqlite_cursor.execute('DELETE FROM {0} WHERE tag=?'.format(
            ObjectStorage._scrub_table_name(self.table_name)), (tag, ))
        self.sqlite_connection.commit()
    
    def delete_all(self) -> None:
        ''' Purge storage of all objects. '''

        self.sqlite_cursor.execute('DROP TABLE IF EXISTS {0}'.format(
            ObjectStorage._scrub_table_name(self.table_name)))
        self.create_table()
