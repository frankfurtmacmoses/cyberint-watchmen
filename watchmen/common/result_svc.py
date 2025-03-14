"""
watchmen/common/result_svc.py
This file is the service to process results generated from monitor()
and finds the correct notifiers to send alert messages.
The sns topic for each target is in notifier.json in order for the ResultSvc class to work.
In the future, sns topics will be in the config.yaml.

@author: Saba Farheen
@email: sfarheen@infoblox.com
"""
# python imports
import boto3
import traceback

# watchmen imports
from watchmen import const
from watchmen.common.result import Result
from watchmen.common.storage_service import StorageService
from watchmen.config import settings
from watchmen.utils.extension import convert_to_snake_case, get_class
from watchmen.utils.logger import get_logger

BUCKET = settings('STORAGE_BUCKET')
ENVIRONMENT = settings("ENVIRONMENT", "test")
GENERIC_TARGET_PREFIX = "Generic"
LOGGER = get_logger('watchmen.' + __name__)
NOTIFIER_DICTIONARY_NAME = "SNS"
NOTIFIER_FILE_NAME = 'notifiers_{}'.format(ENVIRONMENT)
NOTIFIER_MODEL_PREFIX = 'watchmen.common.'


class ResultSvc:
    """
    class of ResultSvc
    """

    def __init__(self, result_list: [Result]):
        """
        Constructor of ResultSvc class
        @param result_list: list of Result Object
        """
        self.result_list = result_list

    @staticmethod
    def _build_test_sns_topic():
        """
        Retrieves the account test sns topic from config.yaml and builds it out with the account details
        :return: The local test sns topic
        """
        try:
            profile = boto3.Session().profile_name
            sns_topic_path = 'result_svc.{}'.format(profile.lower())
            local_sns_topic = settings(sns_topic_path)

            region = boto3.Session().region_name
            sts_client = boto3.client('sts')
            account_id = sts_client.get_caller_identity().get('Account')

            return local_sns_topic.format(region=region, account_id=account_id)

        except Exception as ex:
            LOGGER.error('Could not get local test Topic! Traceback:\n{}'.format(ex))

    def create_lambda_message(self):
        """
        Makes the message that is returned to the lambda. The lambda message contains all of the messages
        within the list of result objects.
        :return: Formatted message of all "message" attributes in the list of result objects.
        """
        lambda_message = ""
        for result in self.result_list:
            lambda_message += result.short_message + const.LINE_SEPARATOR
        return lambda_message

    def _get_notifier(self, result):
        """
        Takes result and generates notifier from the notifier dictionary.
        @param result: <Result> result object
        @return: <Notifier> notifier class
        """
        notifiers_dict = self._load_notifiers()
        target = result.target
        try:
            notifier_class_name = notifiers_dict[target].get("notifier")
            notifier_model_name = convert_to_snake_case(notifier_class_name)
            notifier_model_path = NOTIFIER_MODEL_PREFIX + notifier_model_name
            return get_class(notifier_class_name, notifier_model_path)
        except KeyError:
            LOGGER.error('Target, {}, not found in {}!'.format(target, NOTIFIER_FILE_NAME))

    def _get_sns_topic(self, result):
        """
        Takes result and gives sns topic from the notifier dictionary.
        @param result: <Result> result object
        @return: <str> sns topic
        """
        notifiers_dict = self._load_notifiers()
        target = result.target
        try:
            sns_topic = notifiers_dict[target].get("sns")
            if not sns_topic and ENVIRONMENT is 'test':
                return self._build_test_sns_topic()

            return sns_topic
        except KeyError:
            LOGGER.error('Target, {}, not found in {}!'.format(target, NOTIFIER_FILE_NAME))

    @staticmethod
    def _load_notifiers():
        """
        Load notifier dictionary from NOTIFIER_FILE_NAME.
        @return: <dict> Dictionary of target names mapping to names of notifiers.
        """
        notifier_file_path = NOTIFIER_MODEL_PREFIX + NOTIFIER_FILE_NAME
        return get_class(NOTIFIER_DICTIONARY_NAME, notifier_file_path)

    @staticmethod
    def _remove_generic(results):
        """
        For each Result in result list, check if the target of the result is a generic target.
        This method removes the Result if it contains a generic target and returns the remaining non-generic results.
        @param results: <list> Result Objects.
        @return: <list> Non-Generic Result Objects; otherwise, None upon exception.
        """
        try:
            for result in results:
                target = result.target
                if GENERIC_TARGET_PREFIX in target:
                    results.remove(result)
            return results

        except Exception as ex:
            LOGGER.exception('{}'.format(ex))
            return None

    def save_results(self, results):
        """
        This method calls the remove_generic() method to remove the generic results.
        The obtained non-generic result objects are then saved using save_results() method from StorageService class.
        @param results: <list> Result Object.
        @return: Dict containing storage metadata; otherwise, None upon exception
        """
        storage_service = StorageService()

        try:
            trimmed_results = self._remove_generic(results)
            if trimmed_results:
                return storage_service.save_results(trimmed_results, BUCKET)
            # At the moment, it is better to save bad and/or redundant results than no results when removing
            # generic errors out. Our queries to S3 can be smart enough to handle this.
            return storage_service.save_results(results, BUCKET)
        except Exception as ex:
            LOGGER.exception('{}'.format(ex))
            return None

    def send_alert(self):
        """
        For each Result in result list, get its notifier and sns topic,
        and then send the alert.
        """
        try:
            for result in self.result_list:
                notifier_class = self._get_notifier(result)
                notifier = notifier_class(result)
                sns_topic = self._get_sns_topic(result)
                notifier.notify(sns_topic)
        except Exception as ex:
            LOGGER.exception(traceback.extract_stack())
            LOGGER.info(const.MESSAGE_SEPARATOR)
            LOGGER.exception('{}: {}'.format(type(ex).__name__, ex))
            return False
        return True
