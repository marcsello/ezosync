#!/usr/bin/env python3
import MySQLdb


class DB(object):

    def __init__(self, user: str, passwd: str, db: str, host: str = None, table: str = "authme"):

        if not host:
            self._dbc = MySQLdb.connect(
                user=user,
                passwd=passwd,
                db=db,
                unix_socket="/var/run/mysqld/mysqld.sock",
                connect_timeout=1
            )

        else:
            self._dbc = MySQLdb.connect(
                host=host,
                user=user,
                passwd=passwd,
                db=db,
                connect_timeout=1
            )

        self._table = table

    def get_current_users(self):
        cursor = self._dbc.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"SELECT id,username,realname,password,salt FROM {self._table}")  # Faszér' nem lehet tábla nevet escapelni

        return cursor.fetchall()

    def delete_user(self, id: int):
        cursor = self._dbc.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"DELETE FROM {self._table} WHERE id = %s", (id,))  # Faszér' nem lehet tábla nevet escapelni
        self._dbc.commit()

    def create_user(self, id: int, username: str, realname: str, password: str, salt: str):
        cursor = self._dbc.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"INSERT INTO {self._table} (id, username, realname, password, salt) VALUES(%s,%s,%s,%s,%s)", (id, username, realname, password, salt))  # Faszér' nem lehet tábla nevet escapelni
        self._dbc.commit()

    def update_password(self, id: int, password: str, salt: str):
        cursor = self._dbc.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(f"UPDATE {self._table} SET password = %s, salt = %s WHERE id = %s", (password, salt, id))  # Faszér' nem lehet tábla nevet escapelni
        self._dbc.commit()
