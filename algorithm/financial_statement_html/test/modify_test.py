# -*- coding:utf-8 -*-
import csv
import datetime
import difflib
import os
import re
import sys
import threading

from concurrent.futures import ThreadPoolExecutor

from algorithm.common import configManage, tools, dbtools
from algorithm.common.para import Para
from algorithm.financial_statement_html import financial_statement_html


record_lock = threading.Lock()

def record(message):
    record_lock.acquire()
    path = os.path.abspath(os.path.dirname(__file__) + os.path.sep + ".") + '/log/modify_test_log.txt'
    logFile = open(path, 'a+')
    try:
        logFile.write(message + '\n')
    finally:
        logFile.close()
        record_lock.release()


def content_compare(tablebox, sample_path, reportid, test_path, test_number, htlmldiffer):
    # 获取内容
    content = []
    for table in tablebox:
        table_content = [tools.linkStr(x, ',') for x in table.output_value_box]
        content = content + table_content

    content = [re.sub('None', '', x) for x in content]

    # 获取对比内容
    try:
        with file(os.path.join(sample_path, reportid) + '.csv', 'r') as compare_file:
            compare_content = list(csv.reader(compare_file))
            compare_content = [re.sub('None', '', tools.linkStr(x, ',')) for x in compare_content]
    except:
        record(reportid + '    ' + 'NEW_ONE')
        return True

    if set(content) != set(compare_content):
        record(reportid + '    ' + 'CONTENT_DIFFERENT')
        save_path = os.path.join(test_path, test_number)
        tools.makeDirs(save_path)
        difile = file(os.path.join(save_path, reportid + '.html'), 'w+')
        difile.write("<meta charset='UTF-8'>")
        difile.write(htlmldiffer.make_file(compare_content, content))
        difile.close()
    else:
        record(reportid + '    ' + 'SAME')

def get_para(box):
    reports = tools.linkStr(["'" + x + "'" for x in box], ',')

    sql = """select countryid,companyid,reportid,statusid,country_name,company_name,fiscal_year,season_type_code,history_status,data_mark,doc_path,doc_type,report_type,error_code     
                                from opd_pdf_status where reportid in ({reports})""".format(reports=reports)
    result = dbtools.query_pdfparse(sql)
    paraBox = []
    for r in result:
        paraBox.append(Para(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12], r[13]))
    return paraBox

def porcess_single(method, para, is_test, sample_path, test_path, test_number, htlmldiffer):
    result = method(para, is_test)

    if isinstance(result, str):
        record(para.reportid + '    ' + result)
    else:
        content_compare(result, sample_path, para.reportid, test_path, test_number, htlmldiffer)
    print para.reportid

def process():
    test_path = os.path.abspath(os.path.dirname(__file__) + os.path.sep + ".")

    sample_path = os.path.join(test_path, 'test_sample')

    box = os.listdir(sample_path)
    box = [b[:-4] for b in box]
    # box = ['USA1264907686832']

    test_number = datetime.datetime.now().strftime('%Y%m%d_%H_%M_%S_%f') + '_' + str(len(box))
    print test_number
    record('================ ' + test_number + ' ================')
    para_box = get_para(box)

    htlmldiffer = difflib.HtmlDiff()

    # 查出需要比较的文件
    with ThreadPoolExecutor(6) as executor:
        for para in para_box:
            executor.submit(porcess_single, financial_statement_html.process, para, True, sample_path, test_path, test_number, htlmldiffer)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)

    # test.process()
    process()