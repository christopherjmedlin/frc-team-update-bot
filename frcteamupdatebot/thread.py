from .client import PSYCOPG2_SETTINGS, client
import requests
import tempfile
import os
import threading
import time
import urllib
from datetime import date
import asyncio
from .observer import FRCTeamUpdateObserver
import psycopg2

class FRCTeamUpdateThread(threading.Thread):
    """
    This thread checks for a new FRC Team Update every 30 minutes

    Originally I was going to use Celery Beat, but Celery runs 
    in a seperate worker process, and I can't access the same
    Discord client object from two seperate processes.
    """

                  

    def __init__(self, event_loop):
        threading.Thread.__init__(self)
        if "FRCTU_LAST_TEAM_UPDATE" in os.environ:
            self.observer = FRCTeamUpdateObserver(last_team_update=int(os.environ["FRCTU_LAST_TEAM_UPDATE"]))
        else:
            self.observer = FRCTeamUpdateObserver()
        self.event_loop = event_loop

    def run(self):
        # overrides threading.Thread.run()
        while True:
            pdf_url = self.observer.check_for_team_updates()
            if pdf_url:
                pdf_url = save_to_web_archive(pdf_url)
                message = self.TEAM_UPDATE_MESSAGE.format(pdf_url)
                send_message_to_channels_in_db(
                    message, psycopg2.connect(PSYCOPG2_SETTINGS), self.event_loop
                )
            time.sleep(1800.0)