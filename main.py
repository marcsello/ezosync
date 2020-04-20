#!/usr/bin/env python3
import os

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

import MySQLdb
import requests
import logging
import logging.handlers
from mcrcon import MCRcon

from lockfile import LockFile
from db import DB
from discord import Discord
from ezotv import EZOTV


def run():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s", handlers=[
        logging.handlers.RotatingFileHandler(os.environ.get("LOGPATH", "logs/ezosync.log"), maxBytes=1048576, backupCount=5),
        logging.StreamHandler()
    ])


    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:
        sentry_logging = LoggingIntegration(
            level=logging.DEBUG,
            event_level=logging.ERROR  # Send errors as events
        )
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[sentry_logging],
            send_default_pii=True
        )

    logging.info("Starting EZO-SYNC...")
    # Prepare some stuff
    logging.debug("Preparing connections...")
    db = DB(os.environ['MYSQL_USER'], os.environ['MYSQL_PASSWORD'], os.environ['MYSQL_DB'], os.environ.get('MYSQL_HOST', None), os.environ.get('MYSQL_TABLE', 'authme'))
    ezotv = EZOTV(os.environ['EZOTV_APIKEY'])
    discord = Discord(os.environ['DISCORD_BOTKEY'], os.environ['DISCORD_GUILD'], os.environ['DISCORD_ADMINCHAT'])

    # STEP1 Create an intersect of web and discord data
    logging.debug("Creating an intersect of discord members and approved registrants...")
    discord_guild_member_ids = discord.get_guild_member_ids()
    discord_guild_member_ids.remove('329622641713348618')  # EZO-BOT

    target_user_list = []

    for user in ezotv.get_users():
        if user['discord_id'] in discord_guild_member_ids:
            target_user_list.append(user)

    target_user_names = [member['minecraft_name'] for member in target_user_list]

    logging.info("List of allowed users: " + " ".join(target_user_names))

    # WARNING: Name change is currently handled by an unregister-re-register sequence. Later, when users addressed by id. this should be considered

    # STEP2 unregister and kick everyone not on the list
    active_user_list = db.get_current_users()
    active_user_names = [member['realname'] for member in active_user_list]
    logging.info("Currently registered users: " + " ".join(active_user_names))

    players_to_kick = []
    for user in active_user_list:
        if not user['realname']:  # ratyis workaround
            user['realname'] = user['username']

        if user['realname'] not in target_user_names:
            logging.info("Removing {}".format(user['realname']))

            # Delete registration
            db.delete_user(user['id'])
            players_to_kick.append(user['realname'])

    if players_to_kick:
        with MCRcon(os.environ['RCON_HOST'], os.environ['RCON_PASSWORD']) as mcr:
            for player_to_kick in players_to_kick:
                # kick player
                logging.debug(f"Kicking {player_to_kick}...")
                logging.debug("MC RCON: " + mcr.command(f"kick {player_to_kick} Az EZO.TV regisztrációd megszűnt!"))

    players_kicked = players_to_kick

    active_user_list = db.get_current_users()
    active_user_names = [member['realname'] for member in active_user_list]
    logging.info("Registered users after cleaning: " + " ".join(active_user_names))

    # STEP3 register everyone who is on the list but not in the database
    players_added = []
    for user in target_user_list:
        if user['minecraft_name'] not in active_user_names:
            logging.info("Creating user: {}".format(user['minecraft_name']))
            db.create_user(user['id'], user['minecraft_name'].lower(), user['minecraft_name'], user['password'], user['salt'])

            players_added.append(user['minecraft_name'])

            logging.debug("Setting in_sync flag...")
            ezotv.set_sync(user['id'])

    active_user_list = db.get_current_users()
    active_user_names = [member['realname'] for member in active_user_list]
    logging.info("Registered users after creating new users: " + " ".join(active_user_names))

    # STEP4 update all changed passwords
    logging.info("Updating passwords...")
    for auser in active_user_list:
        for tuser in target_user_list:
            if auser['realname'] == tuser['minecraft_name']:
                if auser['password'] != tuser['password'] or auser['salt'] != tuser['salt']:
                    logging.debug('Updating password for {}'.format(tuser['minecraft_name']))
                    db.update_password(tuser['id'], tuser['password'], tuser['salt'])

                    logging.debug("Setting in_sync flag...")
                    ezotv.set_sync(tuser['id'])

    # LAST STEP Send summary to discord adminchat
    if players_added or players_kicked:
        logging.debug("Sending Discord message ...")

        message = "Synchronization complete!"

        if players_added:
            message += f"\nAdded {len(players_added)} players: " + ", ".join(players_added)

        if players_kicked:
            message += f"\nRemoved {len(players_kicked)} players: " + ", ".join(players_kicked)

        discord.post_log(message)

    else:
        logging.debug("No Discord message sending required")

    logging.info("EZO-SYNC finished")


def main():
    # Step -1 read config file
    l = LockFile('/tmp/ezosync.pid')

    with l:  # makes sure, hogy ezen a rendszeren egyidőben csak egyszer fusson
        run()


if __name__ == "__main__":
    main()
