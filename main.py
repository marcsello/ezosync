#!/usr/bin/env python3
import os
import MySQLdb
import requests
import logging
from mcrcon import MCRcon

from lockfile import LockFile
from db import DB
from discord import Discord
from ezotv import EZOTV


def run():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s", handlers=[
        logging.FileHandler("ezosync.log"),
        logging.StreamHandler()
    ])

    logging.info("Starting EZO-SYNC...")
    # Prepare some stuff
    logging.debug("Preparing connections...")
    db = DB(os.environ['MYSQL_USER'], os.environ['MYSQL_PASSWORD'], os.environ['MYSQL_DB'], os.environ.get('MYSQL_HOST', None), os.environ.get('MYSQL_TABLE', 'authme'))
    ezotv = EZOTV(os.environ['EZOTV_APIKEY'])
    discord = Discord(os.environ['DISCORD_BOTKEY'], os.environ['DISCORD_GUILD'])
    mcr = MCRcon(os.environ['RCON_HOST'], os.environ['RCON_PASSWORD'])

    # STEP1 Create an intersect of web and discord data
    logging.debug("Creating an intersect of discord members and approved registrants...")
    discord_guild_member_ids = discord.get_guild_member_ids()
    discord_guild_member_ids.remove('329622641713348618')  # EZO-BOT

    master_user_list = []

    for user in ezotv.get_users():
        if user['discord_id'] in discord_guild_member_ids:
            master_user_list.append(user)

    logging.info("List of allowed users: " + " ".join(member['minecraft_name'] for member in master_user_list))

    # STEP2 unregister and kick everyone not on the list
    # STEP3 register everyone who is on the list but not in the database
    # STEP4 update all changed passwords

    logging.info("EZO-SYNC finished")


def main():
    # Step -1 read config file
    l = LockFile('/tmp/ezosync.pid')

    with l:  # makes sure, hogy ezen a rendszeren egyidőben csak egyszer fusson
        run()


if __name__ == "__main__":
    main()
