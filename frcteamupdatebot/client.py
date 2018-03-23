import discord
import asyncio
import psycopg2
import os
import logging
import sys
import requests

HELP_MESSAGE = """Type '!frctu mark' to mark a channel for team updates.
Type '!frctu unmark' to unmark a channel for team updates."""
# these default settings assume this is being ran with docker-compose
DEFAULT_PSYCOPG2_SETTINGS = "dbname=postgres user=postgres password=postgres host=172.19.0.3"
ADMIN_IDS = ['188472809280897024', '117126246168657924']

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
client = discord.Client()
db = psycopg2.connect(os.getenv("PSYCOPG2_SETTINGS", default=DEFAULT_PSYCOPG2_SETTINGS))

# import after stuff is defined
from .thread import FRCTeamUpdateThread

@client.event
async def on_ready():
    print('\nLogged in as\n------')
    print(client.user.name)
    print(client.user.id)
    print('------\n\n')

    if os.getenv("DISABLE_TEAM_UPDATE_OBSERVER", default=False) == 'True':
        pass
    else:
        print("Starting thread...")
        FRCTeamUpdateThread(asyncio.get_event_loop()).start()
        print("Thread started.")

#TODO holy shit i need to refactor this mess
@client.event
async def on_message(message):
    if message.content.startswith("!frctu"):
        command = message.content.split() 
        query = None
        success_message = None
        if len(command) >= 2:
            if command[1] == "mark":
                query = """
                        INSERT INTO channels (id) VALUES (%s);
                        """
                success_message = "'" + message.channel.name + "' has been marked for FRC team updates."
            elif command[1] == "unmark":
                query = "DELETE FROM channels WHERE id=%s;"
                success_message = "'" + message.channel.name + "' has been unmarked for FRC team updates."
            elif command[1] == "stop":
                if message.author.id in ADMIN_IDS:
                    await client.send_message(message.channel, "Going to sleep...")
                    db.close()
                    sys.exit()
                else:
                    await client.send_message(message.channel, "'" + command[1] + "' is not a command.")
                    await client.send_message(message.channel, HELP_MESSAGE)
            else:
                await client.send_message(message.channel, "'" + command[1] + "' is not a command.")
                await client.send_message(message.channel, HELP_MESSAGE)
        else:
            await client.send_message(message.channel, HELP_MESSAGE)
        if query:
            permissions = message.author.permissions_in(message.channel)
            if permissions.administrator:
                try:
                    cursor = db.cursor()
                    cursor.execute(query, (message.channel.id, ))
                    cursor.close()
                    db.commit()
                    await client.send_message(message.channel, success_message)
                except psycopg2.IntegrityError:
                    await client.send_message(
                        message.channel,
                        "This channel has already been marked for FRC Team Updates."
                    )
                except psycopg2.Error as err:
                    await client.send_message(
                        message.channel, 
                        "An internal database error occured while trying to process your request:\n\n" + err.message
                    )
            else:
                await client.send_message(message.channel, "Administrator priveleges are required for command '" + command[1] + "'.")
