# -*- coding: UTF-8 -*-
import re
import sys

from algorithm.common import dbtools, configManage
from algorithm.common_tools_pdf import title_match_tools


def get_title_lib(company_name):
    title_lib = {}
    # sqlj = "insert into title_match_lib(title, matchcode, tabletype,language_type , user_create) values('年初到报吿期末利润表','初到报吿期末利润表', 'IS', 'CHN', 'li') "
    # result = dbtools.query_pdfparse(sqlj)
    sql = 'select matchcode, tabletype from title_match_lib'
    result = dbtools.query_pdfparse(sql)
    for unit in result:
        key = title_match_tools.getMatchTitleText(unit[0].encode('utf-8'), company_name)
        # print key
        title_lib[key] = unit[1]
    # print '=============================='
    return title_lib

def is_in_lib(matchText, title_lib):
    if matchText == '':
        return False
    # 去掉重叠matchtitie

    matchText_no_repeat = unicode(matchText)
    temp_box = matchText_no_repeat[0]
    for i, u in enumerate(matchText_no_repeat):
        if u not in temp_box:
            temp_box += u

    matchText_no_repeat = temp_box.encode('utf-8')
    # print matchText

    for title in title_lib.keys():
        if matchText == title:
            return matchText
        elif matchText_no_repeat == title:
            return matchText_no_repeat
    return False

def take_out_catalog(title_anchor):
    page_map = {}
    for t in title_anchor:
        if t['title_pageNum'] not in page_map:
            page_map[t['title_pageNum']] = [t]
        else:
            page_map[t['title_pageNum']].append(t)

    for titles in page_map.values():
        if len(titles) < 3:
            continue
        for t in titles:
            title_anchor.remove(t)
    return title_anchor

def find_fs_title(line_box, reportid, company_name):
    # 获取标题库
    title_lib = get_title_lib(company_name)

    # 开始查找
    title_anchor = []

    page_num = set()

    # 中国的只需要查找一行，如果其他语言的，可能要通过多行进行查找
    for index, line in enumerate(line_box):
        page_num.add(line.pageNum)
        # if line.pageNum==19 :
        #     print str(line.pageNum) + '  ' + line.text + '  ' + str(line.linetableid)


        # 如果该行在有线的表格中，直接不进行判断
        # if line.linetableid is not None:
        #     continue

        isMatched = False
        # 先逐个block判断
        for block in line.blockbox:
            matchText = title_match_tools.getMatchTitleText(block.text, company_name)
            matchText = is_in_lib(matchText, title_lib)
            if matchText:
                block.identity = 'title'
                table_type = title_lib[matchText]
                title_anchor.append({'index': index, 'table_type': table_type, 'title_line': line, 'title_pageNum': line.pageNum, 'title_lineindex': line.lineIndex, 'title_text': line.text, 'isConsolidated': -1})
                isMatched = True
                break
        # 如果单个block找不到表，则尝试把整行合起来进行判断
        if not isMatched:
            matchText = title_match_tools.getMatchTitleText(line.text, company_name)
            matchText = is_in_lib(matchText, title_lib)
            if matchText:
                for b in line.blockbox:
                    b.identity = 'title'
                table_type = title_lib[matchText]
                title_anchor.append({'index': index, 'table_type': table_type, 'title_line': line, 'title_pageNum': line.pageNum, 'title_lineindex': line.lineIndex, 'title_text': line.text, 'isConsolidated': -1})

    # 生成表范围
    for i,anchor in enumerate(title_anchor):
        anchor['table_range'] = [anchor['index'] + 1, title_anchor[i + 1]['index'] if i + 1 < len(title_anchor) else sys.maxint]


    # 把从目录中找到标题取掉，特征就是在同一页三个表都有的
    title_anchor = take_out_catalog(title_anchor)


    # 获取所有表类型
    found_type = set()
    for t in title_anchor:
        found_type.add(t['table_type'])

    # 识别报表是合并类型还是别的类型，然后判断是否找全
    # 没找全直接报错，后续程序成熟后，一个每找到的可设置为“怀疑无用pdf”， 没找全的设置为“怀疑原pdf财报就不全”
    # @test
    if len(found_type) < 3 :
        if not len(found_type) or is_notice(line_box):
            raise Exception('USELESS_PDF')
        else:
            message = ''
            for t in title_anchor:
                message = message + str(t['table_type']) + ':' + str(t['title_pageNum']) + '    '
            configManage.logger.info('[TITLE_MISSING],' + reportid + ',' + message)
            raise Exception('NOT_ALL_FOUND_TITLE')
    title_anchor = is_found_all(title_anchor)
    if not title_anchor:
        raise Exception('NOT_ALL_FOUND_TITLE')


    #返回结果
    return title_anchor

def is_notice(line_box):
    flag = ['更正公告']
    first_page = line_box[0].pageNum
    for l in line_box:
        if l.pageNum != first_page:
            break
        for f in flag:
            if f in l.text:
                return True
    return False


def d_is_1(title_anchor):
    page_box = []
    for t in title_anchor:
        page_box.append(t['title_pageNum'])
    page_box = sorted(page_box)
    for i,p in enumerate(page_box):
        if i+1 >= len(page_box):
            break
        next_p = page_box[i+1]
        if abs(next_p-p) > 3:
            return False
    return True





def is_found_all(title_anchor):
    # 备忘： 后续可能需要加上时间跨度的判断，如果某个表有某个时间跨度，那么所有类型的报表是否都有这个时间跨度的表？
    consolidatedKeyWord = ['consolidated','合并']
    standaloneKeyWord = ['standalone','母公司']

    consolidatedBox = set()
    consolidated_title_box = []
    standaloneBox = set()
    standalone_title_box = []
    unknowBox = set()
    unknowBox_title_box = []

    for anchor in title_anchor:
        is_Judge = False
        pureTitle = re.sub('\s', '', anchor['title_text'])
        for standWord in standaloneKeyWord:
            if standWord in pureTitle:
                anchor['isConsolidated'] = 0
                standaloneBox.add(anchor['table_type'])
                standalone_title_box.append(anchor)
                is_Judge = True
                break
        for conWord in consolidatedKeyWord:
            if conWord in pureTitle:
                is_Judge = True
                anchor['isConsolidated'] = 1
                consolidatedBox.add(anchor['table_type'])
                consolidated_title_box.append(anchor)
                break
        if not is_Judge:
            unknowBox.add(anchor['table_type'])
            unknowBox_title_box.append(anchor)

    #  判断
    if len(consolidatedBox) == 3:
        return consolidated_title_box
    elif len(consolidatedBox) == 0 and len(unknowBox) == 3:
        return unknowBox_title_box  # 表示表找全了，但是没有独立报表和母公司报表之分
    else:
        return False