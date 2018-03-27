import requests
from datetime import date
import os

class FRCTeamUpdateObserver(object):

    TEAM_UPDATE_URL = "https://firstfrc.blob.core.windows.net/frc{}/Manual/TeamUpdates/TeamUpdate{}.pdf"

    def __init__(self, last_team_update=None):
        if last_team_update:
            self.last_team_update = [date.today().year, last_team_update]
        else:
            self.last_team_update = [date.today().year, 18] 
            self._find_last_team_update()

    def _get_url(self, next_update=False):
        team_update = self.last_team_update[:]
        if next_update:
            team_update[1] += 1
        team_update_number = str(team_update[1])
        if team_update[1] < 10:
            # add trailing zero for numbers less than 10
            team_update_number = '0' + team_update_number

        return self.TEAM_UPDATE_URL.format(
            team_update[0], team_update_number
        )

    def _find_last_team_update(self):
        """
        Increments the second element in last_team_update until the last posted
        team update has been found with requests.
        """
        loop = True
        while loop:
            self.last_team_update[1] += 1
            r = requests.get(self._get_url())
            print(self._get_url())
            if r.status_code != 200:
                self.last_team_update[1] -= 1
                loop = False

    def _check_year(self):
        """
        Checks if there is a new year. If there is, the team update number is
        reset and the year is updated.
        """
        if (self.last_team_update[0] < date.today().year):
            self.last_team_update[0] = date.today().year
            self.last_team_update[1] = 1

    def check_for_team_updates(self):
        """
        Checks for a new FRC Team Update based on last_team_update values
        
        If it is found, the next time the URL is checked it will look for the next
        team update.

        :returns: None if the team update wasn't found, the url otherwise
        """
        self._check_year()
        url = self._get_url(next_update=True)
        
        print("Checking for team update at " + url + "...")
        r = requests.get(url)

        if r.status_code == 200:
            self.last_team_update[1] += 1
            return url
        else:
            return None