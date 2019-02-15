# -*- coding:utf-8 -*-
import re

from algorithm.common.recognize_timeinfo import time_info

month2digit = {
        'january': '01',
        'february': '02',
        'march': '03',
        'april': '04',
        'may': '05',
        'june': '06',
        'july': '07',
        'august': '08',
        'september': '09',
        'october': '10',
        'november': '11',
        'december': '12',
        'jan': '01',
        'feb': '02',
        'mar': '03',
        'apr': '04',
        'jun': '06',
        'jul': '07',
        'aug': '08',
        'sept': '09',
        'oct': '10',
        'nov': '11',
        'dec': '12',
    }

month_regex = '(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|oct|nov|dec)'


def usa_recognize(str, time_quarter, time_length):

    result = time_info.Time()

    # 匹配时间段和报表类型
    if re.findall('half-year|six-monthended|six-monthsended|6monthended|sixmonthended|q2|2quarter|2ndquarter|secondquarter|sixmonthsended|halfyear|半年', str):
        result.time_quarter = 'Q2'
        result.time_length = '6'
    elif re.findall('(9-month|nine-monthended|9monthended|q3|3quarter|3rdquarter|thirdquarter|ninemonthsended|nine-month)', str):
        result.time_quarter = 'Q3'
        result.time_length = '9'
    elif re.findall('(3-monthended|3monthended|three-monthended|q1|1quarter|1stquarter|firstquarter|threemonthended|quarter|季度|three-month|threemonthsended)', str):
        result.time_quarter = 'Q1'
        result.time_length = '3'
    elif re.findall('(theyearended|annual|twelvemonthsended)', str):
        result.time_quarter = 'FY'
        result.time_length = '12'

    year = None
    month = None
    day = None
    is_find = False

    start_year, start_month, start_day = None, None, None
    # 时间段
    range_result = re.findall('{month}(\d+),(20[0-1][0-9]).*(to|through){month}(\d+),(20[0-1][0-9])'.format(month=month_regex), str)
    if range_result:
        start_day = range_result[-1][1]
        start_month = range_result[-1][0]
        start_year = range_result[-1][2]
        day = range_result[-1][5]
        month = range_result[-1][4]
        year = range_result[-1][6]

        start_month = month2digit[start_month]
        month = month2digit[month]
        is_find = True


    # 31-Dec-15
    if not is_find:
        time_result = re.findall('(\d{count})-{month}-(\d{count})'.format(month=month_regex, count='{2}'), str)
        if time_result:
            day = time_result[-1][0]
            month = time_result[-1][1]
            month = month2digit[month]
            year = time_result[-1][2]
            year = '20' + year
            is_find = True

    # December 31 2107
    if not is_find:
        mm_dd_yyyy = [
            "{month}(\d{count})(20[0-1][0-9])".format(month=month_regex, count='{1,2}'),
            "{month}(\d{count}),(20[0-1][0-9])and(20[0-1][0-9])".format(month=month_regex, count='{1,2}'),
        ]
        for regex in mm_dd_yyyy:
            time_result = re.findall(regex, str)
            if time_result:
                month = time_result[-1][0]
                month = month2digit[month]
                day = time_result[-1][1]
                year = time_result[-1][2]
                is_find = True
                break

    # December 31
    if not is_find:
        month_day__result = re.findall('{month}(\d+)'.format(month=month_regex), str)
        if month_day__result:
            month = month_day__result[-1][0]
            month = month2digit[month]
            day = month_day__result[-1][1]



    if not is_find:
        year_result = re.findall('20[0-1][0-9]', str)
        if year_result:
            year = year_result[-1]

    if day:
        day = '0' + day if len(day) == 1 else day

    if time_length and time_quarter and not result.time_length and not result.time_length:
        result.time_length = time_length
        result.time_quarter = time_quarter

    if start_day and start_month and start_year:
        result.time_begin = start_year + '-' + start_month + '-' + start_day

    if year and month and day:
        result.time_str = year + '-' + month + '-' + day
        result.time_end = result.time_str

    if result.time_begin and result.time_end:
        result.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
        result.time_type = 4
        return result
    elif result.time_end:
        result.time_format = 'yyyy-mm-dd'
        result.time_type = 1
        return result

    if month and day:
        result.time_str = month + '-' + day
        result.time_end = result.time_str
        result.time_format = 'mm-dd'
        result.time_type = 6
        return result

    return None


