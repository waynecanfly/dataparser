# -*- coding:utf-8 -*-
import re
import time

from algorithm.common.recognize_timeinfo import time_info


def str_day_add(month):
    if month in [1, 3, 5, 7, 8, 10, 12]:
        result = '31'
    elif month in [4, 6, 9, 11]:
        result = '30'
    else:
        result = '01'
    return result


def normalize_title(title, year_global, month_global, day_global):
    """
    将可以转化格式的title统一化,减少出现的种类
    例如:将yyyy-mm格式转换为yyyy-mm-dd格式
    :param title: 传入title对象
    :param year_global: 全局年份
    :param month_global: 全局月份
    :param day_global: 全局日期
    :return:
    """
    if title is None:
        title = time_info.Time()
        if year_global is not None:

            title.time_type = 3
            title.time_str = year_global
            title.time_format = 'yyyy'
            if month_global is not None:
                if day_global is None:
                    day_global = str_day_add(int(month_global))
                title.time_type = 1
                title.time_str = '{}-{}-{}'.format(year_global, month_global, day_global)
                title.time_format = 'yyyy-mm-dd'
    elif title.time_type == 2:
        title_time = title.time_str
        title_time_split = title_time.split('-')
        year = title_time_split[0]
        month = title_time_split[1]
        day = str_day_add(int(month))
        title.time_type = 1
        title.time_str = '{}-{}-{}'.format(year, month, day)
        title.time_format = 'yyyy-mm-dd'
    elif title.time_type == 3:
        if month_global is not None:
            if day_global is None:
                day_global = str_day_add(int(month_global))
            title.time_type = 1
            title.time_str = '{}-{}-{}'.format(title.time_str, month_global, day_global)
            title.time_format = 'yyyy-mm-dd'
    elif title.time_type == 5:
        if month_global is not None:
            if day_global is None:
                day_global = str_day_add(int(month_global))
            title.time_type = 4
            title.time_begin = '{}-{}-{}'.format(title.time_begin, month_global, '01')
            title.time_end = '{}-{}-{}'.format(title.time_end, month_global, day_global)
            title.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
    elif title.time_type == 6:
        if year_global is not None:
            title.time_type = 1
            title.time_str = '{}-{}'.format(year_global, title.time_str)
            title.time_format = 'yyyy-mm-dd'
    elif title.time_type == 7:
        if year_global is not None:
            title.time_type = 4
            title.time_begin = '{}-{}'.format(year_global, title.time_begin)
            title.time_end = '{}-{}'.format(year_global, title.time_end)
            title.time_format = 'yyyy-mm-dd to yyyy-mm-dd'
    return title


def quarter_to_begin(day, month, year, quarter):
    day = '01'
    if quarter == 'Q1':
        if month < 3:
            year -= 1
            month += 10
            day = '01'
        else:
            month -= 2
            day = '01'
        time_begin = '{}-{}-{}'.format(year, month, day)
    elif quarter in ('Q2', 'HY'):
        if month < 6:
            year -= 1
            month += 7
            day = '01'
        else:
            month -= 5
            day = '01'
        time_begin = '{}-{}-{}'.format(year, month, day)
    elif quarter == 'Q3':
        if month < 9:
            year -= 1
            month += 4
            day = '01'
        else:
            month -= 8
            day = '01'
        time_begin = '{}-{}-{}'.format(year, month, day)
    elif quarter in ('FY', 'Q4'):
        # time_begin = '{}-{}-{}'.format(int(year) - 1, month, day)
        if month == 12:
            time_begin = '{}-{}-{}'.format(year, 1, day)
        else:
            time_begin = '{}-{}-{}'.format(int(year)-1, int(month)+1, day)
    elif quarter == 'Q':
        # 无法取到开始日期,标记为0000-00-00固定格式
        time_begin = '0000-00-00'
        if year:
            time_begin = '{}-00-00'.format(year)
    else:
        time_begin = '0000-00-00'

    return time_begin

def quarter_to_end(header, month, day):
    year = header.time_str
    t = '{}-{}-{}'.format(year, month, day)
    try:
        t_test = time.strptime(t, "%Y-%m-%d")
    except Exception as e:
        # 简单修复下2月的错误 其他错误直接这里不处理，抛出去给下一层检查
        if month == 2 and day > 28:
           return '{}-{}-28'.format(year, month)
        else:
            return t
    else:
        return t


def date_extract(title, header, table_type, index_information, year_global, month_global, day_global):
    """
    数据回填程序
    :param title:title的Time对象
    :param header: header的Time对象
    :param table_type: 表类型
    :param index_information: index表中的信息
    :param month_global: PDF全局的月份,如果取不到月份时使用
    :param day_global: PDF全局的日期,如果取不到日期时使用
    :return: tuple(开始日期,结束日期)
    """
    time_begin = ''
    time_end = ''

    title = normalize_title(title, year_global, month_global, day_global)
    # 首先取出季度
    # 取用的优先级从高到低 header->title->global
    if header.time_quarter is not None:
        quarter = header.time_quarter
    else:
        if title.time_quarter is not None:
            quarter = title.time_quarter
        else:
            quarter = index_information[1]

    # 不需要回填的种类:
    # 1:yyyy-mm-dd
    # 2:yyyy-mm
    # 3:yyyy-mm-dd to yyyy-mm-dd
    if header.time_type == 1:
        year = int(header.time_str.split('-')[0])
        month = int(header.time_str.split('-')[1])
        day = '01'
        time_end = header.time_str
        time_begin = quarter_to_begin(day, month, year, quarter)
    elif header.time_type == 2:
        year = int(header.time_str.split('-')[0])
        month = int(header.time_str.split('-')[1])
        day = '01'
        time_end = header.time_str + '-' + str_day_add(int(month))
        time_begin = quarter_to_begin(day, month, year, quarter)
    elif header.time_type == 4:
        time_begin = header.time_begin
        time_end = header.time_end





    # 需要回填的种类
    elif header.time_type == 3:
        if title.time_type == 1:
            year = int(header.time_str)
            month = int(title.time_str.split('-')[1])
            day = int(title.time_str.split('-')[2])
            time_end = quarter_to_end(header, month ,day)
            time_begin = quarter_to_begin(day, month, year, quarter)
        elif title.time_type == 3:
            if quarter == 'Q1':
                time_begin = '{}-01-01'.format(header.time_str)
                time_end = '{}-03-31'.format(header.time_str)
            elif quarter == ('Q2', 'HY'):
                time_begin = '{}-04-01'.format(header.time_str)
                time_end = '{}-06-30'.format(header.time_str)
            elif quarter == 'Q3':
                time_begin = '{}-07-01'.format(header.time_str)
                time_end = '{}-09-30'.format(header.time_str)
            elif quarter == 'FY':
                time_begin = '{}-01-01'.format(header.time_str)
                time_end = '{}-12-31'.format(header.time_str)
            elif quarter == 'Q':
                time_begin = '0000-00-00'
                time_end = '{}-00-00'.format(header.time_str)
        elif title.time_type == 4:
            year = int(title.time_end.split('-')[0])
            month = int(title.time_end.split('-')[1])
            day = int(title.time_end.split('-')[2])
            time_end = '{}-{}-{}'.format(year, month, day)
            time_begin = quarter_to_begin(year, month, day, quarter)
        elif title.time_type == 5:
            time_begin = '{}-01-01'.format(title.time_end)
            time_end = '{}-12-31'.format(title.time_end)
    elif header.time_type == 5:
        if title.time_type == 1:
            month = int(title.time_str.split('-')[1])
            day = int(title.time_str.split('-')[2])
            time_begin = '{}-{}-{}'.format(header.time_begin, month, day)
            time_end = '{}-{}-{}'.format(header.time_end, month, day)
        elif title.time_type == 4:
            month = int(title.time_end.split('-')[1])
            day = int(title.time_end.split('-')[2])
            time_begin = '{}-{}-{}'.format(header.time_begin, month, day)
            time_end = '{}-{}-{}'.format(header.time_end, month, day)
        elif title.time_type in [3, 5]:
            time_begin = '{}-01-01'.format(header.time_end)
            time_end = '{}-12-31'.format(header.time_end)
    elif header.time_type == 6:
        # 找到例子添加
        pass
    elif header.time_type == 10:
        if title.time_type == 1:
            title_split = title.time_str.split('-')
            year = title_split[0]
            month = title_split[1]
            day = title_split[2]
        elif title.time_type == 3:
            year = title.time_str
            month = month_global
            day = day_global
        elif title.time_type == 4:
            year = title.time_end.split('-')[0]
            month = title.time_end.split('-')[1]
            day = title.time_end.split('-')[2]
        elif title.time_type == 5:
            year = time_end
            month = month_global
            day = day_global
        if re.findall('(current|closingbalance)', header.time_str):
            time_begin = '{}-{}-{}'.format(int(year) - 1, month_global, '01')
            time_end = '{}-{}-{}'.format(year, month_global, str_day_add(int(month_global)))
        elif re.findall('(previous|priorperiod|openingbalance)', header.time_str):
            time_begin = '{}-{}-{}'.format(int(year) - 2, month, day)
            time_end = '{}-{}-{}'.format(int(year) - 1, month, day)
    #
    # 中国特殊匹配
    #
    elif header.time_type == 11:
        str = re.sub(header.time_format, '', header.time_str)
        month_list = []
        for a in str:
            if a.isdigit():
                month_list.append(a)
        if len(month_list) == 2:
            time_begin = '{}-{}-{}'.format(year_global, month_list[0], '01')
            time_end = '{}-{}-{}'.format(year_global, month_list[1], str_day_add(int(month_list[1])))
        else:
            if title.time_type == 1:
                year = int(title.time_str.split('-')[0])
                month = int(title.time_str.split('-')[1])
                day = int(title.time_str.split('-')[2])
                time_end = '{}-{}-{}'.format(year, month, day)
                if quarter == 'FY':
                    time_begin = '{}-{}-{}'.format(int(year) - 1, month, day)
                elif quarter == 'Q1':
                    month = '01'
                    day = '01'
                    time_begin = '{}-{}-{}'.format(year, month, day)
                elif quarter in ('Q2', 'HY'):
                    month = '01'
                    day = '01'
                    time_begin = '{}-{}-{}'.format(year, month, day)
                elif quarter == 'Q3':
                    month = '07'
                    day = '01'
                    time_begin = '{}-{}-{}'.format(year, month, day)
            elif title.time_type == 3:
                if quarter == 'Q1':
                    time_begin = '{}-01-01'.format(year_global)
                    time_end = '{}-03-31'.format(year_global)
                elif quarter in ('Q2', 'HY'):
                    time_begin = '{}-01-01'.format(year_global)
                    time_end = '{}-06-30'.format(year_global)
                elif quarter == 'Q3':
                    time_begin = '{}-07-01'.format(year_global)
                    time_end = '{}-09-30'.format(year_global)
                elif quarter == 'FY':
                    time_begin = '{}-01-01'.format(year_global)
                    time_end = '{}-12-31'.format(year_global)
            elif title.time_type == 4:
                time_begin = title.time_begin
                time_end = title.time_end
            elif title.time_type == 5:
                time_begin = '{}-01-01'.format(title.time_end)
                time_end = '{}-12-31'.format(title.time_end)
    elif header.time_type == 12:
        if table_type == 'BS':
            # time_end = '{}-12-31'.format(int(year_global)-1)
            time_end = '{}-01-01'.format(year_global)
        else:
            month_list = []
            str = re.sub(header.time_format, '', header.time_str)
            for a in str:
                if a.isdigit():
                    month_list.append(a)
            if len(month_list) == 2:
                time_begin = '{}-{}-{}'.format(int(year_global) - 1, month_list[0], '01')
                time_end = '{}-{}-{}'.format(int(year_global) - 1, month_list[1], str_day_add(int(month_list[1])))
            else:
                if title.time_type == 1:
                    year = int(title.time_str.split('-')[0]) - 1
                    month = int(title.time_str.split('-')[1])
                    day = int(title.time_str.split('-')[2])
                    time_end = '{}-{}-{}'.format(year, month, day)
                    if quarter == 'FY':
                        time_begin = '{}-{}-{}'.format(year, '01', '01')
                    elif quarter == 'Q1':
                        month = '01'
                        day = '01'
                        time_begin = '{}-{}-{}'.format(year, month, day)
                    elif quarter in ('Q2', 'HY'):
                        month = '01'
                        day = '01'
                        time_begin = '{}-{}-{}'.format(year, month, day)
                    elif quarter == 'Q3':
                        month = '07'
                        day = '01'
                        time_begin = '{}-{}-{}'.format(year, month, day)
                elif title.time_type == 3:
                    year = int(year_global) - 1
                    if quarter == 'Q1':
                        time_begin = '{}-01-01'.format(year)
                        time_end = '{}-03-31'.format(year)
                    elif quarter in ('Q2', 'HY'):
                        time_begin = '{}-01-01'.format(year)
                        time_end = '{}-06-30'.format(year)
                    elif quarter == 'Q3':
                        time_begin = '{}-07-01'.format(year)
                        time_end = '{}-09-30'.format(year)
                    elif quarter == 'FY':
                        time_begin = '{}-01-01'.format(year)
                        time_end = '{}-12-31'.format(year)
                elif title.time_type == 4:
                    year = int(title.time_end.split('-')[0])
                    month = int(title.time_end.split('-')[1])
                    day = int(title.time_end.split('-')[2])
                    begin_month = title.time_begin.split('-')[1]
                    time_end = '{}-{}-{}'.format(int(year) - 1, month, str_day_add(int(month)))
                    time_begin = '{}-{}-{}'.format(int(year) - 1, begin_month, '01')
                elif title.time_type == 5:
                    time_begin = '{}-01-01'.format(int(title.time_end) - 1)
                    time_end = '{}-12-31'.format(int(title.time_end) - 1)

    return time_begin, time_end
