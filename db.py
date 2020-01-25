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
        cursor.execute("SELECT id,username,realname,password,salt FROM %s", (self._table,))

        return cursor.fetchall()
