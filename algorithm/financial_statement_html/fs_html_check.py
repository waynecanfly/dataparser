# -*- coding:utf-8 -*-
from algorithm.common import dbtools, configManage


def checkinfointegrity(reportid,table):
    for index, header in table.header_columns.items():
        # html的只要检查有用的表头
        if index in table.valid_row_ids:
            if table.table_type in ('IS','CF') and (header.time_begin == None or header.time_end == None):
                raise Exception('TIMEINFO_MISSING')
            elif table.table_type == 'BS' and header.time_end == None:
                raise Exception('TIMEINFO_MISSING')
            elif header.currency == None or header.measureunit == None:
                raise Exception('BASEINFO_MISSING')


def check_year_season(table, year_db, season_db):
    year = table.fiscal_year
    season = table.season_type
    # 先不做时间上的回填，暂时按这个条件先拦截下来
    if year != year_db or season != season_db:
        raise Exception('TIME_INFO_WRONG')


def get_year_season_db(reportid):
    # 获取status表中年份
    getsql = "select fiscal_year, season_type_code from {table} where reportid='{reportid}'"
    getsql = getsql.format(table=configManage.config['table']['status'], reportid=reportid)
    result = dbtools.query_pdfparse(getsql)
    fiscal_year_db = result[0][0]
    season_type_db = result[0][1]
    return [fiscal_year_db, season_type_db]


def check_header(table):
    if not table.header_columns or not table.valid_row_ids:
        raise Exception('HEADER_NO_VALID_ROWS')
    if int(max(table.header_columns.keys())) < int(max(table.valid_row_ids)):
        # 处理方法1. 将部分数据过滤掉  2. 报错
        raise Exception('HEADER_MISMATCHING')


def check_subject_and_value(table):
    # 检查科目和值是否为空
    if not table.subject_df:
        raise Exception('SUBJECT_MISSING')
    if not table.subject_value_df:
        raise Exception('SUBJECT_VALUE_MISSING')


def process(reportid,tablebox):
    year_season = get_year_season_db(reportid)
    year_db = year_season[0]
    season_db = year_season[1]

    for table in tablebox:
        # 检查表信息完整性
        checkinfointegrity(reportid,table)

        # 检查年度和季度 （html的每一个表年份不一样，暂时不检查）
        # check_year_season(table, year_db, season_db)

        # 检查header是否为空(调试，暂时注释)
        # check_header(table)

        # 检查科目和值是否为空(调试，暂时注释)
        # check_subject_and_value(table)

