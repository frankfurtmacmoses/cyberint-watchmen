"""
Created August 2021

This watchman is designed to check status of reflections pulled out on the fly by dremio.py based on information
specified in the config, dremoio_targets.yaml.
Currently the checks that can be performed are for reflections that already be created and that does not start
with tmp. Reflections status are checked every 60minutes


@author: Olawole Frankfurt Ogunfunminiyi
@email: oogunfunminiyi@infoblox.com
"""

import datetime
import os
import traceback
import yaml
import watchmen.utils.dremio as dremio
from watchmen import const, messages
from watchmen.common.result import Result
from watchmen.common.watchman import Watchman
from watchmen.config import settings

CONFIG_NAME = settings('ozymandias.targets')

SECRETE = settings('ozymandia.dremio_secret')
ROOT_URL = settings('ozymandia.ROOT_URL')
LOGIN_URL = settings('ozymandia.LOGIN_URL')
REFLECTION_URL = settings('ozymandia.REFLECTION_URL')
MESSAGES = messages.OZYMANDIAS
REGION = settings("ozymandia.targets.region")
user_name = settings("ozymandia.targets.region")
final_result = {}
CONFIG_PATH = os.path.join(
    os.path.realpath(os.path.dirname(__file__)), 'configs', CONFIG_NAME)


class Ozymandias(Watchman):

    def __init__(self, event, context):
        """
        Ozymandias Constructor
        """
        super().__init__()
        self.event = event.get('Type')

    def monitor(self):
        """
        Monitors Dremio Targets in the config.yaml file
        :return: <List> A list of result objects from the checks performed on each target.
        """

        if not self._is_valid_event():
            return self._create_invalid_event_result()

        github_targets, tb = self._load_config()
        if tb:
            return self._create_config_not_loaded_result()

        processed_targets = self._process_targets(github_targets)
        summary_parameters = self._create_summary_parameters(processed_targets)
        results = self._create_results(summary_parameters)
        return results


    @staticmethod
    def create_details():
        """
        Creates details for the result objects from the new_change_strings and exception_strings if they exist.
        :param processed_target: <dict> A dictionary of the target name with any failures or exceptions that occurred
        :return: <str> A details string for the target with information from the checks performed
        """
        secret = dremio.get_secret(SECRETE, REGION)
        """
        split secrete dictionary to user_name and password, pass the outputs to dremio.generate_auth_token
        """
        token = dremio.generate_auth_token(str(list(secret.keys())), str(list(secret.values())))
        reflection_list = dremio.get_reflection_list(token, REFLECTION_URL)

        reflection_results = dremio.fetch_reflection_metadata(token, reflection_list, REFLECTION_URL)
        """
        Return list containing dictionary of reflection result
         Get information about single reflection and return ->  "status": {
        "config": "OK",
        "refresh": "SCHEDULED",
        "availability": "AVAILABLE",
        "combinedStatus": "CAN_ACCELERATE",
        "failureCount": 0,
        "lastDataFetch": "2021-08-16T20:55:58.311Z",
        "expiresAt": "2021-08-16T23:55:58.311Z"
                                 }   
        """

        for reflection_result in reflection_results:
            reflectionid, name, failurecount = reflection_result["id"], reflection_result["name"], \
                                               reflection_result["status"]['failureCount']
            if failurecount == 3:
                final_result[reflectionid]: [name, failurecount]

        return final_result

    def _format_results(self):

        results = []


                details=parameters.get("details"),
                disable_notifier=parameters.get("disable_notifier"),
                short_message=parameters.get("short_message"),
                snapshot={},
                state=parameters.get("state"),
                subject=parameters.get("subject"),
                success=success is True,
                target=parameters.get("target"),
                watchman_name=self.watchman_name,



    def switcher(self, reflection_final_result):
        if bool(reflection_final_result):

            "False" = {
                "disable_notifier": False,
                "state": "Failled",
                "success": False
            }

            None: {
                "disable_notifier": False,
                "state": "Exception",
                "success": None
            },
            True: {
                "disable_notifier": True,
                "state": "Success",
                "success": True
            },





    @staticmethod
    def _format_api_exception(check_name, target_name, tb, path=None):

