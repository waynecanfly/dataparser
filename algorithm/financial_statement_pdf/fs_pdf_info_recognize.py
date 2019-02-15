# -*- coding: UTF-8 -*-
from algorithm.common import configManage, dbtools
from algorithm.common.recognize_baseinfo import recognize_baseinfo
from algorithm.common.recognize_timeinfo import time_analyse

# header = {
#     "columnIndex":2,
#     "text":"期末余额",
#     "time_begin": "",
#     "time_end": ""
#     "currency": ""
#     "time_end": ""
#     "time_end": ""
# }
#
# table = {
#     "table_type": "BS",
#     "page_number": "1",
#     "title_text": "资产负债表",
#     "header_list": [header,...]
# }
#
# information_dic = {
#     "report_id": "CHN10001**********",
#     "tablebox": [table,...]
# }


def gen_para(reportid, table_map):
    table_box = []
    for id in table_map.keys():
        t = table_map[id]
        table_para = {}
        table_para['id'] = id
        table_para['table_type'] = t.table_type
        table_para['page_number'] = t.pageNum
        title_area_text = t.title['title_text']
        for t_area in t.title_area:
            title_area_text = title_area_text + t_area.text
        table_para['title_text'] = title_area_text

        header_box = []
        for h_index in sorted(t.header.header_columns.keys()):
            header = t.header.header_columns[h_index]
            header_box.append({'columnIndex': h_index, 'text': header.text, 'time_begin': '', 'time_end': ''})
        table_para['header_list'] = header_box

        table_box.append(table_para)

    para = {'report_id': reportid, 'tablebox': table_box}
    return para


def recognize_info_backfill(para, table_map):
    for t_result in para['tablebox']:
        table = table_map[t_result['id']]

        table.fiscal_year = t_result['fiscal_year']
        table.season_type = t_result['season_type']
        for h_result in t_result['header_list']:
            curHeader = table.header.header_columns[h_result['columnIndex']]

            curHeader.fiscal_year = table.fiscal_year
            curHeader.season_type = table.season_type
            curHeader.time_begin = h_result['time_begin']
            curHeader.time_end = h_result['time_end']
            curHeader.isConsolidated = h_result['isCon']
            curHeader.currency = h_result['currency']
            curHeader.measureunit = h_result['measureunit']
            curHeader.actstandards = h_result['actstandards']
            curHeader.isadjust = h_result['isadjust']

def backfill_to_db(para, reportid):
    # 回填检测。如果一致，不回填，如果不一致输出到log让实习生检查
    fiscal_year = set()
    season_type = set()
    for table in para['tablebox']:
        if len(table['recognize_info']) > 0:
            fiscal_year.add(table['fiscal_year'])
            season_type.add(table['season_type'])
    if len(fiscal_year) > 1 or len(season_type) > 1:
        # 一个pdf中不存在有多财年的报表，也不存在有多个季度的数据
        raise Exception('TIME_INFO_WRONG')

    # 获取status表中年份
    getsql = "select fiscal_year, season_type_code from {table} where reportid='{reportid}'"
    getsql = getsql.format(table=configManage.config['table']['status'], reportid=reportid)
    result = dbtools.query_pdfparse(getsql)
    fiscal_year_db = result[0][0]
    season_type_db = result[0][1]

    year_differt = False
    season_differt = False

    if fiscal_year:
        this_year = list(fiscal_year)[0]
        if this_year != fiscal_year_db:
            year_differt = True
    if season_type:
        this_season = list(season_type)[0]
        if this_season != season_type_db:
            season_differt = True

    if not year_differt and not season_differt:
        return True
    else:
        message = "BACKFILL, {reportid}, {db_year}, {db_season}, {this_year}, {this_season}"
        message = message.format(reportid=reportid, db_year=fiscal_year_db, db_season=season_type_db, this_year=list(fiscal_year)[0], this_season=list(season_type)[0])
        configManage.logger.info(message)
        sql = "update {table} set fiscal_year='{fiscal_year}', season_type_code='{season_type}' where reportid='{reportid}'"
        sql = sql.format(table=configManage.config['table']['status'], fiscal_year=list(fiscal_year)[0],
                         season_type=list(season_type)[0], reportid=reportid)
        dbtools.query_pdfparse(sql)

def info_recognize(reportid, tablebox):
    # tablebox转换成tablemap，方便识别后信息进行回天
    table_map = {}
    for index, table in enumerate(tablebox):
        table_map[index] = table

    # 生成识别所用的
    para = gen_para(reportid, table_map)

    # 时间识别(识别结果直接附在入参上)
    time_analyse.process(para)

    # 合并、母公司识别； 货币； 数量单位识别
    recognize_baseinfo.process(para)

    # 根据识别出来的信息回填到table对象中
    recognize_info_backfill(para, table_map)

    # 根据识别出来的信息回填年份和季度到status表中(不准确，先废弃)
    # backfill_to_db(para, reportid)

    return True

