# -*- coding: utf-8 -*-
import time
from datetime import datetime


class Time_Not_valid(Exception):
    def __init__(self, message, info=''):
        Exception.__init__(self, message, info)
        self.message = message
        self.statusinfo = info


def str_day_add(month):
    """
    根据月份填写结束日期
    :param month:
    :return:
    """
    if month in [1, 3, 5, 7, 8, 10, 12]:
        result = '31'
    elif month in [4, 6, 9, 11]:
        result = '30'
    else:
        result = '01'
    return result


def english_transform(str):
    """
    将英文的月份表达转换成数字类型
    :param str:月份英文表达
    :return:月份数字表达
    """
    month = str
    if month == 'dec' or month == 'dec.' or month == 'december':
        month = '12'
    elif month == 'nov' or month == 'nov.' or month == 'november':
        month = '11'
    elif month == 'oct' or month == 'oct.' or month == 'october':
        month = '10'
    elif month == 'sep' or month == 'sep.' or month == 'september':
        month = '09'
    elif month == 'aug' or month == 'aug.' or month == 'august':
        month = '08'
    elif month == 'jul' or month == 'july' or month == 'jul.':
        month = '07'
    elif month == 'jun' or month == 'jun.' or month == 'june':
        month = '06'
    elif month == 'may' or month == 'may.' or month == 'may':
        month = '05'
    elif month == 'apr' or month == 'apr.' or month == 'april':
        month = '04'
    elif month == 'mar' or month == 'mar.' or month == 'march':
        month = '03'
    elif month == 'feb' or month == 'feb.' or month == 'february':
        month = '02'
    elif month == 'jan' or month == 'jan.' or month == 'january':
        month = '01'
    return month


def season_type_check(db_season, cal_season):
    if db_season == 'HY':
        db_season = 'Q2'
    if cal_season == 'HY':
        cal_season = 'Q2'
    if db_season != cal_season:
        raise Time_Not_valid('season_db_error', cal_season)


def is_valid_date(head_text, times):
    """判断是否是一个有效的日期字符串"""
    cur_year = datetime.now().year
    for t in times:
        if t in ('', '0000-00-00') or t is None:
            continue

        try:
            t = time.strptime(t, "%Y-%m-%d")
        except:
            raise Time_Not_valid('WrongTimeString')

        if not 1950 < int(t.tm_year) <= int(cur_year):
            raise Time_Not_valid('YearNotValid', head_text)


def recongnize_current(table_box):
    for table in table_box:
        time_ends = set()
        for header in table['header_list']:
            if header['time_end']:
                time_ends.add(header['time_end'])
        time_ends = list(time_ends)
        time_ends = sorted(time_ends, key=lambda x: datetime.strptime(x, '%Y-%m-%d'), reverse=True)

        if len(time_ends) == 1:
            for header in table['header_list']:
                if header['time_end']:
                    header['is_current'] = '1'
                else:
                    header['is_current'] = '0'
        else:
            for header in table['header_list']:
                if header['time_end']:
                    if header['time_end'] == time_ends[0]:
                        header['is_current'] = '1'
                    else:
                        header['is_current'] = '-1'
                else:
                    header['is_current'] = '0'


def cmp_datetime(a, b):
    a_datetime = datetime.strptime(a, '%Y-%m-%d %H:%M:%S')
    b_datetime = datetime.strptime(b, '%Y-%m-%d %H:%M:%S')

    if a_datetime > b_datetime:
        return -1
    elif a_datetime < b_datetime:
        return 1
    else:
        return 0