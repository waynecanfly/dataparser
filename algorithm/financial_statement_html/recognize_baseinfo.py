# -*- coding: utf-8 -*-

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
#     "header_list": [header,...]
# }
#
# information_dic = {
#     "report_id": "CHN10001**********",
#     "tablebox": [table,...]
# }
import re

from algorithm.common import dbtools
from algorithm.common.tools import tupleToMap, tupleToMapList


class RecognizeLib:
    def __init__(self,currency_measureunit_lib, currency_lib, measureunit_lib):
        self.currency_measureunit_lib = currency_measureunit_lib
        self.currency_lib = currency_lib
        self.measureunit_lib = measureunit_lib

def getRecognizeLib():
    currency_sql = """select content,currency,country_code from currency_measureunit_mapping_lib where mapping_type = 1 and country_code='USA'"""
    measureunit_sql = """select content,measureunit,country_code from currency_measureunit_mapping_lib where mapping_type = 2 and country_code='USA'"""
    currency_measureunit_sql = """select content,currency,measureunit,country_code from currency_measureunit_mapping_lib where mapping_type = 3 and country_code='USA'"""

    currency_measureunit = tupleToMapList(dbtools.query_pdfparse(currency_measureunit_sql))
    currency = tupleToMap(dbtools.query_pdfparse(currency_sql))
    measureunit = tupleToMap(dbtools.query_pdfparse(measureunit_sql))

    return RecognizeLib(currency_measureunit, currency, measureunit)


def recognize_currency_measureunit_iscon(text, lib, country_code, is_header):
    # actstandards会计准则  isadjust是否调整
    result = {'currency': None, 'measureunit': None, 'isCon': -1, 'actstandards': None, 'isadjust': 1}
    # 美国数据识别的不要去掉空格
    pureText = text.lower()

    # 识别货币和数量单位(以下排序是为了优先匹配长度长的，如单位：元， 和 元  应优先匹配单位元， 这个排序以后有优化的余地，如按国家排，本国的识别不到再识别别国的)
    currency_measureunit = lib.currency_measureunit_lib.keys()
    currency_measureunit.sort(key=lambda x: len(x))
    currency_measureunit.reverse()
    break_flag = False
    for key in currency_measureunit:
        pute_key = key.lower()
        if pute_key in pureText:
            # country_code参数在currency_measureunit_lib里面的情况
            for li in lib.currency_measureunit_lib[key]:
                if li[2] == country_code:
                    result['currency'] = li[0]
                    result['measureunit'] = li[1]
                    break_flag = True
                    break
            if result['currency'] is not None and result['measureunit'] is not None:
                break
            # 以下用来匹配数据库的country_code字段为空的情况
            for li in lib.currency_measureunit_lib[key]:
                if li[2] is None or li[2].strip() == '':
                    result['currency'] = li[0]
                    result['measureunit'] = li[1]
                    break_flag = True
                    break
            if break_flag:
                break

    if result['currency'] is None:
        currency_lib = lib.currency_lib.keys()
        currency_lib.sort(key=lambda x: len(x))
        currency_lib.reverse()
        for key in currency_lib:
            pute_key = key.lower()
            if pute_key in pureText:
                result['currency'] = lib.currency_lib[key]
                break
    if result['measureunit'] is None:
        measureunit_lib = lib.measureunit_lib.keys()
        measureunit_lib.sort(key=lambda x: len(x))
        measureunit_lib.reverse()
        for key in measureunit_lib:
            pute_key = key.lower()
            if pute_key in pureText:
                result['measureunit'] = lib.measureunit_lib[key]
                break

    # 识别合并还是母公司（全局的话识别这个意义不大，因为单独的母公司报表不会来到这里，不过走一次这个步骤无副作用）
    consolidatedKeyWord = ['consolidated', '合并'] if not is_header else ['consolidated', '合并', '本集团', '集团']
    standaloneKeyWord = ['standalone', '母公司'] if not is_header else ['standalone', '公司', '母公司']
    for standWord in standaloneKeyWord:
        if standWord in pureText:
            result['isCon'] = 0
            break
    for conWord in consolidatedKeyWord:
        if conWord in pureText:
            result['isCon'] = 1
            break

    # 新增信息点：会计准则（国际会计准则：itnlstd 中国会计准则：chnstd）
    if not is_header:
        result['actstandards'] = 'chnstd'
        chnaccountingkeyword = ['中国会计准则']
        itnlaccountingkeyword = ['国际会计准则', '国际财务报告准则']
        for chnword in chnaccountingkeyword:
            if chnword in pureText:
                result['actstandards'] = 'chnstd'
                break
        for itnlword in itnlaccountingkeyword:
            if itnlword in pureText:
                result['actstandards'] = 'itnlstd'
                break

    # 新增信息点：是否调整（-1调整前：1调整后）
    if is_header:
        adjustkeywordaft = ['调整后', '已重述', '重编', '重述后', '重列', '经重置', '置入资产', '实际']
        adjustkeywordbef = ['调整前', '未含并购影响', '唐山陶瓷', '准则']
        for befword in adjustkeywordbef:
            if befword in pureText:
                result['isadjust'] = -1
                break
        for aftword in adjustkeywordaft:
            if aftword in pureText:
                result['isadjust'] = 1
                break

    return result


def get_info_from_db(reportid):
    sql = "select table_type, currency,measureunit from currency_measureunit_update_record where report_id='{}'".format(reportid)
    # print sql
    result = dbtools.query_pdfparse(sql)
    tabletype_info_map = {}
    for r in result:
        tabletype_info_map[r[0]] = [r[1], r[2]]
    return tabletype_info_map

def fitting_global_info(global_result, info_map_db, table_type):
    db_info = info_map_db.get(table_type, None)
    if db_info is None:
        return global_result
    else:
        global_result['currency'] = db_info[0] if db_info[0] != '' else global_result['currency']
        global_result['measureunit'] = db_info[1] if db_info[1] != '' else global_result['measureunit']
        return global_result

def process(para, country_code=None):
    # 获取识别库
    """
    # 20181129 修改：识别货币符号和单位，需要带国家code参数。
    # 否则货币符号库里面同一条记录（同一表达，例如"$"）不能正确识别出USD,还是KHD等
    """
    # 为了适配没有给country_code参数的引用的情况，暂时通过切片取到country_code
    if country_code is None:
        country_code = para['report_id'][0:3]

    lib = getRecognizeLib()

    # 全表货币和数量单位。用于当某个表没有标明数量和货币单位时使用
    global_currency = None
    global_measureunit = None

    # 获取数据库中的信息
    info_map_db = get_info_from_db(para['report_id'])

    for table in para['tablebox']:
        if table['title_text'] == ' CONSOLIDATED STATEMENTS OF OPERATIONS Years Ended June 30, (In Thousands, Except Per Share Amounts) 2015 2017 2016 ﻿$$$':
            pass
        # 先识别全局信息
        global_result = recognize_currency_measureunit_iscon(table['title_text'], lib, country_code, False)
        table['isConsolidated'] = global_result['isCon']

        # 检查数据库中是否有值
        global_result = fitting_global_info(global_result, info_map_db, table['table_type'])

        # 识别每个表头列的信息，如果表头列信息没有的话，就从全局信息中取
        for header in table['header_list']:
            header_result = recognize_currency_measureunit_iscon(header['text'], lib, country_code, True)

            #根据global结果和header结果，对header赋值
            header['currency'] = header_result['currency'] if header_result['currency'] is not None else global_result['currency']
            header['measureunit'] = header_result['measureunit'] if header_result['measureunit'] is not None else global_result['measureunit']
            header['isCon'] = header_result['isCon'] if header_result['isCon'] != -1 else global_result['isCon']
            header['actstandards'] = header_result['actstandards'] if header_result['actstandards'] is not None else global_result['actstandards']
            header['isadjust'] = header_result['isadjust'] if header_result['isadjust'] != 1 else global_result['isadjust']
    # 检查信息是否都识别出来了。如果信息补全，到人工填写库中查找（以后完善）

    return True

    # 利用global_currency和global_measureunit多表联合进行回填（以后完善）
