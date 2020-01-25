#!/usr/bin/env python3
import requests


class EZOTV(object):

    def __init__(self, apikey: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": apikey})

    def get_users(self) -> dict:
        r = self._session.get("https://ezotv.marcsello.com/api/user?approvedonly&withpassword")
        r.raise_for_status()

        return r.json()

    def set_sync(self, uid: int) -> dict:
        r = self._session.patch(f"https://ezotv.marcsello.com/api/user/{uid}", data={"in_sync": True})
        r.raise_for_status()

        return r.json()

