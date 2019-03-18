from datetime import date, timedelta, datetime
from dateutil.easter import easter
import holidays

from watchmen.config import get_boolean
from watchmen.utils.logger import get_logger

LOGGER = get_logger('watchmen.' + __name__)

ADD_HOLIDAY_ERROR = "Holiday cannot be added!"
DATE_ERROR = "Incorrect date formatting!"
DATE_TYPE_ERROR = "The date entered is not of type date. Cannot generate desired information."
REMOVE_HOLIDAY_ERROR = "Holiday cannot be removed!"

HOLIDAY_GOOD_FRIDAY = get_boolean('holiday.good_friday')
HOLIDAY_DAY_B4_XMAS_EVE = get_boolean('holiday.day_b4_xmas_env')

DOW = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]

NOM = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
}


class InfobloxCalendar(object):

    def __init__(self, start=date.today().year, end=None):
        """
        Constructor for watchmen.common.cal.py
        @param start: starting year to generate holidays
        @param end: exclusive ending year to generate holidays
        @note
        There are 3 different constructors:
            1) InfobloxCalendar()
                - This creates a calendar of holidays for the current year
            2) InfobloxCalendar(2020)
                - This creates a calendar for just the given year
            3) InfobloxCalendar(2020, 2090)
                - This creates a calendar for the given range of years (end year exclusive)
        """
        if end is None:
            end = start+1

        self.year_range = list(range(start, end))

        self.holiday_list = holidays.US(state='WA', years=self.year_range, expand=False)
        # Customize holiday list to reflect infoblox holidays
        self._generate_infoblox_holidays()

    def add_holiday(self, year=None, month=None, day=None, name='Custom Infoblox Holiday'):
        """
        Add a custom holiday to the holiday list
        @param year: of new holiday
        @param month: of new holiday
        @param day: of new holiday
        @param name: of new holiday
        @return: An exception if date attributes are None
        @note if the year of the holiday is outside of the range,
        the calendar will populate all the holidays for that year.
        """
        try:
            new_date = '{}-{}-{}'.format(year, month, day)
            self.holiday_list.append({new_date: name})
        except Exception as e:
            message = "{}\nTrying to add holiday: Year-{} Month-{} Day-{}".format(ADD_HOLIDAY_ERROR, year, month, day)
            LOGGER.error(message)

    def _add_holiday_xmas_eve(self):
        """
        Add Christmas Eve to holiday list
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Christmas Day":
                eve = key - timedelta(days=1)
                self.add_holiday(eve.year, eve.month, eve.day, "Christmas Eve")

    def _add_holiday_day_b4_xmas_eve(self):
        """
        Add the Day before Christmas Eve to the holiday list
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Christmas Eve":
                if value.weekday() == 6:
                    day_before = value - timedelta(days=2)
                else:
                    day_before = value - timedelta(days=1)
                self.add_holiday(day_before.year, day_before.month, day_before.day, "Day Before Christmas Eve")

    def _add_holiday_day_after_thanksgiving(self):
        """
        Add the day after Thanksgiving to the holiday list
        """
        for key, value in dict(self.holiday_list).items():
            if value == "Thanksgiving":
                next_day = key + timedelta(days=1)
                self.add_holiday(next_day.year, next_day.month, next_day.day, "Day After Thanksgiving (Black Friday)")

    def _add_holiday_good_friday(self):
        """
        Add Good Friday to the holiday list
        @return:
        """
        for year in self.year_range:
            good_friday = easter(year) - timedelta(days=2)
            self.add_holiday(good_friday.year, good_friday.month, good_friday.day, "Good Friday")

    def _add_holiday_slowdown(self):
        """
        Add the Holiday Slowdown to the holiday list.
        Holiday Slowdown are the following dates: Dec. 26th-31st
        """
        for year in self.year_range:
            d = 26
            while d <= 31:
                self.add_holiday(year, 12, d, "Holiday Slowdown")
                d = d+1

    @staticmethod
    def _find_weekday(self, date_to_check):
        """
        Finds which day of the week the given date is
        @param date_to_check:
        @return: int value corresponding with the correct day of the week
        """
        if not isinstance(date_to_check, date):
            LOGGER.error(DATE_TYPE_ERROR)
            return None
        return DOW[date_to_check.weekday()]

    def _generate_infoblox_holidays(self):
        """
        Populates holiday list with Infoblox specific holidays and removes holidays that are not days off
        ADD: Day after Thanksgiving, Christmas Eve,and Holiday Slowdown (week of Christmas)
        REMOVE: MLK Day and Veteran's Day
        DEPENDENT: Good Friday and the Day before Christmas Eve
        @param year_range: years to add/remove holidays
        @note Some years, Good Friday is not an Infoblox holiday
        """
        not_holidays = ["Martin Luther King, Jr. Day", "Veterans Day"]

        # remove holidays that are still work days
        self.remove_holiday(names=not_holidays)

        # add infoblox specific holidays
        if HOLIDAY_GOOD_FRIDAY:
            self._add_holiday_good_friday()
        self._add_holiday_day_after_thanksgiving()
        self._add_holiday_slowdown()
        self._add_holiday_xmas_eve()
        if HOLIDAY_DAY_B4_XMAS_EVE:
            self._add_holiday_day_b4_xmas_eve()

    def _get_month(self, date_to_check):
        """
        Get the numeric value of the month for a given date
        @param date_to_check:
        @return: the numeric month
        """
        if not isinstance(date_to_check, date):
            LOGGER.error(DATE_TYPE_ERROR)
            return None

        return NOM.get(date_to_check.month)

    def _is_weekend(self, day):
        """
        Determines if given day is a weekend day based on its weekday number.
        5 and 6 represent Saturday and Sunday. 0-4 are Mon-Fri.
        @param day: to be checked
        @return: whether or not the given day is a weekend day or not
        """
        week_num = day.weekday()
        if week_num < 5:
            return False
        return True

    def is_workday(self, year=date.today().year, month=date.today().month, day=date.today().day):
        """
        Determines if the given day is a work day
        @param year: given year or today's year by default
        @param month: given month or today's month by default
        @param day: given day or today's day by default
        @return: whether or not the given day is a work day
        """
        # has to be input with year-month-day style
        # if not holiday or weekend, return true
        try:
            if year is None or month is None or day is None:
                date_to_check = date.today()
            else:
                date_to_check = date(year, month, day)
        except Exception as e:
            message = "{}\nTrying to check : Year-{} Month-{} Day-{}".format(DATE_ERROR, year, month, day)
            LOGGER.error(message)
            return None

        if self._is_weekend(date_to_check) or (date_to_check in self.holiday_list):
            return False
        return True

    @staticmethod
    def is_workhour(hour=datetime.now().hour):
        """
        Determines if given hour is between 6am and 6pm; considered work hours
        @param hour: to be checked
        @return: Whether or not the hour falls between 6am and 6pm
        """
        if 6 <= hour < 18:
            return True
        return False

    def print_holidays(self):
        """
        Print all the holidays in the list.

        Should print in the order:
            ```
            ***********Current Year***********
            Day of the Week, Month Day Year: Name of Holiday
            ```

        Example:
            ```
            --------2020--------
            Wednesday, January 1 2020: New Year's Day
            Monday, February 17 2020: Washington's Birthday
            Friday, April 10 2020: Good Friday
            Monday, May 25 2020: Memorial Day
            ...
            ```
        """
        year = None
        for date, name in sorted(self.holiday_list.items()):
            day_of_week = InfobloxCalendar._find_weekday(self, date)
            month_name = self._get_month(date)
            if year != date.year:
                year = date.year
                print('\n--------{}--------'.format(date.year))

            print('{}, {} {} {}: {}'.format(day_of_week, month_name, date.day, date.year, name))

    def remove_holiday(self, year=None, month=None, day=None, names=None):
        """
        Remove the given date from holiday list or all holidays with the given name(s) from the holiday list
        @param year: of date to be removed
        @param month: of date to be removed
        @param day: of date to be removed
        @param names: single holiday name or list of holiday names that are to be deleted
        """
        if isinstance(names, list):
            for key, value in dict(self.holiday_list).items():
                if value in names:
                    del self.holiday_list[key]
                    LOGGER.info('{} has been removed'.format(value))
            return

        if isinstance(names, str):
            for key, value in dict(self.holiday_list).items():
                if value == names:
                    del self.holiday_list[key]
            LOGGER.info('{} has been removed'.format(names))
            return

        try:
            new_date = '{}-{}-{}'.format(year, month, day)
            removed_date = self.holiday_list.pop(new_date)
            LOGGER.info('{} has been removed'.format(removed_date))
        except Exception as e:
            message = "{}\nTrying to remove holiday: Year-{} Month-{} Day-{}".format(REMOVE_HOLIDAY_ERROR, year, month, day)
            LOGGER.error(message)

    def main(self):
        print("TEST")



if __name__ == "__main__":
    cal = InfobloxCalendar(2017, 2026)
    print HOLIDAY_DAY_B4_XMAS_EVE
