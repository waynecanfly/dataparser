# -*- coding:utf-8 -*-
import time
import traceback
from datetime import datetime
from algorithm.common import dbtools, configManage
from algorithm.common.recognize_timeinfo import header_recognize, special_process_chn, time_standardization
from algorithm.common.recognize_timeinfo.data_backfill import date_extract
from algorithm.common.recognize_timeinfo.header_recognize import date_dispose
from algorithm.common.recognize_timeinfo.recoginze_time_exception import TimeRecoginzeException
from algorithm.common.recognize_timeinfo.time_standardization import Time_Not_valid, is_valid_date, season_type_check, \
    recongnize_current
from algorithm.common.recognize_timeinfo.title_recognize import date_dispose_for_title


# header = {
#     "columnIndex":2,
#     "text":"期末余额",
#     "time_begin": "",
#     "time_end": ""
# }
#
# table = {
#     "table_type": "BS",
#     "page_number": "1",
#     "title_text": "资产负债表",
#     "fiscal_year": "2014",
#     "season_type": "Q1",
#     "header_list": [header,...],
#     "recognize_info": ["fiscal_year",...]
# }
#
# information_dic = {
#     "report_id": "CHN10001**********",
#     "tablebox": [table,...]
# }


def get_common_information(report_id):
    """
    查询库中的年度和季度类型信息
    :param report_id:
    :return: fiscal_year(年份),season_type_code(季度类型)
    """
    fiscal_year = None
    season_type_code = None
    sql = 'select fiscal_year,season_type_code from %s where reportid="%s";'
    result = dbtools.query_pdfparse(sql % (configManage.config['table']['status'], report_id))
    for unit in result:
        fiscal_year = unit[0]
        season_type_code = unit[1]
    return fiscal_year, season_type_code


def get_global_time(information_dic):
    """
    获取PDF文件中的全局的年月日
    :param information_dic:
    :return: 全局年月日(可能为空)
    """
    year_global = None
    month_global = None
    day_global = None
    title_list = []

    report_id = information_dic["report_id"]
    for table in information_dic["tablebox"]:
        table_type = table["table_type"]
        title = date_dispose_for_title(report_id[0:3], table["title_text"])
        if title is not None:
            title_list.append(title)
        for unit in table["header_list"]:
            text = unit["text"]
            header = date_dispose(text, table_type, report_id[0:3])
            if header is not None:
                if header.time_type == 1:
                    month_global = header.time_str.split('-')[1]
                    day_global = header.time_str.split('-')[2]
                    break
                elif header.time_type == 2:
                    month_global = header.time_str.split('-')[1]
                    day_global = time_standardization.str_day_add(month_global)
                    break
                elif header.time_type == 4:
                    month_global = header.time_end.split('-')[1]
                    day_global = header.time_end.split('-')[2]
                    break
                elif header.time_type == 6:
                    month_global = header.time_end.split('-')[0]
                    day_global = header.time_end.split('-')[1]
                    break

    if len(title_list) > 0:
        for title in title_list:
            if title.time_type == 1:
                year_global = title.time_str.split('-')[0]
                month_global = title.time_str.split('-')[1]
                day_global = title.time_str.split('-')[2]
                break
            elif title.time_type == 2:
                year_global = title.time_str.split('-')[0]
                month_global = title.time_str.split('-')[1]
                day_global = time_standardization.str_day_add(int(month_global))
                break
            elif title.time_type == 4:
                year_global = title.time_end.split('-')[0]
                month_global = title.time_end.split('-')[1]
                day_global = title.time_end.split('-')[2]
                break
            elif title.time_type == 6:
                month_global = title.time_str.split('-')[0]
                day_global = title.time_str.split('-')[1]
                break

    return year_global, month_global, day_global


def time_format(time_begin, time_end, table_type):
    """
    将输出的时间标准化
    :param time_begin:
    :param time_end:
    :param table_type:
    :return:
    """
    if time_begin != '':
        year = time_begin.split('-')[0]
        month = time_begin.split('-')[1]
        day = time_begin.split('-')[2]
        if len(month) == 1:
            month = '0{}'.format(month)
        if len(day) == 1:
            day = '0{}'.format(day)
        if month == '12' and day == '31':
            year = str(int(year) + 1)
            month = '01'
            day = '01'
        time_begin = '{}-{}-{}'.format(year, month, day)
    if time_end != '':
        year = time_end.split('-')[0]
        month = time_end.split('-')[1]
        day = time_end.split('-')[2]
        if len(month) == 1:
            month = '0{}'.format(month)
        if len(day) == 1:
            day = '0{}'.format(day)
        time_end = '{}-{}-{}'.format(year, month, day)
    if table_type == 'BS':
        time_begin = None
    return time_begin, time_end


def tablebox_to_information_dic(tablebox, report_id):
    """
    将tablebox对象,转化为通用的时间识别接口
    :param tablebox:
    :param report_id:
    :return:
    """
    information_dic = {}
    information_dic["report_id"] = report_id
    information_dic["tablebox"] = []
    for table_unit in tablebox:
        table = {}
        table["table_type"] = table_unit.tabletype
        table["page_number"] = table_unit.pageNum
        table["title_text"] = table_unit.globalinfo.text
        table["header_list"] = []
        for header_unit in table_unit.index_header_map.values():
            if header_unit.identity == "value":
                header = {}
                header["columnIndex"] = header_unit.columnIndex
                header["text"] = header_unit.text
                table["header_list"].append(header)
        information_dic["tablebox"].append(table)
    return information_dic


def process(information_dic):
    # header = {
    #     "columnIndex":2,
    #     "text":"期末余额",
    #     "time_begin": "",
    #     "time_end": ""
    # }
    #
    # table = {
    #     "table_type": "BS",
    #     "page_number": "1",
    #     "title_text": "资产负债表",
    #     "fiscal_year": "2014",
    #     "season_type": "Q1",
    #     "header_list": [header,...],
    #     "recognize_info": ["fiscal_year",...]
    # }
    #
    # information_dic = {
    #     "report_id": "CHN10001**********",
    #     "tablebox": [table,...]
    # }
    try:
        report_id = information_dic["report_id"]

        # 查询数据库中的信息
        fiscal_year_mysql, season_type_code_mysql = get_common_information(report_id)

        # 获取整个文件的年度/月份/日期/季度信息,作为全局信息,如果获取不到的,使用数据库中查到的信息填充
        year_global, month_global, day_global = get_global_time(information_dic)
        if year_global is None:
            year_global = str(fiscal_year_mysql)
        else:
            if int(year_global) > int(datetime.now().year) or abs(int(year_global) - int(fiscal_year_mysql)) >= 4:
                year_global = fiscal_year_mysql
            if int(year_global) > int(fiscal_year_mysql):
                year_global = fiscal_year_mysql
        global_season_type = season_type_code_mysql

        for table in information_dic["tablebox"]:
            if table['page_number'] == 91:
                pass
            fiscal_year = year_global
            index_information = [fiscal_year, global_season_type]
            table_type = table["table_type"]
            table["recognize_info"] = []

            # 获取title对象
            title = date_dispose_for_title(report_id[0:3], table["title_text"])

            if year_global is not None:
                table["recognize_info"].append("fiscal_year")

            # 如果title中能取到季度类型则忽略全局的季度类型
            if title is not None:
                if title.time_quarter is not None:
                    table["recognize_info"].append("season_type")
                    season_type_check(global_season_type, title.time_quarter)
                #     global_season_type = title.time_quarter
                # else:
                #     global_season_type = index_information[1]
                if title.time_str is not None:
                    if title.time_type != 6:
                        if int(title.time_str[0:4]) > int(datetime.now().year) or abs(
                                int(title.time_str[0:4]) - int(fiscal_year_mysql)) >= 4:
                            title = None

            table["season_type"] = global_season_type
            table["fiscal_year"] = fiscal_year

            for unit in table["header_list"]:
                header = header_recognize.date_dispose(unit["text"], table_type, report_id[0: 3])

                # 识别
                if header is not None:
                    time_begin, time_end = date_extract(title, header, table_type, index_information,
                                                        year_global, month_global, day_global)
                    # 将识别出来的时间输出为标准格式
                    time_begin, time_end = time_format(time_begin, time_end, table_type)
                    unit["time_begin"] = time_begin
                    unit["time_end"] = time_end

                    is_valid_date(unit["text"], [time_begin, time_end])   # 识别结果检查
                    # 以表内最大年份为fiscal_year
                    if time_end and int(time_end.split('-')[0]) > int(table["fiscal_year"]):
                        table["fiscal_year"] = time_end.split('-')[0]

            special_process_chn.chn_special_title_recognize(report_id[0:3], table)


        if len({table['season_type'] for table in information_dic['tablebox']}) != 1:
            raise Time_Not_valid('season_not_same')
        recongnize_current(information_dic['tablebox'])

        return information_dic
    except Time_Not_valid as e:
        raise Time_Not_valid(e.message, e.statusinfo)
    except Exception as e:
        excepttext = traceback.format_exc()
        print excepttext
        raise Exception('TIME_RECOGNIZE_EXCEPTION')

