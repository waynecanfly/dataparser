# -*- coding:utf-8 -*-
import re

from algorithm.common.recognize_timeinfo import time_info


def chn_title_recognize(str):
    """
    中国时间,标题需要首先按照特殊方式来识别,
    即:如果能识别出年度和季度确定的文字,如2017年度第二季度报告,
    就能确定中国的时间
    否则,使用时间识别模块
    :return:
    """
    regex_first = [
        r'(20\d{2})年第一季度'
    ]
    regex_second = [
        r'(20\d{2})年第二季度',
        r'(20\d{2})年半年度',
        r'(20\d{2})半年度'
    ]
    regex_third = [
        r'(20\d{2})年第三季度'
    ]
    regex_forth = [
        r'(20\d{2})年第四季度',
        r'(20\d{2})年年度',
        r'(20\d{2})年度'
    ]
    title = str.replace(' ', '')
    result = time_info.Time()
    if result.time_type is None:
        for regex in regex_first:
            match_result = re.search(regex, title)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(1)
                month = '03'
                day = '31'
                result.time_quarter = 'Q1'
                result.time_str = '{}-{}-{}'.format(year, month, day)
                result.time_format = 'yyyy-mm-dd'
                break

    if result.time_type is None:
        for regex in regex_first:
            match_result = re.search(regex, title)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(1)
                month = '06'
                day = '30'
                result.time_quarter = 'Q2'
                result.time_str = '{}-{}-{}'.format(year, month, day)
                result.time_format = 'yyyy-mm-dd'
                break

    if result.time_type is None:
        for regex in regex_third:
            match_result = re.search(regex, title)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(1)
                month = '09'
                day = '30'
                result.time_quarter = 'Q3'
                result.time_str = '{}-{}-{}'.format(year, month, day)
                result.time_format = 'yyyy-mm-dd'
                break

    if result.time_type is None:
        for regex in regex_forth:
            match_result = re.search(regex, title)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(1)
                month = '12'
                day = '31'
                result.time_quarter = 'FY'
                result.time_str = '{}-{}-{}'.format(year, month, day)
                result.time_format = 'yyyy-mm-dd'
                break
    return result


def chn_season_type_recognize(str):
    """
    recognize season_type specially for china
    :return:
    """
    season_type = None
    if '第一季度' in str:
        season_type = 'Q1'
    elif '第二季度' in str:
        season_type = 'Q2'
    elif '半年度' in str:
        season_type = 'Q2'
    elif '第三季度' in str:
        season_type = 'Q3'
    elif '年度报告' in str:
        season_type = 'FY'

    return season_type


def chn_special_title_recognize(country, table):
    # 中国特殊处理
    if country == 'CHN':
        if table["table_type"] != 'BS':
            regex_special1 = r'(年初到报告期末)'
            regex_special = [regex_special1]
            title = table["title_text"]
            title = re.sub('\s', '', title)
            for regex in regex_special:
                match_result = re.search(regex, title)
                if match_result is not None:
                    # 匹配到了特殊格式的表头,header中无法确定月份
                    for header in table["header_list"]:
                        year = header["time_begin"].split('-')[0]
                        if year != '':
                            header["time_begin"] = '{}-01-01'.format(year)


