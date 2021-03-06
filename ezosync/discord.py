#!/usr/bin/env python3
import requests


class Discord(object):

    def __init__(self, apikey: str, guild: str, admin_chat: str):
        self._session = requests.Session()
        self._session.headers.update({"Authorization": f"Bot {apikey}"})
        self._guild = guild
        self._admin_chat = admin_chat

    def get_guild_member_ids(self) -> list:
        # This might be a problem for guilds larger than 1000.... discord's default is 1
        r = self._session.get(f"https://discordapp.com/api/guilds/{self._guild}/members?limit=1000")
        r.raise_for_status()

        discord_guild_members = r.json()
        discord_guild_member_ids = \
            [discord_guild_member['user']['id'] for discord_guild_member in discord_guild_members]

        return discord_guild_member_ids

    def post_log(self, msg: str):
        data = {
            "content": msg,
            "tts": False
        }

        r = self._session.post(f"https://discordapp.com/api/channels/{self._admin_chat}/messages", json=data)
        r.raise_for_status()
