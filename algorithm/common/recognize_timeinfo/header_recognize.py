# -*- coding: utf-8 -*-
import re

from algorithm.common.recognize_timeinfo import time_info, special_process_hkg, special_process_usa
from algorithm.common.recognize_timeinfo.time_standardization import english_transform, str_day_add


def time_match(regex, str):
    """
    时间匹配
    :param regex: 匹配的正则表达式
    :param str: 需要匹配的文本行
    :return: 匹配结果
    """
    match_result = re.search(regex, str)
    return match_result


def date_dispose(time_str, table_type, country):
    """
    输入字符串，返回时间对象
    :param time_str: 字符串
    :param table_type: 表类型
    :return:
    """
    result = time_info.Time()
    str = time_str.replace(' ', '').replace('#|#', ',').lower()
    str = re.sub(' ', '', str)

    # 匹配时间段和报表类型
    if 'half-year' in str or 'six-monthended' in str or '6monthended' in str or 'sixmonthended' in str or 'q2' in str or '2quarter' in str or '2ndquarter' in str or 'secondquarter' in str or 'sixmonthsended' in str:
        result.time_quarter = 'Q2'
        result.time_length = '6'
    elif '3-monthended' in str or '3monthended' in str or 'three-monthended' in str or 'q1' in str or '1quarter' in str or '1stquarter' in str or 'firstquarter' in str or 'threemonthsended' in str:
        result.time_quarter = 'Q1'
        result.time_length = '3'
    elif '9-month' in str or 'nine-monthended' in str or '9monthended' in str or 'q3' in str or '3quarter' in str or '3rdquarter' in str or 'thirdquarter' in str or 'ninemonthsended' in str:
        result.time_quarter = 'Q3'
        result.time_length = '9'
    elif 'theyearended' in str or 'annual' in str:
        result.time_quarter = 'FY'
        result.time_length = '12'

    if country == 'HKG':
        special_result = special_process_hkg.hkg_header_recognize(str, result.time_quarter, result.time_length, table_type)
        if special_result:
            return special_result

    if country == 'USA':
        special_result = special_process_usa.usa_recognize(str, result.time_quarter, result.time_length)
        if special_result:
            return special_result


    # 时间范围格式的匹配
    regex_range1 = r'([1|2][0|9]\d{2})[/-]([1|2][0|9]\d{2})'
    regex_range2 = r'[1|2][0|9]\d{2}-[0|1]{1}\d{1}'
    range_regex = [regex_range1, regex_range2]

    # 日月年的匹配(31-12-2018)
    # 月日年的格式根据日期的大小和关键字转换格式
    regex1 = r'(\d{1,2})-(\d{1,2})-([1|2][0|9]\d{2})'
    regex2 = r'(\d{1,2})/(\d{1,2})/([1|2][0|9]\d{2})'
    regex3 = r'(\d{1,2})[\.](\d{1,2})[\.]([1|2][0|9]\d{2})'
    regex4 = r'(\d{1,2})\s(\d{1,2})\s([1|2][0|9]\d{2})'
    number_list = [regex1, regex2, regex3, regex4]

    # 年月日的格式匹配(2018-12-31)
    regex_asc1 = r'((19|20)\d{2})[\.](\d{1,2})[\.](\d{1,2})'
    regex_asc2 = r'((19|20)\d{2})/(\d{1,2})/(\d{1,2})'
    regex_asc3 = r'((19|20)\d{2})-(\d{1,2})-(\d{1,2})'
    regex_asc4 = r'((19|20)\d{2}),(\d{1,2}),(\d{1,2})'
    regex_asc5 = r'((19|20)\d{2})\s(\d{1,2})\s(\d{1,2})'
    asc_regex = [regex_asc1, regex_asc2, regex_asc3, regex_asc4, regex_asc5]

    # 月份格式匹配
    regex_month_1 = r'(january|jan)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_2 = r'(february|feb)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_3 = r'(march|mar)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_4 = r'(april|apr)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_5 = r'(may)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_6 = r'(june|jun)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_7 = r'(july|jul)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_8 = r'(august|aug)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_9 = r'(september|sep)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_10 = r'(october|oct)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_11 = r'(november|nov)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    regex_month_12 = r'(december|dec)[\s\./,-]*(\d{1,2})[dhnrst]*[\s\./,-]*([1|2][0|9]\d{2})'
    month_list = [regex_month_1, regex_month_2, regex_month_3, regex_month_4, regex_month_5, regex_month_6,
                  regex_month_7, regex_month_8, regex_month_9, regex_month_10, regex_month_11, regex_month_12]

    regex_month_desc_1 = r'(\d{1,2})[dhnrst]*[\./,-]*(january|jan)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_2 = r'(\d{1,2})[dhnrst]*[\./,-]*(february|feb)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_3 = r'(\d{1,2})[dhnrst]*[\./,-]*(march|mar)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_4 = r'(\d{1,2})[dhnrst]*[\./,-]*(april|apr)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_5 = r'(\d{1,2})[dhnrst]*[\./,-]*(may)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_6 = r'(\d{1,2})[dhnrst]*[\./,-]*(june|jun)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_7 = r'(\d{1,2})[dhnrst]*[\./,-]*(july|july)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_8 = r'(\d{1,2})[dhnrst]*[\./,-]*(august|aug)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_9 = r'(\d{1,2})[dhnrst]*[\./,-]*(september|sep)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_10 = r'(\d{1,2})[dhnrst]*[\./,-]*(october|oct)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_11 = r'(\d{1,2})[dhnrst]*[\./,-]*(november|nov)[\./,-]*[\s]*([1|2][0|9]\d{2})'
    regex_month_desc_12 = r'(\d{1,2})[dhnrst]*[\./,-]*(december|dec)[\./,-]*[\s]*([1|2][0|9]\d{2})'

    month_list_2 = [regex_month_desc_1, regex_month_desc_2, regex_month_desc_3, regex_month_desc_4, regex_month_desc_5,
                    regex_month_desc_6, regex_month_desc_7, regex_month_desc_8, regex_month_desc_9, regex_month_desc_10,
                    regex_month_desc_11, regex_month_desc_12]

    regex_quarter1 = r'([1|2|3|4]{1})[dhnrst]*\squarter\s[of\s]*([1|2][0|9]\d{2})'
    regex_quarter2 = r'(first)\squarter\s[of\s]*([1|2][0|9]\d{2})'
    regex_quarter3 = r'(second)\squarter\s[of\s]*([1|2][0|9]\d{2})'
    regex_quarter4 = r'(third)\squarter\s[of\s]*([1|2][0|9]\d{2})'
    regex_quarter5 = r'(forth)\squarter\s[of\s]*([1|2][0|9]\d{2})'
    regex_quarter6 = r'(end)\squarter\s[of\s]*([1|2][0|9]\d{2})'
    quarter_regex = [regex_quarter1, regex_quarter2, regex_quarter3, regex_quarter4, regex_quarter5, regex_quarter6]

    regex_month_year1 = r'(january|jan)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year2 = r'(february|feb)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year3 = r'(march|mar)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year4 = r'(april|apr)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year5 = r'(may|may)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year6 = r'(june|jun)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year7 = r'(july|jul)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year8 = r'(august|aug)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year9 = r'(september|sep)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year10 = r'(october|oct)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year11 = r'(november|nov)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    regex_month_year12 = r'(december|dec)[dhnrst]*[\s,]*([1|2][0|9]\d{2})'
    month_year_regex = [regex_month_year1, regex_month_year2, regex_month_year3, regex_month_year4, regex_month_year5,
                        regex_month_year6, regex_month_year7, regex_month_year8, regex_month_year9, regex_month_year10,
                        regex_month_year11, regex_month_year12]

    regex_special1 = r'from(.{5,})to(.+)'
    regex_special2 = r'fortheperiod^ended&*(.{5,})to(.+)'
    regex_special3 = r'((\d{2})[\.](\d{2})[\.]([1|2][0|9]\d{2}))-((\d{2})[\.](\d{2})[\.]([1|2][0|9]\d{2}))'
    regex_special9 = r'((\d{2})[年](\d{2})[月]([1|2][0|9]\d{2}))[日]-(()(\d{2})[月]([1|2][0|9]\d{2})[日])'
    regex_special4 = r'(currentyear|previousyear|currentperiod|priorperiod|closingbalance|openingbalance)'
    regex_special5_BS = r'(当期|本期|期末|年末|本年)'
    regex_special6_BS = r'(上期|上年|期初|上年年初|年初余额|年初数|年初金额)'
    regex_special7 = r'(当期|本期|期末|年末|本年)'
    regex_special8 = r'(上期|期初|上年年初|上年同期|上年)'
    special_regex = [regex_special1, regex_special2, regex_special3, regex_special4, regex_special9]

    special_regex_chinese_BS = [regex_special6_BS, regex_special5_BS]
    special_regex_chinese = [regex_special8, regex_special7]

    regex_chinese1 = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
    regex_chinese2 = r'(\d{4})年(\d{1,2})月'
    chinese_regex = [regex_chinese1, regex_chinese2]

    regex_chinese_range1 = r'(\d{4})年(\d{1,2})-(\d{1,2})月'
    regex_chinese_range2 = r'(\d{4})年(\d{1,2})月(\d{1,2})日至(\d{4})年(\d{1,2})月(\d{1,2})日'
    chinese_range_regex = [regex_chinese_range1, regex_chinese_range2]

    # regex_chinese_month_range1 = r'(\d{1,2})-(\d{1,2})月'
    # chinese_month_range_regex = [regex_chinese_month_range1]

    # 匹配中文特殊表达
    if result.time_type is None:
        if table_type == 'BS':
            for regex in special_regex_chinese_BS:
                match_result = time_match(regex, str)
                if match_result is not None:
                    if regex == regex_special6_BS:
                        result.time_type = 12
                        result.time_str = str
                        result.time_format = match_result.group(0)
                        break
                    elif regex == regex_special5_BS:
                        result.time_type = 11
                        result.time_str = str
                        result.time_format = match_result.group(0)
                        break
        else:
            for regex in special_regex_chinese:
                match_result = time_match(regex, str)
                if match_result is not None:
                    if regex == regex_special8:
                        result.time_type = 12
                        result.time_str = str
                        result.time_format = match_result.group(0)
                        break
                    elif regex == regex_special7:
                        result.time_type = 11
                        result.time_str = str
                        result.time_format = match_result.group(0)
                        break

    # 匹配特殊表达
    if result.time_type is None:
        for regex in special_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                if regex == regex_special1 or regex == regex_special2:
                    begin = match_result.group(1)
                    end = match_result.group(2)
                    if date_dispose(begin, table_type, country) is not None and date_dispose(end, table_type, country) is not None:
                        end_str = date_dispose(end, table_type, country).time_str
                        if date_dispose(begin, table_type, country) is None:
                            begin = '{}{}'.format(begin, end_str[0:4])
                        result.time_type = 4
                        result.time_str = date_dispose(begin, table_type, country).time_str + ' to ' + end_str
                        result.time_begin = date_dispose(begin, table_type, country).time_str
                        result.time_end = end_str
                        result.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
                        break
                elif regex == regex_special3:
                    result.time_type = 4
                    result.time_begin = date_dispose(match_result.group(1), table_type, country).time_str
                    result.time_end = date_dispose(match_result.group(5), table_type, country).time_str
                    result.time_str = result.time_begin + ' to ' +result.time_end
                    result.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
                    break
                elif regex == regex_special4:
                    result.time_type = 10
                    result.time_str = match_result.group(0)
                    result.time_quarter = 'FY'
                    result.time_length = 12
                    result.time_format = 'special_express'
                    break
                elif regex == regex_special6_BS:
                    result.time_type = 12
                    result.time_str = str
                    result.time_format = match_result.group(0)
                    break
                elif regex == regex_special5_BS:
                    result.time_type = 11
                    result.time_str = str
                    result.time_format = match_result.group(0)
                    break

    # 匹配特殊表达(月日年)的日期
    if result.time_type is None:
        for regex in month_list:
            match_result = time_match(regex, str)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(3)
                month = match_result.group(1)
                day = match_result.group(2)
                if len(day) == 1:
                    day = '0{}'.format(day)
                result.time_str = '{}-{}-{}'.format(year, english_transform(month), day)
                result.time_format = 'yyyy-mm-dd'
                break

    # chinese range
    if result.time_type is None:
        for regex in chinese_range_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                if regex == regex_chinese_range1:
                    result.time_type = 4
                    year = match_result.group(1)
                    month1 = match_result.group(2)
                    month2 = match_result.group(3)
                    result.time_begin = '{}-{}-01'.format(year, month1)
                    result.time_end = '{}-{}-{}'.format(year, month2, str_day_add(int(month2)))
                    result.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
                    break
                elif regex == regex_chinese_range2:
                    result.time_type = 4
                    year = match_result.group(1)
                    month1 = match_result.group(2)
                    month2 = match_result.group(5)
                    result.time_begin = '{}-{}-01'.format(year, month1)
                    result.time_end = '{}-{}-{}'.format(year, month2, str_day_add(int(month2)))
                    result.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
                    break

    # 匹配特殊表达(日月年)的日期
    if result.time_type is None:
        for regex in month_list_2:
            match_result = time_match(regex, str)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(3)
                month = match_result.group(2)
                day = match_result.group(1)
                if len(day) == 1:
                    day = '0{}'.format(day)
                result.time_str = '{}-{}-{}'.format(year, english_transform(month), day)
                result.time_format = 'yyyy-mm-dd'
                break

    # 中文年月日/年月表达
    if result.time_type is None:
        for regex in chinese_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                if regex == regex_chinese1:
                    result.time_type = 1
                    year = match_result.group(1)
                    month = match_result.group(2)
                    day = match_result.group(3)
                    result.time_str = '{}-{}-{}'.format(year, month, day)
                    result.time_format = 'yyyy-mm-dd'
                    break
                elif regex == regex_chinese2:
                    result.time_type = 2
                    year = match_result.group(1)
                    month = match_result.group(2)
                    result.time_str = '{}-{}'.format(year, month)
                    result.time_format = 'yyyy-mm'
                    break

    # 匹配日月年格式表达
    if result.time_type is None:
        for regex in number_list:
            match_result = time_match(regex, str)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(3)
                month = match_result.group(2)
                day = match_result.group(1)
                if int(month) > 12:
                    month, day = day, month
                result.time_str = '{}-{}-{}'.format(year, month, day)
                result.time_format = 'yyyy-mm-dd'
                break

    # 匹配年月日格式表达
    if result.time_type is None:
        for regex in asc_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                result.time_type = 1
                year = match_result.group(1)
                month = match_result.group(3)
                day = match_result.group(4)
                result.time_str = '{}-{}-{}'.format(year, month, day)
                result.time_format = 'yyyy-mm-dd'
                break

    # 最后匹配范围格式的日期
    if result.time_type is None:
        for regex in range_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                result.time_type = 5
                r = match_result.group(0)
                if regex == regex_range2:
                    result.time_type = 5
                    if 'annual' in str.lower():
                        result.time_begin = r[:4]
                        result.time_end = '{}{}'.format('20', r[-2:])
                        result.time_format = 'yyyy-yyyy'
                    elif r[5:7] > '12':
                        result.time_begin = r[:4]
                        result.time_end = '{}{}'.format('20', r[-2:])
                        result.time_format = 'yyyy-yyyy'
                    else:
                        result.time_type = 3
                        result.time_str = '{}{}'.format('20', match_result.group(0)[-2:])
                        result.time_format = 'yyyy'
                # elif regex == regex_range3:
                #     result = '{}-{}-{}'.format(match_result.group(3), match_result.group(4), day)
                else:
                    result.time_begin = match_result.group(1)
                    result.time_end = match_result.group(2)
                    result.time_str = '{}'.format(r.replace('/', '-').replace(' ', ''))
                    result.time_format = 'yyyy-yyyy'
                break

    # 年月匹配
    if result is None:
        for regex in month_year_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                month = english_transform(match_result.group(1))
                year = match_result.group(2)
                result = '{}-{}'.format(year, month)
                break



    # 季度匹配
    if result.time_type is None:
        for regex in quarter_regex:
            match_result = time_match(regex, str)
            if match_result is not None:
                result.time_type = 5
                quarter = match_result.group(1)
                year = match_result.group(2)
                if quarter == '1' or quarter == 'first':
                    quarter = 'Q1'
                    month = '3'
                elif quarter == '2' or quarter == 'second':
                    quarter = 'Q2'
                    month = '6'
                elif quarter == '3' or quarter == 'third':
                    quarter = 'Q3'
                    month = '9'
                elif quarter == '4' or quarter == 'forth' or quarter == 'end':
                    quarter = 'Q4'
                    month = '12'
                result.time_str = match_result.group(2)
                result.time_quarter = quarter
                result.time_length = month
                result.time_format = 'yyyy'

    # # 月份范围匹配
    # if result.time_type is None:
    #     for regex in chinese_month_range_regex:
    #         match_result = time_match(regex, str)
    #         if match_result is not None:
    #             result.time_type = 7
    #             month1 = match_result.group(1)
    #             month2 = match_result.group(2)
    #             result.time_begin = '{}-{}'.format(month1, '01')
    #             result.time_end = '{}-{}'.format(month2, str_day_add(int(month2)))
    #             result.time_format = 'mm-dd to mm-dd'

    # 纯年份匹配
    if result.time_type is None:
        regex = r'(19|20)(\d{2})'
        match_result = time_match(regex, str)
        if match_result is not None:
            result.time_type = 3
            result.time_str = match_result.group(0)
            result.time_format = 'yyyy'
            import datetime
            if int(result.time_str) > int(datetime.datetime.now().year):
                result = None



    if result.time_type is not None:
        return result
