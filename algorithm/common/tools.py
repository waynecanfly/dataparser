# -*- coding: UTF-8 -*-
import datetime
import os
import re
import shutil
import threading
import requests
import tools

from algorithm.common import configManage, dbtools

mkdirLock = threading.Lock()

subjectfileLock = threading.Lock()

stautsMap = {
    0: '待数据提取',
    10: '数据提取完成',
    -10: '数据提取失败',
    -20: '字符汇聚失败',
    20: '字符汇聚完成',
    -30: '报表提取失败',
    30: '报表提取完成',
    31: 'PDF中无表',
    32: '无用PDF',
    33: '表提取库缺失',
    34: '待二次提取',
    -40: '字符汇聚失败_无线',
    40: '字符汇聚完成_无线',
    42: '待二次识别',
    100: 'file_generated',
    110: '已上传至FDSS',
    -110: 'HDFS连接错误'
}

stauts_map_html = {
    -100: 'UNKNOWN_ERROR',
    -31: '没有匹配到表头',  # 待移除
    -30: '报表提取失败',
    0: '待数据提取',
    10: '数据提取完成',
    30: 'html无table标签',
    31: '没有匹配到报表',
    32: '无用HTML',
    33: '报表不全',  # 待移除
    43: '时间信息缺失',  # 待移除
    100: 'FILE_GENERATED'
}


def isOneWord(a, b, is_oneline):
    if not is_oneline:
        return False
    return a - b <= 1 if a - b > 0 else True



def comparexy(a, b):
    return abs(a - b) <= 1

def isHaveTitleKeyWord(blocktext):
    keyWord = {'balance','income','cash','loss', 'financial', 'consolidated', 'position'}
    for key in keyWord:
        if key in blocktext:
            return True
    return False

def removeTextTimeInfo(text):
    rule = ['([0-9]{2}(st)?)',


           '([0-9]{2}\.[0-9]{2}\.[0-9]{4})',
            '[&,~\[\]]', '\d']
    reText = linkStr(rule, '|')
    return re.sub(reText, '', text)

def removeTextTimeInfo2(text):
    text = re.sub('[^a-z]', '', text.lower())
    rule = ['([0-9]{2}(st)?)',
        '((january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december))',
        '((jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(jl)|(aug)|(sep)|(sept)|(oct)|(nov)|(dec))',
            '(consolidated)']
    reText = linkStr(rule, '|')
    return re.sub(reText, '', text)

def linkStr(strlist, connector):  # join
    result = str(strlist[0])
    for i in range(1, len(strlist)):
        s = strlist[i]
        result = result + connector + str(s)
    return result


def move(oldpath, newpath):
    aimPath = os.path.abspath(newpath + os.path.sep+"..")
    if not os.path.exists(aimPath):
        os.makedirs(aimPath)
    try:
        shutil.move(oldpath, newpath)
    except:
        pass


def replaceTimeAndUseless(text):
    pureText = getPureTextForP(text)

    textRe = re.sub('[0-9]', '*', pureText).lower()
    temptext = re.sub('((january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december))|((jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(jl)|(aug)|(sep)|(sept)|(oct)|(nov)|(dec))', '#',  textRe).lower()
    return re.sub('\s', '', temptext)

def getPureText(text):
    return re.sub("[\(\)\s\.(#|#)']", '', text).lower()

def getPureTextForP(text):
    return re.sub("[\(\)\s`'\*]", '', text).lower()


def genBlockColumnIndexs(linebox):
    referLine = initReferLine(linebox)
    for l in linebox:
        columnNum = len(l.blockbox)
        for b in l.blockbox:
            referLine = genSingleBlockIndex(b, referLine, columnNum)
    # uniformization
    # print '=========================='
    uniformization = {}
    for i, f in enumerate(referLine):
        # print f['index']
        uniformization[f['index']] = i
    # print uniformization
    for l in linebox:
        for b in l.blockbox:
            # print b.columnIndex
            b.columnIndex = uniformization[b.columnIndex]

    tempset = set()
    for l in linebox:
        for b in l.blockbox:
            tempset.add(b.columnIndex)

    return len(referLine)


def genSingleBlockIndex(block, referLine, columnNum):
    for i, f in enumerate(referLine):
        if block.x1 <= f['x0']:
            newIndex = int((0 + f['index']) / 2) if i == 0 else int((referLine[i-1]['index'] + f['index']) / 2)
            block.columnIndex = newIndex
            referLine.append({
                'x0': block.x0,
                'x1': block.x1,
                'index': newIndex
            })
            break
        elif not (block.x1 <= f['x0'] or block.x0 >= f['x1']):
            block.columnIndex = f['index']
            referLine[i] = resetReferLine(referLine[i], block, columnNum)
            break
        elif block.x0 >= f['x1'] and (i + 1) == len(referLine):
            newIndex = f['index'] + 8000
            block.columnIndex = newIndex
            referLine.append({
                'x0': block.x0,
                'x1': block.x1,
                'index': newIndex
            })
            break
    referLine = sorted(referLine, key=lambda refer: refer['index'])
    return referLine

def resetReferLine(referLine, block, columnNum):
    if columnNum < 2:
        return referLine
    return {
        'x0': referLine['x0'] if referLine['x0'] < block.x0 else block.x0,
        'x1': referLine['x1'] if referLine['x1'] > block.x1 else block.x1,
        'index': referLine['index']
    }


def initReferLine(linebox):
	# 以后修改成referline为列数的最多的那几行综合起来的结果，每一列参考的[x0, x1]为该列下范围最大的。
    referLine = []
    for i, b in enumerate(linebox[0].blockbox):
        referLine.append({
            'x0': b.x0,
            'x1': b.x1,
            'index': (i+1) * 8000
        })
    return referLine


def tupleToMap(tu):
    result = {}
    for t in tu:
        result[t[0]] = t[1]
    return result


def tupleToMapList(tu):
    result = {}
    for unit in tu:
        if unit[0] not in result:
            result[unit[0]] = [unit[1:]]
        else:
            result[unit[0]].append(unit[1:])
    return result


def tupleToList(tu):
    result = []
    for t in tu:
        result.append(t[0])
    return result


def overlapRate(firstYRange, secondYRange, offset=2):
    if firstYRange[0] > secondYRange[1] or secondYRange[0] + offset > firstYRange[1]:
        return 0
    borderList = (firstYRange + secondYRange)
    borderList.sort()
    firstGap = abs(firstYRange[1] - firstYRange[0])
    secondGap = abs(secondYRange[1] - secondYRange[0])
    overlapGap = abs(borderList[2] - borderList[1])
    return overlapGap / min(firstGap, secondGap) if min(firstGap, secondGap) != 0 else 1


def timeMove(time, year=0, month=0):
    units = time.split('-')
    time_year = int(units[0])
    time_month = int(units[1])
    time_day = int(units[2])
    if year != 0:
        time_year = time_year + year
        return str(time_year) + '-' + str(time_month) + '-' + str(time_day)
    elif month < 0 and abs(month) >= time_month:
        time_year = time_year - (abs(month)-time_month) / 12 + 1
        time_month = 12 - ((abs(month) - time_month) % 12)
        return str(time_year) + '-' + str(time_month) + '-' + str(time_day)
    elif month > 0 :
        time_year = time_year + (month + time_month) / 12
        time_month = (month + time_month) % 12
        return str(time_year) + '-' + str(time_month) + '-' + str(time_day)

def batchLockUp(paras):
    reportids = []
    for p in paras:
        reportids.append(p.reportid)
    reportidsSQl = "('" + linkStr(reportids, "', '") + "')"
    lockupSql = """update {table} set lockup=1, last_process_time=now() where reportid in """ + reportidsSQl
    lockupSql = lockupSql.format(table=configManage.config['table']['status'])
    dbtools.query_pdfparse(lockupSql)

def lockUp(p_country, p_company, p_reportid):
    # lockoff
    lockupSql = """update {table} set lockup={lockup} where countryid='{p_country}' and companyid='{p_company}' and reportid='{p_reportid}'"""
    lockupSql = lockupSql.format(lockup=1, p_country=p_country, p_company=p_company, p_reportid=p_reportid, table=
    configManage.config['table']['status'])
    dbtools.query_pdfparse(lockupSql)

def updatePDFStatus(p_country, p_company, p_reportid, statusid, statusinfo, errorcode = ''):
    status_name = stautsMap.get(statusid, '')
    sql = """update {table} set statusid={statusid}, status_name='{status_name}',status_info="{statusinfo}" ,history_status=concat(substring_index(history_status, ',', -10),',','{statusid}'), error_code='{errorcode}', last_process_time=now() where countryid='{p_country}' and companyid='{p_company}' and reportid='{p_reportid}'"""
    sql = sql.format(statusid=statusid, status_name=status_name, statusinfo=statusinfo, p_country=p_country, p_company=p_company, p_reportid=p_reportid, errorcode=errorcode, table=
    configManage.config['table']['status'])
    dbtools.query_pdfparse(sql)
    # lockoff
    lockoffSql = """update {table} set lockup={lockup} where countryid='{p_country}' and companyid='{p_company}' and reportid='{p_reportid}'"""
    lockoffSql = lockoffSql.format(lockup=0, p_country=p_country, p_company=p_company, p_reportid=p_reportid, table=
    configManage.config['table']['status'])
    dbtools.query_pdfparse(lockoffSql)


def update_html_status(p_country, p_company, p_reportid, statusid, statusinfo, errorcode=''):
    status_name = stauts_map_html.get(statusid, '')
    sql = """update {table} set statusid={statusid}, status_name='{status_name}',status_info="{statusinfo}" ,history_status=concat(substring_index(history_status, ',', -10),',','{statusid}'), error_code='{errorcode}', last_process_time=now() where countryid='{p_country}' and companyid='{p_company}' and reportid='{p_reportid}'"""
    sql = sql.format(statusid=statusid, status_name=status_name, statusinfo=statusinfo, p_country=p_country,
                     p_company=p_company, p_reportid=p_reportid, errorcode=errorcode, table=
                     configManage.config['table']['status'])
    dbtools.query_pdfparse(sql)
    # lockoff
    lockoffSql = """update {table} set lockup={lockup} where countryid='{p_country}' and companyid='{p_company}' and reportid='{p_reportid}'"""
    lockoffSql = lockoffSql.format(lockup=0, p_country=p_country, p_company=p_company, p_reportid=p_reportid, table=
    configManage.config['table']['status'])
    dbtools.query_pdfparse(lockoffSql)


def isIdleTime():
    curHour = datetime.datetime.now().strftime('%H')
    idleTimeBox = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '23']
    return curHour in idleTimeBox


def lockoff(p_country, p_company, p_reportid):
    # lockoff
    lockupSql = """update {table} set lockup={lockup} where countryid='{p_country}' and companyid='{p_company}' and reportid='{p_reportid}'"""
    lockupSql = lockupSql.format(lockup=0, p_country=p_country, p_company=p_company, p_reportid=p_reportid, table=
    configManage.config['table']['status'])
    dbtools.query_pdfparse(lockupSql)

def getCheckedReport(all=False):
    reportsFile = open('./test/testlist.txt')
    reports = []
    try:
        while 1:
            line = reportsFile.readline()
            if not line or 'end' in line and not all:
                break
            if '#' in line and not all:
                continue
            if len(line) < 21 and all:
                continue
            reports.append(line[0:21])
    finally:
        reportsFile.close()
    return reports


def makeDirs(path):
    mkdirLock.acquire()
    try:
        if not os.path.exists(path):
            try:
                os.makedirs(path)
            except:
                raise
    finally:
        mkdirLock.release()


def outputsubejct(message):
    subjectfileLock.acquire()
    logFile = open('./log/subjects.txt', 'a+')
    try:
        logFile.write(message + '\n')
    finally:
        logFile.close()
        subjectfileLock.release()

def Rewording(characters):
    url = 'https://translate.google.cn/#en/zh-CN/' + characters
    userAgent = ''
    sentence = ''
    return sentence
