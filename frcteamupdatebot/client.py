import discord
import asyncio
import psycopg2
import os
import logging
import sys
import requests
from psycopg2 import errorcodes
from .observer import FRCTeamUpdateObserver

HELP_MESSAGE = """Type '!frctu mark' to mark a channel for team updates.
Type '!frctu unmark' to unmark a channel for team updates."""
# these default settings assume this is being ran with docker-compose
ADMIN_IDS = ['188472809280897024', '117126246168657924']
DEFAULT_PSYCOPG2_SETTINGS = "dbname=postgres user=postgres password=postgres host=172.19.0.3"
PSYCOPG2_SETTINGS = os.getenv("PSYCOPG2_SETTINGS", default=DEFAULT_PSYCOPG2_SETTINGS)
TEAM_UPDATE_URL = "https://firstfrc.blob.core.windows.net/frc{}/Manual/TeamUpdates/TeamUpdate{}.pdf"
TIMESTAMP_FORMAT = "'%Y-%m-%d'"
TEAM_UPDATE_MESSAGE = ("New FRC Team Update:\n"
                        "{}")   

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
client = discord.Client()

# import after stuff is defined

@client.event
async def on_ready():
    print('\nLogged in as\n------')
    print(client.user.name)
    print(client.user.id)
    print('------\n\n')

    if os.getenv("DISABLE_TEAM_UPDATE_OBSERVER", default=False) == 'True':
        pass
    else:
        if "FRCTU_LAST_TEAM_UPDATE" in os.environ:
            observer = FRCTeamUpdateObserver(last_team_update=int(os.environ["FRCTU_LAST_TEAM_UPDATE"]))
        else:
            observer = FRCTeamUpdateObserver()
        observe(observer)

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
                    db = psycopg2.connect(PSYCOPG2_SETTINGS)
                    cursor = db.cursor()
                    cursor.execute(query, (message.channel.id, ))
                    cursor.close()
                    db.commit()
                    db.close()
                    await client.send_message(message.channel, success_message)
                except psycopg2.IntegrityError:
                    await client.send_message(
                        message.channel,
                        "This channel has already been marked for FRC Team Updates."
                    )
                except psycopg2.Error as err:
                    try:
                        await client.send_message(
                            message.channel, 
                            "An internal database error occured while trying to process your request: " + errorcodes.lookup(err.pgcode)
                        )
                    except KeyError:
                        await client.send_message(
                            message.channel, 
                            "An unknown internal error occured. ¯\_(ツ)_/¯"
                        )
            else:
                await client.send_message(message.channel, "Administrator priveleges are required for command '" + command[1] + "'.")

def observe(observer):
    client.loop.call_later(1800, observe, observer)
    pdf_url = observer.check_for_team_updates()
    if pdf_url:
        pdf_url = save_to_web_archive(pdf_url)
        message = TEAM_UPDATE_MESSAGE.format(pdf_url)
        send_message_to_channels_in_db(
            message, psycopg2.connect(PSYCOPG2_SETTINGS), client.loop
        )

WEB_ARCHIVE_HOST = "https://web.archive.org"
WEB_ARCHIVE_SAVE_URL = "https://web.archive.org/save/"

def save_to_web_archive(url):
    """
    Saves a webpage to WebArchive using the Wayback Machine

    :param url: the url of the webpage
    
    :returns: the resulting WebArchive url
    """
    return WEB_ARCHIVE_HOST + requests.get(
        WEB_ARCHIVE_SAVE_URL + url,
        allow_redirects=False
    ).headers['Content-Location']

def send_message_to_channels_in_db(message, db, event_loop):
    """
    Sends the message to all of the channels currently contained in the
    PostgreSQL database

    :param message: the message
    :param db: the psycopg2 connection
    :param event_loop: the event loop to use when sending the messages
    """
    cursor = db.cursor()
    cursor.execute("SELECT * FROM channels;")
    for record in cursor:
        channel = client.get_channel(str(record[0]))
        #TODO delete the channel from DB if it doesn't exist
        if channel:
            # event_loop.create_task(client.send_file(channel, file))
            event_loop.create_task(client.send_message(channel, message))
    cursor.close()
    db.close()