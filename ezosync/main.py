#!/usr/bin/env python3
import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

import logging

from discord import Discord
from ezotv_web import EZOTVWeb
from ezoapi import EZOAPI


class Config:
    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    EZOTV_WEB_APIKEY = os.environ['EZOTV_WEB_APIKEY']
    EZOAPI_APIKEY = os.environ['EZOAPI_APIKEY']
    DISCORD_BOTKEY = os.environ['DISCORD_BOTKEY']
    DISCORD_GUILD = os.environ['DISCORD_GUILD']
    DISCORD_ADMINCHAT = os.environ['DISCORD_ADMINCHAT']
    IGNORE_MEMBERS = os.environ.get("IGNORE_MEMBERS", "329622641713348618").split(',')  # Ignore EZO-BOT


def main():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s", filename='')

    if Config.SENTRY_DSN:
        sentry_logging = LoggingIntegration(
            level=logging.DEBUG,
            event_level=logging.ERROR  # Send errors as events
        )
        sentry_sdk.init(
            dsn=Config.SENTRY_DSN,
            integrations=[sentry_logging],
            send_default_pii=True
        )

    logging.info("Starting EZO-SYNC...")
    # Prepare some stuff
    logging.debug("Preparing connections...")
    ezotv = EZOTVWeb(Config.EZOTV_WEB_APIKEY)
    ezoapi = EZOAPI(Config.EZOAPI_APIKEY)
    discord = Discord(Config.DISCORD_BOTKEY, Config.DISCORD_GUILD, Config.DISCORD_ADMINCHAT)

    # STEP1 Create an intersect of web and discord data
    logging.debug("Creating an intersect of discord members and approved registrants...")
    discord_guild_member_ids = discord.get_guild_member_ids()

    for ignored_member in Config.IGNORE_MEMBERS:
        discord_guild_member_ids.remove(ignored_member)

    target_user_list = []

    for user in ezotv.get_users():
        if user['discord_id'] in discord_guild_member_ids:
            target_user_list.append(user)

    target_user_names = [member['minecraft_name'] for member in target_user_list]
    target_user_ids = [member['id'] for member in target_user_list]

    logging.info("List of allowed users: " + " ".join(target_user_names))

    # STEP2 unregister and kick everyone not on the list
    active_user_list = ezoapi.get_users()
    logging.info("Currently registered users: " + " ".join(member['realname'] for member in active_user_list))

    players_deleted = []
    for user in active_user_list:
        if not user['realname']:  # ratyis workaround
            user['realname'] = user['username']

        if user['id'] not in target_user_ids:
            logging.info(f"Removing {user['realname']}")
            ezoapi.delete_user(user['id'])
            players_deleted.append(user['realname'])

    active_user_list = ezoapi.get_users()
    logging.info("Registered users after cleaning: " + " ".join(member['realname'] for member in active_user_list))
    active_user_ids = [member['id'] for member in active_user_list]

    # STEP3 register everyone who is on the list but not in the database
    players_added = []
    for user in target_user_list:
        if user['id'] not in active_user_ids:
            logging.info(f"Creating user: {user['minecraft_name']}")
            ezoapi.create_user(
                user['id'],
                user['minecraft_name'],
                user['password'],
                user['salt']
            )

            players_added.append(user['minecraft_name'])

            logging.debug("Setting in_sync flag...")
            ezotv.set_sync(user['id'])

    active_user_list = ezoapi.get_users()
    logging.info("Registered users after creating new users: " + " ".join(member['realname'] for member in active_user_list))

    # STEP4 update all changed passwords and names
    logging.info("Updating passwords and names...")
    names_changed = []
    for auser in active_user_list:
        for tuser in target_user_list:
            if auser['id'] == tuser['id']:
                if auser['password'] != tuser['password'] or auser['salt'] != tuser['salt']:
                    logging.debug(f"Updating password for {tuser['minecraft_name']}")
                    ezoapi.update_password(tuser['id'], tuser['password'], tuser['salt'])

                    logging.debug("Setting in_sync flag...")
                    ezotv.set_sync(tuser['id'])

                if auser['realname'] != tuser['minecraft_name']:
                    logging.debug(f"Updating name {auser['realname']} -> {tuser['minecraft_name']}")
                    ezoapi.update_name(tuser['id'], tuser['minecraft_name'])

                    logging.debug("Setting in_sync flag...")
                    ezotv.set_sync(tuser['id'])
                    names_changed.append(f"{auser['realname']} -> {tuser['minecraft_name']}")

    # LAST STEP Send summary to discord adminchat
    if players_added or players_deleted or names_changed:
        logging.debug("Sending Discord message ...")

        message = "Synchronization complete!"

        if players_added:
            message += f"\nAdded {len(players_added)} players: " + ", ".join(players_added)

        if players_deleted:
            message += f"\nRemoved {len(players_deleted)} players: " + ", ".join(players_deleted)

        if names_changed:
            message += f"\nChanged {len(names_changed)} names: " + ", ".join(names_changed)

        discord.post_log(message)

    else:
        logging.debug("No Discord message sending required")

    logging.info("EZO-SYNC finished")


if __name__ == "__main__":
    main()
