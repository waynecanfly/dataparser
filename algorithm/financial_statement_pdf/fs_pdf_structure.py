# -*- coding:utf-8 -*-
import copy
import re
import sys

from algorithm.common import configManage, tools, dbtools
from algorithm.common_tools_pdf import subject_match_tools, standerSubjectLib, fittingSubjectLib
from algorithm.common import tools
from algorithm.financial_statement_pdf.containers.line import Line


def checkIfMulSubject(table):
    headers = table.header.header_columns
    headers_len = len(table.header.header_columns)
    # 列数大于等于6， 且列数为双数
    if headers_len >= 6 and headers_len % 2 == 0:
        headerIndex = sorted(headers.keys())
        half = len(headers) / 2
        for i, index in enumerate(headerIndex):
            if i >= half:
                break
            else:
                curHeader = headers[index]
                comHeader = headers[headerIndex[i+half]]
                # 以下条件判断当前列与其对应的另一列是否一致，不一致的话直接返回
                con1 = curHeader.identity == comHeader.identity
                con2 = curHeader.identity == 'value' and comHeader.identity == 'value'
                con3 = curHeader.text == comHeader.text
                if (not con1) or (con1 and con2 and not con3):
                    return False
        return True
    else:
        return False

# 解决多科目列
def solve_multi_subject_column(table):
    # 检查是否为多列科目
    if checkIfMulSubject(table):
        cloumn_indexs = sorted(table.header.header_columns.keys())
        half = len(table.header.header_columns) / 2
        left_index = cloumn_indexs[0:half]
        right_index = cloumn_indexs[half:]
        right_left_map = dict(zip(right_index, left_index))

        columnIndexFitting = right_index[0]
        leftMaxLineIndex = 0
        rightMinLineIndex = sys.maxint
        # 计算左边最大行号和右边最小行号
        for line in table.body:
            for unit in line.blockbox:
                if unit.columnIndex >= columnIndexFitting:
                    rightMinLineIndex = rightMinLineIndex if rightMinLineIndex < unit.total_lineindex else unit.total_lineindex
                else:
                    leftMaxLineIndex = leftMaxLineIndex if leftMaxLineIndex > unit.total_lineindex else unit.total_lineindex

        # 根据上一步的计算值，按行整理出待输出数据结合
        new_line_box = []
        for line in table.body:
            new_line = None
            del_box = []
            for i,unit in enumerate(line.blockbox):
                # 修改右边的lineIndex、columnIndex, 以lineIndex作为后面数据整理的基础。
                # 但时这里有个弊端，就是block内部的属性会不一致，line对象内部属性也会不一致。
                # 暂时每想到更好的办法了，而且把所有属性都对齐好，后面用不上，而且太麻烦。
                # newLine = copy.deepcopy(line)
                if unit.columnIndex >= columnIndexFitting:
                    unit.total_lineindex = (unit.total_lineindex - rightMinLineIndex + 1) + leftMaxLineIndex
                    unit.columnIndex = right_left_map[unit.columnIndex]
                    if new_line is None:
                        new_line = Line(unit, unit.total_lineindex)
                    else:
                        new_line.add(unit)
                    del_box.append(i)
            del_box.reverse()
            for d in del_box:
                del line.blockbox[d]
            if new_line is not None:
                new_line_box.append(new_line)
        table.body += new_line_box




        # 去掉右边无用header(主要的作用时为了以后整理数据的时候不会带上无用的列)
        for key in cloumn_indexs:
            header = table.header.header_columns[key]
            if header.columnIndex >= columnIndexFitting:
                table.header.header_columns.pop(header.columnIndex)

    # 根据调整后的行号重新调整tablebody(后面使用时再根据需求进行处理)

def gen_body_lineindex_map(table):
    table.body_line_map = {}
    table.body_max_lineindex = table.body[-1].total_lineindex

    last_range = [-1, -1, -1]

    for line in table.body + table.body_buffer:
        over_lap = tools.overlapRate([last_range[1], last_range[2]], [line.y0, line.y1])
        if over_lap > 0.3:
            line.total_lineindex = last_range[0]
            for b in line.blockbox:
                b.total_lineindex = last_range[0]
            table.body_line_map[line.total_lineindex] += line.blockbox
        else:
            table.body_line_map[line.total_lineindex] = line.blockbox
        last_range = [line.total_lineindex, line.y0, line.y1]


def gen_body_columnindex_map(table):
    table.body_column_map = {}
    # body column converge
    for line in table.body:
        for unit in line.blockbox:
            if unit.columnIndex in table.body_column_map:
                table.body_column_map[unit.columnIndex].append(unit)
            else:
                table.body_column_map[unit.columnIndex] = [unit]

def checkIfIsSubjectColumn(blocks):
    for b in blocks:
        pure_text = subject_match_tools.getPureSbuectText(b.text)
        if pure_text in standerSubjectLib.subjects:
            return True
    return False


def gen_subject_map(table):
    table.subject_map = {}

    # 获取索引列
    index_h = []
    for i in table.header.header_columns:
        h = table.header.header_columns[i]
        if h.identity == 'index':
            index_h.append(i)
    index_clounm = min(index_h) if len(index_h) else -1

    # 确定科目列范围(中国的话其实完全可以默认第一列就是科目列)
    indexs = sorted(table.body_column_map)
    subject_range = []
    for i, index in enumerate(indexs):
        if i == 0:
            subject_range.append(index)
            continue
        header = table.header.header_columns.get(index, None)
        if header is not None and header.identity == 'value':
            break
        # 小于索引列的都是值列
        if index < index_clounm:
            subject_range.append(index)
        # 判断是不是科目列
        elif not checkIfIsSubjectColumn(table.body_column_map.get(index, None)):
            break
        else:
            subject_range.append(index)

    # 根据subject_range生成
    for index in sorted(table.body_line_map.keys()):
        for block in table.body_line_map[index]:
            if block.columnIndex in subject_range:
                if index not in table.subject_map.keys():
                    table.subject_map[index] = block.text
                else:
                    table.subject_map[index] = table.subject_map[index] + block.text
    return True



def lacking_word_fitting(pure_range_text):
    for key in fittingSubjectLib.subject_fittint_box.keys():
        if pure_range_text == key:
            text = re.sub(key, fittingSubjectLib.subject_fittint_box[key], pure_range_text)
            text = re.sub(r'[a-zA-Z]', '', text)
            return text

def wrong_word_fitting(table):
    for index in table.subject_map.keys():
        text = table.subject_map[index]
        wordMap = {
            '臵': '置',
            '小汁': '小计',
            '总汁': '总计',
            '力 口': '加',
            '力口': '加',
            '□': '',
            '△': '',
            '准各金': '准备金',
            '员填列': '号填列',
            '计人': '计入',
            '中内银行': '中国银行',
            '外币报有': '外币报表',
            '这算差额': '折算差额',
            '投注活动': '投资活动',
            '少股股东': '少数股东',
            '投资受到': '投资收到',
            '已决算': '已结算',
            '结耀备Ⲵ金': '结算备付金',
            '金': '金',
            '劢': '动',
            '绊营': '经营',
            '亍': '于',
            '癿': '的',
            '贩建': '构建',
            '贩买': '购买'
        }
        for key in wordMap.keys():
            text = re.sub(key, wordMap[key], text)
        text = re.sub(r'[a-zA-Z]', '', text)
        table.subject_map[index] = text
    return True

def get_range_text(subject_map, index_range):
    text = ''
    for index in sorted(index_range):
        text = text + subject_map[index]
    return text


def get_same_in_subject_lib(subject):
    pure_subject = subject_match_tools.getPureSbuectText(subject)
    lostpart_box = []
    for s in standerSubjectLib.subjects:
        com_part = s[0: len(pure_subject)]
        if com_part == pure_subject:
            lostpart = s[len(pure_subject):]
            if lostpart != '':
                lostpart_box.append(lostpart)
    return lostpart_box

def is_overlap_with_nextline_and_fitting(position, line_indexs, subject_map):
    if position+1 >= len(line_indexs):
        return False
    cur_subject = subject_map[line_indexs[position]]
    next_subjecct = subject_map[line_indexs[position+1]]

    lostpart_box = get_same_in_subject_lib(cur_subject)
    # lostpart_box = fitting_map

    for lostpart in lostpart_box:
        lostpart = unicode(lostpart, 'utf-8')
        findAll = True
        next_subjecct_copy = unicode(copy.deepcopy(next_subjecct), 'utf-8')
        # for i in range(0, len(lostpart)):
        for lost_char in lostpart:
            # lost_char = lostpart[i]
            # print lost_char
            if lost_char in next_subjecct_copy:
                next_subjecct_copy = next_subjecct_copy.replace(lost_char, '', 1)
            else:
                findAll = False
                break

        # print str(findAll) + ' ' + lostpart + '  ' + next_subjecct_copy
        pure_next_subjecct_copy = subject_match_tools.getPureSbuectText(next_subjecct_copy.encode('utf-8'))
        if findAll and pure_next_subjecct_copy in standerSubjectLib.subjects:
            subject_map[line_indexs[position]] = (cur_subject + lostpart).encode('utf-8')
            subject_map[line_indexs[position + 1]] = (next_subjecct_copy).encode('utf-8')
            return True

    return False

def is_useless(pure_range_text):
    useless_falg = ['法人代表', '公司负责人', '法定代表人', '单位负责人']
    for u in useless_falg:
        if u in pure_range_text:
            return True

    useless_box = ['项目', '……']
    return pure_range_text in useless_box

def subject_merge(table, para):
    # pdf少字多字集合
    table.subject_map_merged = {}
    line_indexs = sorted(table.subject_map.keys())
    position = 0

    is_over = False
    is_new_subject = False
    # subject_statistics = []

    while 1:
        if position+1 > len(line_indexs) or is_over:
            break

        for crange in [5, 4, 3, 2, 1]:
            if position + crange > len(line_indexs):
                continue
            index_range = line_indexs[position: position + crange]
            range_text = get_range_text(table.subject_map, index_range)
            # 科目去掉无用的字符
            pure_range_text = subject_match_tools.getPureSbuectText(range_text)

            # print pure_range_text

            if pure_range_text in standerSubjectLib.subjects:
                if pure_range_text == '其他综合收益总额' and crange != 1:
                    continue
                if not position + 1 >= len(line_indexs):
                    pure_next_subject = subject_match_tools.getPureSbuectText(table.subject_map[line_indexs[position + 1]])
                    if crange == 1 and pure_next_subject not in standerSubjectLib.subjects and is_overlap_with_nextline_and_fitting(position,line_indexs,table.subject_map):
                        table.subject_map_merged[str(line_indexs[position])] = table.subject_map[line_indexs[position]]
                        position = position + 1
                        continue

                table.subject_map_merged[tools.linkStr(index_range, '_')] = range_text
                position = position + crange
                # 记录到科目统计表中
                # subject_statistics.append("('{}','{}','{}','{}')".format(range_text,pure_range_text,table.reportid,table.table_type))
                break
            elif crange == 1:
                # 在当前position下判断到最后一个在库里都没有找到subject，则subject_merge(table)认为在这个位置上由新科目
                if is_useless(pure_range_text):
                    position = position + crange
                    break
                # 判断是不是和下一行重叠了
                elif is_overlap_with_nextline_and_fitting(position,line_indexs,table.subject_map):
                    table.subject_map_merged[str(line_indexs[position])] = table.subject_map[line_indexs[position]]
                    position = position + 1

                # 判断是不是少字，多字的情况，修正
                elif pure_range_text in fittingSubjectLib.subject_fittint_box.keys():
                    text = lacking_word_fitting(pure_range_text)
                    table.subject_map_merged[tools.linkStr(index_range, '_')] = text
                    position = position + crange
                    break
                else:
                    # print range_text+','+pure_range_text
                    if min(index_range) > table.body_max_lineindex:
                        is_over = True
                        break
                    else:
                        print ',[NEW_SUBJECT],' + table.reportid + ',' + str(table.pageNum) + ','  + str(position) + ','  + para.sector_code + ',' + para.sector_name + ',' + re.sub(',', '', range_text) + ',' + pure_range_text
                        configManage.logger.error(',[NEW_SUBJECT],' + table.reportid + ',' + str(table.pageNum) + ','  + str(position) + ',' + re.sub(',', '', range_text) + ',' + pure_range_text)
                        is_new_subject = True
                        table.subject_map_merged[tools.linkStr(index_range, '_')] = pure_range_text
                        position = position + crange
                        # raise Exception('NEW_SUBJECTERROR')



    # 记录到科目统计表中
    # sql = 'insert into subject_statistics(original_subject, match_subject, report_id, table_type) values{values}'
    # sql = sql.format(values=','.join(subject_statistics))
    # dbtools.query_pdfparse(sql)
    if is_new_subject:
        configManage.logger.error(',[NEW_SUBJECT],1')
    return is_new_subject


def structure(tablebox, para):
    is_new_subject = False
    for table in tablebox:
        # 拟合一行多列的情况（修改了右边正文部分block的lineindex和columnindex， 删除了无用的header）
        solve_multi_subject_column(table)

        # 生成以lineindex为key的bodymap
        gen_body_lineindex_map(table)

        # 生成正文列索引map
        gen_body_columnindex_map(table)

        # 生成subject集合
        gen_subject_map(table)

        # 修正科目错别字
        wrong_word_fitting(table)

        # 科目合并(新科目的发现也是在这里)
        if subject_merge(table, para):
            is_new_subject = True
    if is_new_subject:
        raise Exception('NEW_SUBJECTERROR')