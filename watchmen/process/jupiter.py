"""
Created on January 29, 2019

This script monitors Sockeye ensuring the database and endpoints are working correctly for all endpoints on Sockeye.
If data is not found in the database or the endpoint does work correctly, an SNS will be sent.

@author: Kayla Ramos
@email: kramos@infoblox.com
"""
import json
import pytz

from datetime import datetime
from logging import getLogger, basicConfig, INFO

from watchmen.config import get_uint
from watchmen.config import settings
from watchmen.common.cal import InfobloxCalendar
from watchmen.common.svc_checker import ServiceChecker
from watchmen.process.endpoints import DATA as ENDPOINTS_DATA
from watchmen.utils.sns_alerts import raise_alarm
from watchmen.utils.s3 import copy_contents_to_bucket
from watchmen.utils.s3 import get_content

LOGGER = getLogger("Jupiter")
basicConfig(level=INFO)

CHECK_TIME_UTC = datetime.utcnow()
CHECK_TIME_PDT = pytz.utc.localize(CHECK_TIME_UTC).astimezone(pytz.timezone('US/Pacific'))
DATETIME_FORMAT = '%Y%m%d_%H%M%S'
MIN_ITEMS = get_uint('jupiter.min_items', 1)
SNS_TOPIC_ARN = settings("jupiter.sns_topic", "arn:aws:sns:us-east-1:405093580753:Sockeye")

# S3
S3_BUCKET = settings('aws.s3.bucket')
S3_PREFIX = settings('aws.s3.prefix')
S3_PREFIX_JUPITER = settings('jupiter.s3_prefix')
S3_PREFIX_STATE = '{}/{}/LATEST'.format(S3_PREFIX, S3_PREFIX_JUPITER)

# Messages
CHECK_LOGS = "Please check logs for more details!"
ERROR_JUPITER = "Jupiter: Failure in runtime"
ERROR_SUBJECT = "Jupiter: Failure in checking endpoint"
NO_RESULTS = "There are no results! Endpoint file might be empty or Service Checker may not be working correctly. " \
             "Please check logs and endpoint file to help identify the issue."
NOT_ENOUGH_EPS = "Jupiter: Too Few Endpoints"
NOT_ENOUGH_EPS_MESSAGE = "Endpoint count is below minimum. There is no need to check or something is wrong with " \
                         "endpoint file."
RESULTS_DNE = "Results do not exist! There is nothing to check. Service Checker may not be working correctly. " \
              "Please check logs and endpoint file to help identify the issue."
SKIP_MESSAGE_FORMAT = "Notification is skipped at {}"
SUCCESS_MESSAGE = "All endpoints are good!"


def check_endpoints(endpoints):
    """
    Checks if first level endpoints are valid or not.
    Non-valid endpoints are printed with error messages.
    If too few validated endpoints exist, no need to check.
    @param endpoints: endpoints to be checked
    @return: list of validated endpoints
    """
    bad_list = []
    validated = []
    for item in endpoints:
        if item.get('path'):
            validated.append(item)
        else:
            bad_list.append(item)

    if bad_list:
        subject = ERROR_SUBJECT
        messages = []
        for item in bad_list:
            msg = 'There is not a path to check for: {}'.format(item.get('name', "There is not a name available"))
            messages.append(msg)
            LOGGER.error('Notify failure:\n%s', msg)
        message = '\n'.join(messages)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        pass

    if len(validated) < MIN_ITEMS:
        subject = NOT_ENOUGH_EPS
        message = NOT_ENOUGH_EPS_MESSAGE
        LOGGER.warning(NOT_ENOUGH_EPS_MESSAGE)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
        return None

    return validated


def _check_last_failure():
    """
    Use key, e.g. bucket/prefix/LATEST to check if last check failed.
    LATEST key contains result (non-empty) if last result has failure; empty indicates success.

    @return: True if last check failed; otherwise, False.
    """
    data = get_content(S3_PREFIX_STATE, bucket=S3_BUCKET)
    return data != ''


def _check_skip_notification():
    """
    If current day and hour do not fall under the desired notification times, there is no need to send a notification
    @return: whether or not to send a notification
    """
    now = CHECK_TIME_PDT
    hour = now.hour
    year = now.year
    # Create a calendar for last year, current year, and next year
    cal = InfobloxCalendar(year - 1, year, year + 1)
    to_skip = False

    if not cal.is_workday():
        to_skip = hour % 8 != 0
    elif not cal.is_workhour(hour):
        to_skip = hour % 4 != 0

    return to_skip


def load_endpoints():
    """
    Loads json file of endpoints.
    If an exception is thrown (meaning an error with opening and/or loading),
    an sns will be sent to the Sockeye Topic
    :return: the endpoints or exits upon exception
    """
    # This will always run because there is no s3 file setup yet
    data_path = settings("aws.s3.prefix")
    data_file = settings("jupiter.endpoints")

    if data_path:
        data_file = '{}/{}'.format(data_path, data_file)

    bucket = settings("aws.s3.bucket")
    data = get_content(data_file, bucket=bucket)

    try:
        endpoints = json.loads(data)
        if endpoints and isinstance(endpoints, list):
            validated = check_endpoints(endpoints)
            if validated:
                return validated
    except Exception as ex:
        subject = "Jupiter endpoints - load error"
        fmt = "Cannot load endpoints from bucket={}, key={}\n{}\nException:{}"
        msg = fmt.format(bucket, data_file, data, ex)
        LOGGER.warning(msg)
        raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=msg)

    endpoints = ENDPOINTS_DATA

    return endpoints


def log_result(results):
    """
    Log results to s3
    @param results: to be logged
    """
    try:
        prefix_datetime = CHECK_TIME_UTC.strftime(DATETIME_FORMAT)
        prefix_result = '{}/{}/{}/{}.json'.format(S3_PREFIX, S3_PREFIX_JUPITER, CHECK_TIME_UTC.year, prefix_datetime)
        LOGGER.info("Jupiter Watchmen results:\n{}".format(results))
        # save result to s3
        content = json.dumps(results, indent=4, sort_keys=True)
        copy_contents_to_bucket(content, prefix_result, S3_BUCKET)
    except Exception as ex:
        LOGGER.error(ex)


def log_state(sanitized_result):
    try:
        success = sanitized_result.get('success')
        content = '' if success else json.dumps(sanitized_result, indent=4, sort_keys=True)
        prefix_state = '{}/{}/LATEST'.format(S3_PREFIX, S3_PREFIX_JUPITER)
        copy_contents_to_bucket(content, prefix_state, S3_BUCKET)
    except Exception as ex:
        LOGGER.error(ex)


# pylint: disable=unused-argument
def main(event, context):
    """
    main function
    :return: status of Sockeye endpoints
    """
    endpoints = load_endpoints()
    checked_endpoints = check_endpoints(endpoints)
    checker = ServiceChecker(checked_endpoints)
    results = checker.start()
    log_result(results)
    validated_paths = checker.get_validated_paths()
    sanitized_result = sanitize(results, endpoints, validated_paths)
    log_state(sanitized_result)
    notify(sanitized_result)

    return sanitized_result


def notify(sanitized_result):
    message = sanitized_result.get('message')
    subject = sanitized_result.get('subject')
    success = sanitized_result.get('success')

    if success:
        return SUCCESS_MESSAGE

    # it is failed right now; should not skip if this is the first failure detection.
    is_skipping = _check_last_failure() and _check_skip_notification()
    if is_skipping:
        return SKIP_MESSAGE_FORMAT.format(CHECK_TIME_UTC)

    raise_alarm(SNS_TOPIC_ARN, subject=subject, msg=message)
    pass


def sanitize(results, endpoints, validated_paths):
    """
    Send notifications to Sockeye topic if failed endpoints exist or no results exist at all.
    Notifications vary depending on the time and day.
    If the day is a holiday and the hour is 8am or 4pm, a notification will be sent.
    If the day is a work day and the hour is 8am, 12pm, or 4pm, a notification will be sent.
    Otherwise, all notifications will be skipped.
    Although a notification may not be sent, results will be logged at all times.
    @param results: dict to be checked for failed endpoints
    @param endpoints: loaded endpoints data
    @param validated_paths: validated endpoints
    @return: the notification message
    """
    if not results or not isinstance(results, dict):
        message = RESULTS_DNE
        return {
            "message": message,
            "subject": ERROR_JUPITER,
            "success": False,
        }

    failure = results.get('failure', [])
    success = results.get('success', [])

    # Checking if results is empty
    if not failure and not success:
        split_line = '-'*80
        message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(results, sort_keys=True, indent=2),
            split_line,
            json.dumps(endpoints, indent=2),
            split_line,
            json.dumps(validated_paths, indent=2)
        )
        LOGGER.error(message)
        message = "{}\n\n\n{}".format(message, NO_RESULTS)
        return {
            "message": message,
            "subject": ERROR_JUPITER,
            "success": False,
        }

    # Checking failure list and announcing errors
    if failure and isinstance(failure, list):
        messages = []
        for item in failure:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            messages.append(msg)
            LOGGER.error('Notify failure:\n%s', msg)
        message = '{}\n\n\n{}'.format('\n\n'.join(messages), CHECK_LOGS)

        first_failure = 's' if len(failure) > 1 else ' - {}'.format(failure[0].get('name'))
        subject = '{}{}'.format(ERROR_SUBJECT, first_failure)
        return {
            "message": message,
            "subject": subject,
            "success": False,
        }

    # All Successes
    return {
        "message": SUCCESS_MESSAGE,
        "success": True,
    }
