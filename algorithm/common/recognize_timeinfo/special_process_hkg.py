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
}
month_regex = '(january|february|march|april|may|june|july|august|september|october|november|december)'

def hkg_title_recognize(str, time_quarter, time_length):
    result = time_info.Time()
    # 匹配时间段和报表类型
    result = recongnize_quarter(str)

    day = re.findall('(ended|asat)(\d*)', str)
    day = day[-1][1] if day else None
    if day:
        day = day if len(day) == 2 else '0' + day

    month = re.findall(month_regex, str)
    month = month2digit.get(month[-1]) if month else None

    year = re.findall('20[0-1][0-9]', str)
    year = year[-1] if year else None

    # 中文转换
    if year is None or day is None or month is None:
        str = re.sub('二十九', '29', str)
        str = re.sub('三十一', '31', str)
        str = re.sub('十二', '12', str)
        str = re.sub('十一', '11', str)
        # str = re.sub('十', '0', str)
        str = re.sub('零', '0', str)
        str = re.sub('一', '1', str)
        str = re.sub('二', '2', str)
        str = re.sub('三', '3', str)
        str = re.sub('四', '4', str)
        str = re.sub('五', '5', str)
        str = re.sub('六', '6', str)
        str = re.sub('七', '7', str)
        str = re.sub('八', '8', str)
        str = re.sub('九', '9', str)
        if not year:
            year = re.findall('20[0-1][0-9]', str)
            year = year[-1] if year else None
        if not day:
            day = re.findall('月(\d+)日', str)
            day = day[-1] if day else None

        if not month:
            month = re.findall('(\d)月', str)
            month = month[-1] if month else None

    time_result = re.findall(
        'ended{month}(\d+)'.format(month=month_regex), str)
    if time_result:
        day = time_result[-1][1]
        month = time_result[-1][0]
        month = month2digit[month]

    if time_length and time_quarter and not result.time_length and not result.time_length:
        result.time_length = time_length
        result.time_quarter = time_quarter

    if year and month and day:
        result.time_str = year + '-' + month + '-' + day
        result.time_end = result.time_str
        result.time_format = 'yyyy-mm-dd'
        result.time_type = 1
        return result
    elif month and day:
        result.time_str = month + '-' + day
        result.time_format = 'mm-dd'
        result.time_end = month + '-' + day
        result.time_type = 6
        return result
    return None

# 表头时间识别
def hkg_header_recognize(str, time_quarter, time_length, table_type):
    # 匹配时间段和报表类型
    result = recongnize_quarter(str)

    # 变量初始化
    time_start_day = None
    time_start_month = None
    time_start_year = None
    day = None
    month = None
    year = None
    is_find = False

    # 先识别整体规则再识别零散信息
    dd_mm_yyyy_to_dd_mm_yyyy = ['(\d+)\.(\d+)\.(\d+)\.to(\d+)\.(\d+)\.(\d+)',
                                '(\d+){month}(20[0-1][0-9])to(\ +){month}(20[0-1][0-9])'.format(month=month_regex)]
    for regex in dd_mm_yyyy_to_dd_mm_yyyy:
        time_result = re.findall(regex, str)
        if time_result:
            time_start_day = time_result[0][0]
            time_start_month = time_result[0][1]
            time_start_year = time_result[0][2]
            day = time_result[0][3]
            month = time_result[0][4]
            year = time_result[0][5]

            time_start_month = month2digit[time_start_month]
            month = month2digit[month]
            is_find = True
            break

    if not is_find:
        # day-month-year
        dd_mm_yyyy = ['(\d+)\.(\d+)\.(20[0-1][0-9])', '(\d+)/(\d+)/(20[0-1][0-9])']
        for regex in dd_mm_yyyy:
            time_result = re.findall(regex, str)
            if time_result:
                day = time_result[0][0]
                month = time_result[0][1]
                year = time_result[0][2]
                is_find = True
                break

    if not is_find:
        # month-day-year
        mm_dd_yyyy = [
            '{month}(\d+),(20[0-1][0-9])'.format(month=month_regex),
            '{month}(\d{count})(20[0-1][0-9])'.format(month=month_regex, count='{2}')
        ]
        for regex in mm_dd_yyyy:
            time_result = re.findall(regex, str)
            if time_result:
                is_find = True
                day = time_result[0][1]
                month = time_result[0][0]
                month = month2digit[month]
                year = time_result[0][2]

    # year-day-month
    if not is_find:
        time_result = re.findall('(20[0-1][0-9])(\d+){month}'.format(month=month_regex), str)
        if time_result:
            is_find = True
            day = time_result[-1][1]
            month = time_result[-1][2]
            month = month2digit[month]
            year = time_result[-1][0]

    if not is_find:
        # month-day
        time_result = re.findall('ended{month}(\d+)'.format(month=month_regex), str)
        if time_result:
            day = time_result[-1][1]
            month = time_result[-1][0]
            month = month2digit[month]

        if not day:
            # 天识别
            day_regex = ['ended(\d+)', '(\d+)st', 'asat(\d+)', '(\d+)th']
            for regex in day_regex:
                day = re.findall(regex, str)
                if day:
                    day = day[-1]
                    break
            else:
                day = None

        if not day:
            day = re.findall('(\d+){month}'.format(month=month_regex),
                             str)
            day = day[-1][0] if day else None
        if not day:
            day = re.findall(
                'at{month}(\d+)20[0-1][0-9]'.format(month=month_regex),
                str)
            day = day[-1][1] if day else None

        # 月份
        if not month:
            month = re.findall('{month}'.format(month=month_regex), str)
            month = month2digit.get(month[-1]) if month else None

        # 年份
        if not year:
            year = re.findall('20[0-1][0-9]', str)
            year = year[-1] if year else None

    # 中文转换
    if year is None or day is None or month is None:
        str = re.sub('二十九', '29', str)
        str = re.sub('三十一', '31', str)
        str = re.sub('三十', '30', str)
        str = re.sub('十二', '12', str)
        str = re.sub('十一', '11', str)
        # str = re.sub('十', '0', str)
        str = re.sub('零', '0', str)
        str = re.sub('一', '1', str)
        str = re.sub('二', '2', str)
        str = re.sub('三', '3', str)
        str = re.sub('四', '4', str)
        str = re.sub('五', '5', str)
        str = re.sub('六', '6', str)
        str = re.sub('七', '7', str)
        str = re.sub('八', '8', str)
        str = re.sub('九', '9', str)
        if not year:
            year = re.findall('20[0-1][0-9]', str)
            year = year[-1] if year else None
        if not day:
            day = re.findall('月(\d+)日', str)
            day = day[-1] if day else None

        if not month:
            month = re.findall('(\d{1,2})月', str)
            month = month[-1] if month else None


    if day:
        day = day if len(day) == 2 else '0' + day
    if month:
        month = month if len(month) == 2 else '0' + month

    if time_start_day:
        time_start_day = time_start_day if len(time_start_day) == 2 else '0' + time_start_day
    if time_start_month:
        time_start_month = time_start_month if len(time_start_month) == 2 else '0' + time_start_month

    if time_length and time_quarter and not result.time_length and not result.time_length:
        result.time_length = time_length
        result.time_quarter = time_quarter

    if time_start_month and time_start_day and time_start_year:
        result.time_begin = time_start_year + '-' + time_start_month + '-' + time_start_day

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
    elif year and table_type == 'BS':
        if month and day:
            result.time_str = year + '-' + month + '-' + day
            result.time_format = 'yyyy-mm-dd'
            result.time_type = 1
            return result
        else:
            result.time_str = year
            result.time_format = 'yyyy'
            result.time_type = 3
            return result
    elif month and day:
        result.time_str = month + '-' + day
        result.time_format = 'mm-dd'
        result.time_end = month + '-' + day
        result.time_type = 6
        return result
    return None


def recongnize_quarter(str):
    result = time_info.Time()
    if re.findall('(ninemonthsended|nine-month)', str):
        result.time_quarter = 'Q3'
        result.time_length = '9'
    elif re.findall(
            'half-year|six-monthended|6monthended|sixmonthended|q2|2quarter|2ndquarter|secondquarter|sixmonthsended|halfyear|半年|sixmonthsandthreemonthsended',
            str):
        result.time_quarter = 'HY'
        result.time_length = '6'
    elif re.findall('(9-month|nine-monthended|9monthended|q3|3quarter|3rdquarter|thirdquarter)', str):
        result.time_quarter = 'Q3'
        result.time_length = '9'
    elif re.findall(
            '(3-monthended|3monthended|three-monthended|q1|1quarter|1stquarter|firstquarter|threemonthended|quarter|季度|three-month|threemonthsended)',
            str):
        result.time_quarter = 'Q1'
        result.time_length = '3'
    elif re.findall('(theyearended|annual|twelvemonthsended|financialyearended|yearended)', str):
        result.time_quarter = 'FY'
        result.time_length = '12'

    return result