# -*- coding:utf-8 -*-
import re
import sys
import time

from algorithm.common import dbtools, configManage, tools
from algorithm.common_tools_pdf import subject_match_tools, standerSubjectLib


def checkinfointegrity(reportid,table):
    for hi in table.header.header_columns:
        header = table.header.header_columns[hi]
        if table.table_type in ('IS','CF') and (header.time_begin == None or header.time_end == None):
            raise Exception('TIMEINFO_MISSING')
        elif table.table_type == 'BS' and header.time_end == None:
            raise Exception('TIMEINFO_MISSING')
        elif header.currency == None or header.measureunit == None:
            header.currency = 'CNY'
            header.measureunit = 1
            # raise Exception('BASEINFO_MISSING')

def check_year_season(table, year_db, season_db):
    year = table.fiscal_year
    season = table.season_type
    # 先不做时间上的回填，暂时按这个条件先拦截下来
    if year != year_db or season != season_db:
        raise Exception('TIME_INFO_WRONG')

def check_value_iellgal(value):
    # rule = re.compile("^\[\[1-9\]+|0\.\],*[\d|元]$|不适用")
    value = re.sub('\s|,|，|^\(|\)$|^（|）$|人民币', '', value)
    rule = re.compile("(^(-)?([1-9]\d*|0)(\.\d+)?(元|分)?$)|(^(不适用|-|—|－|―|/|=|–)+$)")

    if value in ['']:
        return True

    if not rule.match(value):
        return False


    return True

def get_year_season_db(reportid):
    # 获取status表中年份
    getsql = "select fiscal_year, season_type_code from {table} where reportid='{reportid}'"
    getsql = getsql.format(table=configManage.config['table']['status'], reportid=reportid)
    result = dbtools.query_pdfparse(getsql)
    fiscal_year_db = result[0][0]
    season_type_db = result[0][1]
    return [fiscal_year_db, season_type_db]

def process(reportid,tablebox):
    year_season = get_year_season_db(reportid)
    year_db = year_season[0]
    season_db = year_season[1]

    for table in tablebox:
        # 检查表信息完整性
        checkinfointegrity(reportid,table)

        # 检查年度和季度
        check_year_season(table, year_db, season_db)


def final_check(table_box):
    for table in table_box:
        table_type = table.table_type
        # 检查输出数据是否为空
        if len(table.output_value_box) == 0:
            raise Exception('OUTPUT_EMPTY')

        # 检查输出数据中是否有值冲突
        # [countryid, 0
        # companyid, 1
        # reportid, 2
        # companyName,3
        #  table.table_type,4
        #  table.pageNum,5
        #  header.fiscal_year,6
        #  header.season_type,7
        #  subject, 8
        # value, 9
        # header.currency,10
        #  header.measureunit,11
        # header.time_begin,12
        #  header.time_end, 13
        # lindex[0], 14
        # tools.linkStr(cindex, '|'),15
        # header.isConsolidated]  16
        # actstandards ,17
        # isadjust ,18

        # 检查值正确性及值是否有冲突
        unique_key_box = []
        for i, s in enumerate(table.output_value_box):
            if i>=6:
                break

            if re.sub('：|:|\s|、', '',s[8]) in ['预付账款', '应收账款', '其他与投资活动有关的现金', '现金流入小计', '现金流出小计', '优先股', '永续债', '其中优先股', '其中永续债', '其中', '项目', '利息收入', '发放贷款及垫款', '其中被合并方在合并前实现的净利润',
                                             '同业拆入拆出资金净额','递延收益','预计负债', '持有至到期投资','其他']:
                continue
            key = tools.linkStr([s[4],s[8],s[12],s[13],s[16],s[5]], '_')
            value = s[9]
            result = check_value_iellgal(value)
            if not result:
                configManage.logger.error('VALUE_ILLEGAL: ' + value)
                raise Exception('VALUE_ILLEGAL')

            if s[16] == 0:
                continue
            # print key + '  ' + s[9]
            if key not in unique_key_box:
                unique_key_box.append(key)
            else:
                raise Exception('VALUE_CLASH')

        # 输出格式时间信息检查
        time_end_set = set()
        time_begin_set = set()
        for t in table.output_value_box:
            time_begin = t[12]
            time_end = t[13]
            time_end_set.add(time_end)
            time_begin_set.add(time_begin)
        if table.table_type == 'BS':
            for time_end in time_end_set:
                time_check(time_end, table_type)
        elif table.table_type in ('CF', 'IS'):
            for time_begin in time_begin_set:
                time_check(time_begin, table_type)
            for time_end in time_end_set:
                time_check(time_end, table_type)





def time_check(time_format,table_type):
    if time_format in ('', '0000-00-00') or time_format is None:
        configManage.logger.error('TIME_INVALID' + table_type)
        raise Exception('TIME_INVALID')
    else:
        try:
            time.strptime(time_format, "%Y-%m-%d")
        except:
            configManage.logger.error('TIME_FORMAT_ERROR' + time_format)
            raise Exception('TIME_FORMAT_ERROR')


def check_integrality(table):
    if table.body_end_line_index == len(table.table_area):
        return True
    value_border_min = sys.maxint
    value_border_max = 0
    for c in table.header.header_columns.values():
        if c.identity == 'value':
            value_border_min = c.x0 if c.x0 < value_border_min else value_border_min
            value_border_max = c.x1 if c.x1 > value_border_max else value_border_max
    check_count = 0
    ignore_box = ['项目']
    for check_line in table.table_area[table.body_end_line_index:]:
        # 只检查后三行
        if not check_line.is_useful:
            continue
        else:
            check_count += 1
            # 减少了检查范围
            if check_count + len(table.body_buffer) > 3:
                return True

        # 获取检查文本
        check_text = ''
        for b in check_line.blockbox:
            if b.x0 < value_border_min and b.x1 > value_border_min:
                return True
            elif b.x1 <= value_border_min:
                check_text = check_text + b.text
        # print check_text
        check_text_prue = subject_match_tools.getPureSbuectText(check_text)
        if check_text_prue == '':
            continue
        if check_text_prue in standerSubjectLib.subjects and check_text_prue not in ignore_box:
            configManage.logger.info("[TABLE_BODY_INCOMPLETE] ," + table.reportid + "," + check_text_prue + ',' + str(check_line.pageNum))
            raise Exception('TABLE_BODY_INCOMPLETE')
    return True



