#!/usr/bin/env python3
import time
import requests
import logging

class EZOAPI(object):

    def __init__(self, apikey: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": apikey})

    def get_users(self) -> dict:
        r = self._session.get("https://luna.marcsello.com/ezotv/api/authme")
        logging.debug(r.content.decode())
        r.raise_for_status()

        return r.json()

    def delete_user(self, uid: int) -> None:
        r = self._session.delete(f"https://luna.marcsello.com/ezotv/api/authme/{uid}")
        logging.debug(r.content.decode())
        r.raise_for_status()

    def create_user(self, uid: int, realname: str, password: str, salt: str) -> dict:
        userdata = {
            "id": uid,
            "username": realname.lower(),
            "realname": realname,
            "password": password,
            "salt": salt,
            "regdate": int(time.time())
        }

        r = self._session.post("https://luna.marcsello.com/ezotv/api/authme", json=userdata)
        logging.debug(r.content.decode())
        r.raise_for_status()

        return r.json()

    def update_password(self, uid: int, password: str, salt: str):
        update_content = {
            "password": password,
            "salt": salt
        }

        r = self._session.patch(f"https://luna.marcsello.com/ezotv/api/authme/{uid}", json=update_content)
        logging.debug(r.content.decode())
        r.raise_for_status()

        return r.json()

    def update_name(self, uid: int, realname: str):
        update_content = {
            "username": realname.lower(),
            "realname": realname,
        }

        r = self._session.patch(f"https://luna.marcsello.com/ezotv/api/authme/{uid}", json=update_content)
        logging.debug(r.content.decode())
        r.raise_for_status()

        return r.json()
