# -*- coding:utf-8 -*-
import datetime
import os
import sys
import threading

from algorithm.common import configManage, tools
from algorithm.common.para import Para
from algorithm.financial_statement_pdf import financial_statement_pdf


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


def content_compare(tablebox, sample_path, reportid):
    # 获取内容
    content = []
    for table in tablebox:
        table_content = [tools.linkStr(x, ',')+'\n' for x in table.output_value_box]
        content = content + table_content

    # 获取对比内容
    with file(os.path.join(sample_path, reportid) + '.csv', 'r') as compare_file:
        compare_content = compare_file.readlines()
    # compare_content = [x.split(',') for x in compare_content]

    if set(content) != set(compare_content):
        record(reportid + '    ' + 'CONTENT_DIFFERENT')
    else:
        record(reportid + '    ' + 'SAME')



def process():
    test_path = os.path.abspath(os.path.dirname(__file__) + os.path.sep + ".")

    sample_path = os.path.join(test_path, 'test_sample')

    box = os.listdir(sample_path)

    test_number = datetime.datetime.now().strftime('%Y%m%d%H_%f') + '_' + str(len(box))

    record('================ ' + test_number + ' ================')

    # 查出需要比较的文件
    for sample in box:
        reportid = sample.split('.')[0]
        # reportid = 'CHN100142007000601044'
        print reportid
        countryid = reportid[0:3]
        companyid = reportid[0:8]
        para = Para(countryid, companyid, reportid, '1', '2', '3', '4', '5', '6', '7', 'x', '8', '9')
        result = financial_statement_pdf.process(para, True)

        if isinstance(result, str):
            record(reportid + '    ' + result)
        else:
            content_compare(result, sample_path, reportid)



if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)

    # test.process()
    process()