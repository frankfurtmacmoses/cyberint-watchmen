"""
Created on July 18, 2018

This script is designed to check the lookalike feed daily and
ensure that data is coming through into S3.

@author Daryan Hanshew
@email dhanshew@infoblox.com

"""

# Python imports
from datetime import datetime, timedelta
from logging import getLogger
import pytz
import json

# Watchmen imports
from watchmen.utils.universal_watchman import Watchmen

LOGGER = getLogger(__name__)

SUCCESS_MESSAGE = "Lookalike feed is up and running!"
FAILURE_MESSAGE = "ERROR: Lookalike feed never added files from yesterday! The feed may be down!"

COMPLETED_STATUS = "COMPLETED"

BUCKET_NAME = "cyber-intel"
FILE_PATH = "analytics/lookalike/prod/results/"
STATUS_FILE = "status.json"


def process_status():
    """
    Checks timestamp of previous day for lookalike feed files being dropped into
    S3. Status.json has a state which determines if the process was successful or not.
    :return: whether the process finished or not
    """
    watcher = Watchmen()
    is_completed = False
    check_time = (datetime.now(pytz.utc) - timedelta(days=1)).strftime("%Y %m %d").split(' ')
    key = FILE_PATH + check_time[0] + '/' + check_time[1] + '/' + check_time[2] + '/' + STATUS_FILE
    file_contents = watcher.get_file_contents_s3(BUCKET_NAME, key)
    if file_contents:
        status_json = json.loads(file_contents)
        if status_json.get('STATE') == COMPLETED_STATUS:
            is_completed = True
    return is_completed


def main():
    """
    main
    :return: status of whether lookalike feed working or not
    """
    status = SUCCESS_MESSAGE
    is_status_valid = process_status()
    if not is_status_valid:
        status = FAILURE_MESSAGE
        # raise alarm
    LOGGER.info(status)
    return status
