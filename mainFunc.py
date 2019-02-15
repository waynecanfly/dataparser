# -*- coding:utf-8 -*-
import datetime
import importlib
import re
import sys
import traceback
import time,os
from concurrent.futures import ThreadPoolExecutor

from algorithm.capture_pattern import capture_pattern
from algorithm.capture_table_pdf import capture_table
from algorithm.character_converge_pdf import character_converge
from algorithm.common import tools, configManage, dbtools
from algorithm.common.para import Para



def reRunSigleReport(p_country, p_company, p_reportid):
    # 检查状态对不对,检查有没有锁上
    checksql = "select reportid from {table} where reportid = '{reportid}' and lockup=0 and statusid=33"
    checksql = checksql.format(reportid=p_reportid, table=configManage.config['table']['status'])
    checkresult = dbtools.query_pdfparse(checksql)
    if len(checkresult) != 0:
        # lock up
        locksql = "update {table} set lockup=1 where reportid='{reportid}'"
        locksql = locksql.format(reportid=p_reportid, table=configManage.config['table']['status'])
        dbtools.query_pdfparse(locksql)
        capture_table.process(p_country, p_company, p_reportid, True)
    # capture_table.process(p_country, p_company, p_reportid, True)


def captureTableRerun():
    # 根据闲时忙时确定程序运行的线程数
    THREAD_NUM = 100

    sql = "select countryid,companyid,reportid,statusid from {table} where countryid='CHN' and statusid=33 order by last_process_time"
    sql = sql.format(table=configManage.config['table']['status'])
    result = dbtools.query_pdfparse(sql)
    print 'capture table rerun 33: ' + str(len(result)) + '  Time: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with ThreadPoolExecutor(THREAD_NUM) as executor:
        for pdfinfo in result:
            try:
                executor.submit(reRunSigleReport, pdfinfo[0], pdfinfo[1], pdfinfo[2])
            except Exception as e:
                excepttext = traceback.format_exc()
                print pdfinfo[2] + '\n' + excepttext
                excepttext = re.sub('\n', ' ', excepttext)
                excepttext = re.sub('\"', '\'', excepttext)
                tools.updatePDFStatus(pdfinfo[0], pdfinfo[1], pdfinfo[2], -100, excepttext)
    print 'Rerun Finish: ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


#手动触发重跑状态33的数据
def manualRerun():
    # config init
    capture_pattern.process()
    captureTableRerun()

# 正式流程中
def threadRun(method, para):
    try:
        method(para)
        print para.reportid
    except Exception as e:
        excepttext = traceback.format_exc()
        configManage.logger.error(para.reportid + '\n' + excepttext)
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)
        tools.updatePDFStatus(para.countryid, para.companyid, para.reportid, -100, excepttext)


# new
def genCondition(al):
    condBox = ['lockup=0']
    if al['doc_type'] != '':
        condBox.append("doc_type in %s" % "('" + tools.linkStr(al['doc_type'].split(','), "','") + "')")
    if al['statusid'] != '':
        condBox.append("statusid in %s" % "(" + tools.linkStr(al['statusid'].split(','), ",") + ")")
    if al['countryid'] != '':
        condBox.append("countryid in %s" % "('" + tools.linkStr(al['countryid'].split(','), "','") + "')")
    if al['datamark'] != '':
        condBox.append("data_mark in %s" % "('" + tools.linkStr(al['datamark'].split(','), "','") + "')")
    if al['error_code'] != '':
        condBox.append("error_code in %s" % "('" + tools.linkStr(al['error_code'].split(','), "','") + "')")

    if len(condBox):
        condStr = tools.linkStr(condBox, ' and ')
        return ' where ' + condStr
    else:
        return ''

def getMethod(al):
    entrance = al['entrance']
    modulePath, methodName = entrance[0:entrance.rfind('.')], entrance.split('.')[-1]

    importlib.import_module(modulePath)

    module = sys.modules[modulePath]

    method = getattr(module, methodName)
    return method

def getProcessFileInfo(al):
    condition = genCondition(al)

    sql = """select countryid,companyid,reportid,statusid,country_name,company_name,fiscal_year,season_type_code,history_status,data_mark,doc_path,doc_type,report_type,error_code,sector_code,sector_name 
                                from {tablename} 
                                {condition}
                                order by companyid desc limit {thread_num}"""
    sql = sql.format(tablename=configManage.config['table']['status'], condition=condition, thread_num=al['threadNum']*20)

    aimFiles = dbtools.query_pdfparse(sql)

    # reportBox = []
    paraBox = []
    for r in aimFiles:
        paraBox.append(Para(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12],r[13],r[14], r[15]))
        # reportBox.append(r[2])

    return paraBox


def sync_fdss_status():
    ok_box = []
    report_map = {}
    checksql = "SELECT distinct guid FROM g_fs_data_original WHERE country_code = 'CHN' AND is_check_done = 'Y'"
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
    for key in report_map:
        value = report_map[key]
        if 'BS' in value and 'IS' in value and 'CF' in value:
            ok_box.append(key)

    sql = "update opd_pdf_status set statusid = 200, status_name='FDSS标记完成' where reportid in ({reports})".format(
        reports="'" + "','".join(ok_box) + "'")
    dbtools.query_pdfparse(sql)

def projectInit():
    # nas挂载
    nas_map_check()

    # lockup off
    lockupoffSql = "update {table} set lockup=0 where statusid<>0 and countryid='CHN'"
    lockupoffSql = lockupoffSql.format(table=configManage.config['table']['status'])
    dbtools.query_pdfparse(lockupoffSql)

    # 同步fdss状态
    sync_fdss_status()

    # 初始化相似度索引
    from algorithm.capture_table_pdf_HKG.match_code_generate import hongkong_init
    hongkong_init()

def nas_map_check():

    def is_mapping():
        m1 = os.path.exists('/PDFdata/SuccessfulMapping.test')
        m2 = os.path.exists('/volume1/homes/SuccessfulMapping.test')
        m3 = os.path.exists('/volume2/data/SuccessfulMapping.test')
        m4 = os.path.exists('/volume3/homes3/SuccessfulMapping.test')
        if m1 and m2 and m3 and m4:
            return True
        else:
            return False

    if is_mapping():
        return True
    while True:
        os.system('mount -o username=super-opdata,password=originp123 //10.100.4.101/PDFdata /PDFdata')
        os.system('mount -o username=admin,password=originp123 //10.100.4.102/homes /volume1/homes')
        os.system('mount -o username=admin,password=originp123 //10.100.4.102/data /volume2/data')
        os.system('mount -o username=admin,password=originp123 //10.100.4.102/homes3 /volume3/homes3/')
        if is_mapping():
            return True
        else:
            print 'sleep waitingMap' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            time.sleep(600)

def getTimePara(cron):
    times = cron.split(' ')
    return {
        'year': times[6],
        'month': times[4],
        'day': times[3],
        'day_of_week': times[5] if times[5]!='?' else '*',
        'hour': times[2],
        'minute': times[1],
        'second': times[0]
    }


def exeAlgorithm(al, method, paraBox, roundtimes, THREAD_NUM):
    configManage.logger.info("algorithm: " + al['name'] + " is running")

    tools.batchLockUp(paraBox)

    begintime = datetime.datetime.now()
    print 'Algorithm: ' + al['name'] + '  |  ' + str(len(paraBox)) + '  |  ' + begintime.strftime(
        '%Y-%m-%d %H:%M:%S')
    configManage.logger.info(
        'Algorithm: ' + al['name'] + '  |  ' + str(len(paraBox)) + '  |  ' + begintime.strftime(
            '%Y-%m-%d %H:%M:%S'))

    with ThreadPoolExecutor(int(al['threadNum'])) as executor:
        for para in paraBox:
            executor.submit(threadRun, method, para)

    configManage.logger.info(
        'Algorithm: ' + al['name'] + '  cost : ' + str(datetime.datetime.now() - begintime))

