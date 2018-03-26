from .client import db, client
import requests
import tempfile
import os
import threading
import time
import urllib
from datetime import date
import asyncio
from .observer import FRCTeamUpdateObserver

class FRCTeamUpdateThread(threading.Thread):
    """
    This thread checks for a new FRC Team Update every 30 minutes

    Originally I was going to use Celery Beat, but Celery runs 
    in a seperate worker process, and I can't access the same
    Discord client object from two seperate processes.
    """

    #TODO change to 10 for production
    FIRST_TEAM_UPDATE_NUMBER = 18

    TEAM_UPDATE_URL = "https://firstfrc.blob.core.windows.net/frc{}/Manual/TeamUpdates/TeamUpdate{}.pdf"
    TIMESTAMP_FORMAT = "'%Y-%m-%d'"
    TEAM_UPDATE_MESSAGE = ("New FRC Team Update:\n"
                           "{}")                 

    def __init__(self, event_loop):
        threading.Thread.__init__(self)
        self.observer = FRCTeamUpdateObserver(self.FIRST_TEAM_UPDATE_NUMBER)
        self.event_loop = event_loop

    def run(self):
        # overrides threading.Thread.run()
        while True:
            pdf_url = self.observer.check_for_team_updates()
            if pdf_url:
                pdf_url = save_to_web_archive(pdf_url)
                message = self.TEAM_UPDATE_MESSAGE.format(pdf_url)
                send_message_to_channels_in_db(
                    message, db, self.event_loop
                )
            time.sleep(1800.0)

        
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