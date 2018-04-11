from .client import client, PSYCOPG2_SETTINGS
import requests, psycopg2

TEAM_UPDATE_MESSAGE = ("New FRC Team Update:\n"
                        "{}")

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