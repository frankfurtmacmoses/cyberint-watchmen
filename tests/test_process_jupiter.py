import json
import pytz
import unittest
from datetime import datetime
from mock import patch

from watchmen import const
from watchmen.process.endpoints import DATA as LOCAL_ENDPOINTS
from watchmen.process.jupiter import Jupiter
from watchmen.process.jupiter import \
    BAD_ENDPOINTS_MESSAGE, \
    CHECK_LOGS, \
    ERROR_JUPITER, \
    ERROR_SUBJECT, \
    FAILURE_SUBJECT, \
    NO_RESULTS, \
    NOT_ENOUGH_EPS, \
    NOT_ENOUGH_EPS_MESSAGE, \
    RESULTS_DNE, \
    SUCCESS_MESSAGE, \
    SUCCESS_SUBJECT, \
    TARGET


class TestJupiter(unittest.TestCase):

    def setUp(self):
        self.check_time_utc = datetime.utcnow()
        self.example_bad_endpoints_result = {
            "details": NOT_ENOUGH_EPS_MESSAGE,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": BAD_ENDPOINTS_MESSAGE + const.LINE_SEPARATOR,
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "EXCEPTION",
            "subject": NOT_ENOUGH_EPS,
            "success": False,
            "target": TARGET,
        }
        self.example_bad_list = [
            {"name": "NoPath"},
            {}
        ]
        self.example_bad_messages = "There is not a path to check for: HaveName\n" \
                                    "There is not a path to check for: There is not a name available"
        self.example_data = """[{
                                    "name": "happy data from s3",
                                    "path": "success",
                                    "more": [{
                                        "name": "nested data"
                                    }]
                                },{
                                    "name": "missing data"
                                }]
                                """
        self.example_date_format = '%Y%m%d'
        self.example_empty = {
            "failure": [],
            "success": []
        }
        self.example_endpoints = [
            {"name": "endpoint", "path": "example"},
            {"name": "Used for testing"}
        ]
        self.example_exception_message = "An exception occurred."
        self.example_exception_result = {
            "details": NOT_ENOUGH_EPS_MESSAGE,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": NOT_ENOUGH_EPS_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "EXCEPTION",
            "subject": NOT_ENOUGH_EPS,
            "success": False,
            "target": TARGET,
        }
        self.example_failed = {
            "failure": [
                {"name": "Failure", "path": "filler/fail", "_err": "something"},
                {"key": "Big fail"}
            ],
            "success": []
        }
        self.example_failure_message = "Endpoints failed during check!"
        self.example_failure_result = {
            "details": self.example_failure_message,
            "disable_notifier": False,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": SUCCESS_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "FAILURE",
            "subject": FAILURE_SUBJECT,
            "success": False,
            "target": TARGET,
        }
        self.example_few_validated = []
        self.example_holiday_bad_time = datetime(year=2018, month=12, day=25, hour=9, tzinfo=pytz.utc)
        self.example_holiday_good_time = datetime(year=2018, month=12, day=25, hour=8, tzinfo=pytz.utc)
        self.example_holiday_midnight_time = datetime(year=2018, month=12, day=25, hour=0, tzinfo=pytz.utc)
        self.example_invalid_paths = [
            {"key": "that fails"}
        ]
        self.example_local_endpoints = [
            {"name": "local", "path": "s3/failed"}
        ]
        self.example_no_failures = {
            "failure": [],
            "success": [
                {"name": "succeeded"}
            ]}
        self.example_passed_endpoints = [
            {"name": "good endpoint", "path": "good/path"}
        ]
        self.example_prefix = "watchmen/jupiter/{}/{}".format("2019",
                                                              self.check_time_utc.strftime(self.example_date_format))
        self.example_results_mix = {
            'failure': [{
                'name': 'failed'
            }],
            'success': [{
                'name': 'passed'
            }]}
        self.example_result_parameters = {
            "success": True,
            "disable_notifier": True,
            "state": "SUCCESS",
            "subject": SUCCESS_SUBJECT,
        }
        self.example_results_passed = {
            'failure': [{
                'name': 'failed'
            }],
            'success': [{
                'name': 'passed'
            }]}
        self.example_status = "Everything has been checked!"
        self.example_success_result = {
            "details": SUCCESS_MESSAGE,
            "disable_notifier": True,
            "dt_created": "2018-12-18T00:00:00+00:00",
            "dt_updated": "2018-12-18T00:00:00+00:00",
            "is_ack": False,
            "is_notified": False,
            "message": SUCCESS_MESSAGE,
            "result_id": 0,
            "snapshot": {},
            "source": "Jupiter",
            "state": "SUCCESS",
            "subject": SUCCESS_SUBJECT,
            "success": True,
            "target": TARGET,
        }
        self.example_summarized_results = {
            "last_failed": True,
            "message": "This is your in-depth result",
            "subject": "Good subject line",
            "success": False,
        }
        self.example_today = datetime(year=2018, month=12, day=18, tzinfo=pytz.utc)
        self.example_valid_paths = [{
            "name": "I will work",
            "path": "here/is/path"
        }]
        self.example_validated = [{
            "name": "endpoint",
            "path": "example"
        }]
        self.example_validated_list = [
            {"name": "HaveName", "path": "have/path"},
            {"path": "pathWith/NoName"}
        ]
        self.example_variety_endpoints = [
            {"name": "endpoint", "path": "cool/path"},
            {"key": "bad endpoint"}
        ]
        self.example_workday_bad_time = datetime(year=2019, month=10, day=28, hour=15, tzinfo=pytz.utc)
        self.example_workday_good_time = datetime(year=2019, month=10, day=28, hour=12, tzinfo=pytz.utc)
        self.example_weekend_bad_time = datetime(year=2019, month=10, day=27, hour=15, tzinfo=pytz.utc)
        self.example_weekend_good_time = datetime(year=2019, month=10, day=27, hour=16, tzinfo=pytz.utc)

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_check_endpoints_path(self, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        tests = [
            {"endpoints": self.example_valid_paths, "expected": self.example_valid_paths},
            {"endpoints": self.example_invalid_paths, "expected": None}
        ]

        for test in tests:
            endpoints = test.get("endpoints")
            expected = test.get("expected")
            returned = jupiter_obj.check_endpoints_path(endpoints)
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.get_content')
    def test_check_failure(self, mock_get_content):
        jupiter_obj = Jupiter(event=None, context=None)
        test_results = [
            {"file_content": None, "expected": False},
            {"file_content": "", "expected": False},
            {"file_content": "FAILURE!!!", "expected": True}
        ]

        for test in test_results:
            mock_get_content.return_value = test.get("file_content")
            expected = test.get("expected")
            returned = jupiter_obj._check_failure()
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter._get_time_pdt')
    def test_check_notification_time(self, mock_datetime):
        tests = [
            {"time": self.example_holiday_bad_time, "expected": False},
            {"time": self.example_holiday_good_time, "expected": True},
            {"time": self.example_holiday_midnight_time, "expected": False},
            {"time": self.example_workday_bad_time, "expected": False},
            {"time": self.example_workday_good_time, "expected": True},
            {"time": self.example_weekend_bad_time, "expected": False},
            {"time": self.example_weekend_good_time, "expected": True},
        ]
        for test in tests:
            jupiter_obj = Jupiter(event=None, context=None)
            mock_datetime.return_value = test.get("time")
            expected = test.get("expected")
            returned = jupiter_obj._check_notification_time()
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.get_boolean')
    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.Jupiter._check_failure')
    @patch('watchmen.process.jupiter.Jupiter._check_notification_time')
    @patch('watchmen.process.jupiter.datetime')
    def test_check_skip_notification(self, mock_datetime, mock_time, mock_last_fail, mock_alarm, mock_boolean):
        jupiter_obj = Jupiter(event=None, context=None)
        success = {
            "last_failed": False,
            "message": "Everything passed",
            "subject": "Happy subject line",
            "success": True,
        }

        failure = {
            "message": "Contains Failures",
            "subject": "Sad subject line",
            "success": False,
        }

        skip_tests = [{
            "use_cal": False, "last_failed": True, "skip": False,
            "expected": failure.get('message'),
        }, {
            "use_cal": True, "last_failed": False, "skip": False,
            "expected": failure.get('message'),
        }, {
            "use_cal": True, "last_failed": True, "skip": False,
            "expected": failure.get('message'),
        }]

        # Success is true
        expected = True, success.get('message')
        returned = jupiter_obj._check_skip_notification_(success)
        self.assertEqual(expected, returned)

        # Cases where alarm is triggered
        for test in skip_tests:
            mock_boolean.return_value = test.get("use_cal")
            mock_last_fail.return_value = test.get("last_failed")
            mock_time.return_value = test.get("skip")
            expected = False, test.get("expected")
            returned = jupiter_obj._check_skip_notification_(failure)
            self.assertEqual(expected, returned)

        # Skip the notify
        mock_boolean.return_value = True
        mock_last_fail.return_value = True
        mock_time.return_value = False
        mock_datetime.now.return_value = self.example_today
        skip_boolean, skip_message = jupiter_obj._check_skip_notification_(self.example_summarized_results)
        # Cannot mock datetime and return result contains exact time to the second
        self.assertIn("Notification is skipped at", skip_message)

    @patch('watchmen.process.jupiter.raise_alarm')
    def test_create_invalid_endpoints_result(self, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        expected = self.example_exception_result
        returned = jupiter_obj._create_invalid_endpoints_result().to_dict()
        returned["dt_created"] = "2018-12-18T00:00:00+00:00"
        returned["dt_updated"] = "2018-12-18T00:00:00+00:00"
        self.assertEqual(expected, returned)

    def test_get_result_parameters(self):
        jupiter_obj = Jupiter(event=None, context=None)
        expected = self.example_result_parameters
        returned = jupiter_obj._get_result_parameters(True)
        self.assertEquals(expected, returned)

    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.json.loads')
    @patch('watchmen.process.jupiter.get_content')
    @patch('watchmen.process.jupiter.settings')
    def test_load_endpoints(self, mock_settings, mock_get_content, mock_loads, mock_alarm):
        jupiter_obj = Jupiter(event=None, context=None)
        # set default endpoints and content
        mock_get_content.return_value = self.example_data

        # load succeeds
        mock_loads.return_value = self.example_valid_paths
        self.assertIsInstance(mock_loads.return_value, list)
        expected_result = self.example_valid_paths
        returned_result = jupiter_obj.load_endpoints()
        self.assertEqual(expected_result, returned_result)

        # load fails
        mock_loads.side_effect = Exception(self.example_exception_message)
        expected = LOCAL_ENDPOINTS
        returned = jupiter_obj.load_endpoints()
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.copy_contents_to_bucket')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_log_result(self, mock_dumps, mock_content):
        jupiter_obj = Jupiter(event=None, context=None)
        mock_dumps.return_value = self.example_results_mix
        results = mock_dumps.return_value
        expected = self.example_prefix
        returned = jupiter_obj.log_result(results)
        self.assertIn(expected, returned)

        # Failed to get contents to s3
        mock_content.side_effect = Exception(self.example_exception_message)
        expected = self.example_prefix
        returned = jupiter_obj.log_result(results)
        self.assertIn(expected, returned)

        # Failed to dump contents
        mock_dumps.side_effect = Exception(self.example_exception_message)
        expected = self.example_prefix
        returned = jupiter_obj.log_result(results)
        self.assertIn(expected, returned)

    @patch('watchmen.process.jupiter.mv_key')
    @patch('watchmen.process.jupiter.copy_contents_to_bucket')
    @patch('watchmen.process.jupiter.json.dumps')
    def test_log_state(self, mock_dumps, mock_content, mock_mv_key):
        jupiter_obj = Jupiter(event=None, context=None)
        mock_dumps.return_value = self.example_summarized_results
        results = mock_dumps.return_value
        mock_content.return_value = True
        self.assertTrue(mock_content.return_value)

        # Failed to get contents to s3
        mock_content.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = jupiter_obj.log_state(results, self.example_prefix)
        self.assertEqual(expected, returned)

        # Failed to dump contents
        mock_dumps.side_effect = Exception(self.example_exception_message)
        expected = None
        returned = jupiter_obj.log_state(results, self.example_prefix)
        self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter.load_endpoints')
    @patch('watchmen.process.jupiter.raise_alarm')
    @patch('watchmen.process.jupiter.ServiceChecker')
    @patch('watchmen.process.jupiter.ServiceChecker.start')
    @patch('watchmen.process.jupiter.Jupiter.log_result')
    @patch('watchmen.process.jupiter.ServiceChecker.get_validated_paths')
    @patch('watchmen.process.jupiter.Jupiter.summarize')
    @patch('watchmen.process.jupiter.Jupiter.log_state')
    @patch('watchmen.process.jupiter.Jupiter._check_skip_notification_')
    def test_monitor(self, mock_skip_notif, mock_log_state, mock_summarize, mock_get_validated_paths, mock_log_result,
                     mock_checker_start, mock_svc_checker, mock_alarm, mock_load_endpoints):
        tests = [
            {"endpoints": self.example_invalid_paths, "expected": self.example_bad_endpoints_result,
             "check_result": None, "details": ""},
            {"endpoints": self.example_valid_paths, "expected": self.example_success_result,
             "check_result": True, "details": SUCCESS_MESSAGE},
            {"endpoints": self.example_valid_paths, "expected": self.example_failure_result,
             "check_result": False, "details": self.example_failure_message}
        ]

        for test in tests:
            jupiter_obj = Jupiter(event=None, context=None)
            endpoints = test.get("endpoints")
            expected = test.get("expected")
            check_result = test.get("check_result")
            details = test.get("details")
            mock_load_endpoints.return_value = endpoints
            mock_skip_notif.return_value = check_result, details
            returned = jupiter_obj.monitor()[0].to_dict()
            returned["dt_created"] = "2018-12-18T00:00:00+00:00"
            returned["dt_updated"] = "2018-12-18T00:00:00+00:00"
            self.assertEqual(expected, returned)

    @patch('watchmen.process.jupiter.Jupiter._check_failure')
    @patch('watchmen.process.jupiter.raise_alarm')
    def test_summarize(self, mock_alarm, mock_fail):
        jupiter_obj = Jupiter(event=None, context=None)
        # Failure setup
        failures = self.example_failed.get('failure')

        failed_message = []
        for item in failures:
            msg = '\tname: {}\n\tpath: {}\n\terror: {}'.format(
                item.get('name'), item.get('path'), item.get('_err')
            )
            failed_message.append(msg)
        failed_message = '{}\n\n\n{}'.format('\n\n'.join(failed_message), CHECK_LOGS)

        first_failure = 's' if len(failures) > 1 else ' - {}'.format(failures[0].get('name'))
        failed_subject = '{}{}'.format(ERROR_SUBJECT, first_failure)

        #  Empty results setup
        empty_message = 'Empty result:\n{}\n{}\nEndpoints:\n{}\n{}\n{}'.format(
            json.dumps(self.example_empty, sort_keys=True, indent=2),
            const.MESSAGE_SEPARATOR,
            json.dumps(self.example_endpoints, indent=2),
            const.MESSAGE_SEPARATOR,
            json.dumps(self.example_validated, indent=2)
        )
        empty_message = "{}\n\n\n{}".format(empty_message, NO_RESULTS)

        test_results = [{
            "results": self.example_no_failures, "last_failed": False, "expected": {
                "message": SUCCESS_MESSAGE, "subject": SUCCESS_SUBJECT, "success": True,
            }
        }, {
            "results": self.example_failed, "last_failed": True, "expected": {
                "last_failed": True, "message": failed_message, "subject": failed_subject, "success": False,
            }
        }, {
            "results": self.example_empty, "last_failed": False, "expected": {
                 "last_failed": False, "message": empty_message, "subject": ERROR_JUPITER, "success": False,
            }
        }]

        for test in test_results:
            mock_fail.return_value = test.get('last_failed')
            results = test.get('results')
            expected = test.get('expected')
            returned = jupiter_obj.summarize(results, self.example_endpoints, self.example_validated)
            self.assertEqual(expected, returned)

        # Results DNE
        results = None
        expected = {
            "last_failed": True, "message": RESULTS_DNE, "subject": ERROR_JUPITER, "success": False,
            }
        mock_fail.return_value = True
        returned = jupiter_obj.summarize(results, None, None)
        self.assertEqual(expected, returned)
