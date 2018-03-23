#!/usr/bin/env python

from frcteamupdatebot.client import client

import os
import logging

class MissingEnvironmentVariableException(Exception):
    """Raise for when the user forgot to define a required
    environment variable"""

if __name__ == "__main__":  
    logging.basicConfig(level=logging.INFO)
    print("asdf")
    try:
        client.run(os.environ["TOKEN"])
    except KeyError:
        raise MissingEnvironmentVariableException("Missing Discord API token environment variable.")