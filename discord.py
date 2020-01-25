#!/usr/bin/env python3
import requests


class Discord(object):

    def __init__(self, apikey: str, guild: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bot {apikey}"})
        self._guild = guild

    def get_guild_member_ids(self) -> dict:
        r = self._session.get(f"https://discordapp.com/api/guilds/{self._guild}/members?limit=1000")  # This might be a problem for guilds larger than 1000.... discord's default is 1
        r.raise_for_status()

        discord_guild_members = r.json()
        discord_guild_member_ids = [discord_guild_member['user']['id'] for discord_guild_member in discord_guild_members]

        return discord_guild_member_ids
