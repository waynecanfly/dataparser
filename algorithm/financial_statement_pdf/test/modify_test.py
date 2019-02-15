# -*- coding:utf-8 -*-
import csv
import datetime
import difflib
import os
import re
import shutil
import sys
import threading

from concurrent.futures import ThreadPoolExecutor

from algorithm.character_converge_pdf import character_converge
from algorithm.common import configManage, tools, dbtools
from algorithm.common.para import Para
from algorithm.financial_statement_pdf import financial_statement_pdf, fs_pdf_tools

record_lock = threading.Lock()

def record(message):
    record_lock.acquire()
    path = os.path.abspath(os.path.dirname(__file__) + os.path.sep + ".") + '/log/modify_test_log2.txt'
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
        for x in table.output_value_box:
            del x[-3]
        table_content = [tools.linkStr(x, ',') for x in table.output_value_box]
        content = content + table_content

    # 获取对比内容
    try:
        with file(os.path.join(sample_path, reportid) + '.csv', 'r') as compare_file:
            reader = csv.reader(compare_file)
            compare_content = []
            for x in reader:
                del x[-3]
                compare_content.append(x)
            compare_content = [tools.linkStr(x, ',') for x in compare_content]
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
    try:
        para.statusid = 10
        c_r = character_converge.process(para, is_test)
        if c_r:
            para.statusid = 20
            result = method(para, is_test)
            if isinstance(result, str):
                para.statusid = -30
                c_r = character_converge.process(para, is_test)
                if c_r:
                    para.statusid = 40
                    result = method(para, is_test)
                    if isinstance(result, str):
                        raise Exception(result)
                    else:
                        content_compare(result, sample_path, para.reportid, test_path, test_number, htlmldiffer)
                else:
                    raise Exception('CONVERGE_ERROR_WIHTOUT_LINE')
            else:
                content_compare(result, sample_path, para.reportid, test_path, test_number, htlmldiffer)
        else:
            raise Exception('CONVERGE_ERROR_WIHT_LINE')
    except Exception as e:
        record(para.reportid + '    ' + e.message)
    print para.reportid

def process():
    test_path = os.path.abspath(os.path.dirname(__file__) + os.path.sep + ".")

    sample_path = os.path.join(test_path, 'test_sample')

    box = os.listdir(sample_path)

    box = ['CHN100412011000601035', 'CHN101752009000201018', 'CHN100552012000601030', 'CHN100562017000301007',
           'CHN100352017000601406', 'CHN100362011000201018', 'CHN102292008000201021', 'CHN100432008000601038',
           'CHN101022008000201039', 'CHN101022011000601029', 'CHN101522012000201024', 'CHN100252012000201026',
           'CHN101452011000201020', 'CHN102112012000601027', 'CHN102512008000101040', 'CHN123992009000601011',
           'CHN102512008000601039', 'CHN102512009000201028', 'CHN102512009000301033', 'CHN102512010000101035',
           'CHN102512010000601034', 'CHN102512011000101031', 'CHN102512011000201020', 'CHN102512012000101027',
           'CHN102512012000301021', 'CHN103352011000301020', 'CHN103352012000301018', 'CHN103472008000201032',
           'CHN104372012000201029', 'CHN112352016000301006', 'CHN112352017000301003', 'CHN121642007000601004',
           'CHN122372011000201014', 'CHN122882010000201010', 'CHN122882013000201021', 'CHN102202009000201019',
           'CHN127892011000601013', 'CHN128662009000301007', 'CHN102202008000201020', 'CHN100032011000201035',
           'CHN100042007000601040', 'CHN100042009000601034', 'CHN100062007000601036', 'CHN100102008000601038',
           'CHN100162013000601010', 'CHN100172008000201042', 'CHN100182016000601007', 'CHN100192012000201031',
           'CHN100222012000101029', 'CHN100252015000601009', 'CHN100272011000601033', 'CHN100272017000601015',
           'CHN100282010000201034', 'CHN100292009000201031', 'CHN100322014000601034', 'CHN100362017000201004',
           'CHN100372013000601035', 'CHN100392011000201017', 'CHN100442011000201030', 'CHN100472015000601014',
           'CHN100482008000601035', 'CHN100492012000101013', 'CHN100502012000101011', 'CHN100522013000201007',
           'CHN100592016000601028', 'CHN100602013000101007', 'CHN100632016000101002', 'CHN107952014000301018',
           'CHN100662017000301005', 'CHN100722017000601004', 'CHN100742017000601007', 'CHN100882011000601022',
           'CHN100892012000101017', 'CHN100902009000201033', 'CHN100962011000601035', 'CHN101152010000201021',
           'CHN101202009000601031', 'CHN101252011000601027', 'CHN101272007000601041', 'CHN101292007000601040',
           'CHN101302017000601407', 'CHN101392010000601033', 'CHN101422010000201025', 'CHN101452011000601037',
           'CHN101522009000601035', 'CHN101532009000601036', 'CHN101552009000101031', 'CHN101622016000201005',
           'CHN101642010000201029', 'CHN101652009000601029', 'CHN101672014000301013', 'CHN101692007000601041',
           'CHN101692018000201401', 'CHN101762008000101038', 'CHN101782015000301012', 'CHN101792012000301018',
           'CHN101802016000301011', 'CHN101812014000201008', 'CHN101892016000201012', 'CHN101902015000201005',
           'CHN101912009000601038', 'CHN101942008000601039', 'CHN101962009000201018', 'CHN102002014000601007',
           'CHN102012011000201022', 'CHN102032017000301007', 'CHN102092015000301016', 'CHN102102018000201401',
           'CHN102122015000201008', 'CHN102162007000601041', 'CHN102162008000601040', 'CHN102172009000601038',
           'CHN102212015000301015', 'CHN102222010000301032', 'CHN102292015000301024', 'CHN103352017000301011',
           'CHN121642018000101401', 'CHN123992010000201010', 'CHN125452013000601021', 'CHN128662011000301015',
           'CHN128732008000201002', 'CHN129012008000601008', 'CHN129892017000301002', 'CHN128732009000101004',
           'CHN128662010000201010', 'CHN120342008000201002', 'CHN100132011000201031', 'CHN128772011000601018',
           'CHN1337301797751']

    useless = ['CHN100412011000601035', 'CHN101752009000201018', 'CHN100552012000601030', 'CHN100562017000301007',
               'CHN100352017000601406', 'CHN100362011000201018', 'CHN102292008000201021', 'CHN100432008000601038',
               'CHN101022008000201039', 'CHN101022011000601029', 'CHN101522012000201024', 'CHN100252012000201026',
               'CHN101452011000201020', 'CHN102112012000601027', 'CHN102512008000101040', 'CHN123992009000601011',
               'CHN102512008000601039', 'CHN102512009000201028', 'CHN102512009000301033', 'CHN102512010000101035',
               'CHN102512010000601034', 'CHN102512011000101031', 'CHN102512011000201020', 'CHN102512012000101027',
               'CHN102512012000301021', 'CHN103352011000301020', 'CHN103352012000301018', 'CHN103472008000201032',
               'CHN104372012000201029', 'CHN112352016000301006', 'CHN112352017000301003', 'CHN125452013000601021',
               'CHN122372011000201014', 'CHN122882010000201010', 'CHN122882013000201021', 'CHN102202009000201019',
               'CHN127892011000601013', 'CHN128662009000301007',  'CHN102202008000201020', 'CHN102002014000601007',
               'CHN100542017000201022'
               ]
    box = [ x  for x in box if x.split('.')[0] not in useless]

    test_number = datetime.datetime.now().strftime('%Y%m%d_%H_%M_%S_%f') + '_' + str(len(box))
    print test_number
    record('================ ' + test_number + ' ================')
    para_box = get_para(box)

    htlmldiffer = difflib.HtmlDiff()

    # 查出需要比较的文件
    with ThreadPoolExecutor(1) as executor:
        for para in para_box:
            executor.submit(porcess_single, financial_statement_pdf.process, para, True, sample_path, test_path, test_number, htlmldiffer)


def sync_status():
    ok_box = []
    report_map = {}
    checksql = "SELECT distinct guid FROM g_fs_data_original WHERE country_code = 'CHN' AND is_check_done = 'Y'"
    print checksql
    okbox = dbtools.query_opd_fdss(checksql)
    for ok in okbox:
        r = ok[0]
        r = re.sub('\r\n', '', r)
        report = r[0:-2]
        t = r[-2:]
        if report not in report_map:
            report_map[report] = [t]
        else:
            report_map[report].append(t)
        # print r
    for key in report_map:
        value = report_map[key]
        if 'BS' in value and 'IS' in value and 'CF' in value:
            ok_box.append(key)

    sql = "update opd_pdf_status set statusid = 200, status_name='FDSS标记完成' where reportid in ({reports})".format(
        reports="'" + "','".join(ok_box) + "'")
    dbtools.query_pdfparse(sql)

def copy_file():
    box = ['CHN128772011000601018']
    for b in box:
        oldpath = '/PDFdata/opd/pdf/pdf_table_new' + "/p_country={p_country}/p_company={p_company}/{reportid}.csv"
        oldpath = oldpath.format(p_country=b[0:3], p_company=b[0:8], reportid=b)
        newpath = '/home/code/DataParser/v000/dataparser/algorithm/financial_statement_pdf/test/test_sample/{reportid}.csv'.format(reportid=b)
        # newpath = '/home/code/DataParser/v000/dataparser/algorithm/financial_statement_pdf/test/check_sample/{reportid}.csv'.format(reportid=b)
        print oldpath
        print newpath
        shutil.copyfile(oldpath, newpath)

def screen_repeat_file():
    sql = """select * from 
(select companyid, fiscal_year, season_type_code,count(*) as nu, GROUP_CONCAT(reportid) as reports from opd_pdf_status where  countryid='CHN'  and statusid not in (200,110,32,-60,-110, 50) group by  companyid, fiscal_year, season_type_code HAVING nu >1)a left join (select companyid, fiscal_year, season_type_code,count(*) as nu2, GROUP_CONCAT(reportid) as reports from opd_pdf_status where  countryid='CHN'  and statusid in (200,110,-60,-110, 50) group by  companyid, fiscal_year, season_type_code )b
on a.companyid=b.companyid 
and a.fiscal_year=b.fiscal_year
and a.season_type_code=b.season_type_code"""
    result = dbtools.query_pdfparse(sql)

    keep_box = []
    drop_box = []

    root_path = configManage.config['location']['pdf_block']
    datapath = root_path + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"

    flags = ['更正公告', '报告摘要']

    for r in result:
        sub_drop_box = []
        sub_keep_box = []
        check_reports = r[4].split(',')
        for cr in check_reports:
            is_drop = False
            countryid = cr[0:3]
            companyid = cr[0:8]
            single_path = datapath.format(p_country=countryid, p_company=companyid, p_reportid=cr)
            try:
                data = fs_pdf_tools.getSourceData(single_path)
            except:
                sub_keep_box.append(cr)
                continue
            text = ''
            page1 =data[0].pageNum
            for b in data:
                if b.pageNum != page1:
                    break
                text += b.text
            for f in flags:
                if f in text:
                    if cr == u'CHN1006202576085':
                        pass
                    is_drop  = True
                    sub_drop_box.append(cr)
                    break
            if not is_drop:
                sub_keep_box.append(cr)
        if len(sub_keep_box) > 1 or (len(sub_keep_box) == 1 and r[5] is not None):
            keep_box.append([r[0], r[1], r[2],len(sub_keep_box), tools.linkStr(sub_keep_box, ','),r[5],r[6],r[7],r[8],r[9]])
        drop_box += sub_drop_box

    print 'ok'

    # update drop one
    drop_sql = "update opd_pdf_status set statusid = 31 where countryid='CHN' and reportid in ('{reportids}')".format(reportids=tools.linkStr(drop_box, "','"))
    print drop_sql
    dbtools.query_pdfparse(drop_sql)

    with file('./repeats.csv', 'w+') as outputFile:
        writer = csv.writer(outputFile)
        for line in keep_box:
            writer.writerow(line)


def temp():
    # 更新状态
    sync_status()

    # 复制文件
    # copy_file()

    # 筛选报告期重复文件
    # screen_repeat_file()

    sys.exit()

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)

    # 临时操作
    # temp()

    process()