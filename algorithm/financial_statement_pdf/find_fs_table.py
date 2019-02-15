# -*- coding: UTF-8 -*-
import copy

from algorithm.capture_table_pdf.capture_table_exceptions import StatementNotAllFound
from algorithm.common import configManage, dbtools
from algorithm.common_tools_pdf import subject_match_tools, standerSubjectLib, header_match_tools
from algorithm.financial_statement_pdf import fs_pdf_tools, fs_pdf_check
from algorithm.financial_statement_pdf.containers.table import Table
from algorithm.financial_statement_pdf.find_fs_header import find_fs_header

# @check:header有没有被全部找到
def check_tablebox(tablebox):
    tabletype = set()
    for table in tablebox:
        tabletype.add(table.table_type)
    if len(tabletype) >= 3:
        return True
    else:
        raise Exception('NOT_ALL_FOUND_HEADER')

def getPatterns():
    ps_box = []
    headers = dbtools.query_pdfparse("select distinct orig_text from opd_structure_pattern")
    for h in headers:
        text = header_match_tools.getMatchText(h[0].encode('utf-8'))
        ps_box.append(text)
    return ps_box

def output_lost_header(reportid, line_box, lost_anchor_box):
    patterns = getPatterns()
    for anchor in lost_anchor_box:
        find_area = line_box[anchor['index'] + 1: anchor['index'] + 10]

        header_begin = -1
        header_end = 0
        for i, l in enumerate(find_area):
            if l.linetableid is None:
                continue
            if header_begin == -1:
                header_begin = i
            pure_l = subject_match_tools.getPureSbuectText(l.text)
            if pure_l in standerSubjectLib.subjects:
                header_end = i
                break
        if header_begin == -1:
            continue
        header_range = find_area[header_begin: header_end]

        lineindex_map = {}
        for h in header_range:
            for b in h.blockbox:
                if b.lineIndex not in lineindex_map:
                    lineindex_map[b.lineIndex] = [b]
                else:
                    lineindex_map[b.lineIndex].append(b)

        lineindexs = sorted(lineindex_map.keys())

# configManage.logger.info('[HEADER],' + reportid + ',' + str(anchor['title_pageNum']))
        columnsMap = {}
        for lineI in lineindexs:
            line = lineindex_map[lineI]

            for b in line:
                for i in b.lineColumnIndex:
                    if i not in columnsMap:
                        columnsMap[i] = b.text
                    else:
                        columnsMap[i] += b.text

# configManage.logger.info('[HEADER],,' + h_text)


        out_box = []
        for i in sorted(columnsMap):
            value = columnsMap[i]
            pure_value = header_match_tools.getMatchText(value)

            if pure_value not in patterns:
                out_box.append(value + ',' + pure_value)
        if out_box:
            configManage.logger.info('[HEADER],' + reportid + ',' + str(anchor['title_pageNum']))
            for o in out_box:
                configManage.logger.info('[HEADER],,' + o)


def find_fs_table(title_anchor, line_box, p_reportid):
    # 获取匹配所用表头库（不应该在这出现)
    patterns = fs_pdf_tools.getPatterns()

    table_box = []

    TABLE_LEN_THR = 10

    lost_anchor_box = []


    for anchor in title_anchor:

        # 获取该title所覆盖的有效范围（有效范围为该tilt和下一个title之间）
        find_area = line_box[anchor['table_range'][0]: anchor['table_range'][1]]

        # 若find_area小于阈值，直接去掉
        if len(find_area) < 10:
            continue

        # 识别表头
        header = find_fs_header(p_reportid, find_area, patterns)

        if header == 'NOT FOUND':
            # 判断是否为有标题无表头的续表
            j1 = len(table_box) and table_box[-1].title['table_type'] == anchor['table_type']
            j2 = len(table_box) and abs(anchor['title_pageNum'] - max(table_box[-1].table_page_ragne)) <= 1
            if j1 and j2:
                last_table = table_box[-1]
                header = copy.deepcopy(last_table.header)
                #当last_table是有线的话，重新计算header范围（范围应为0）
                header.header_range_uncertainty = True
            else:
                lost_anchor_box.append(anchor)
                continue

        # 生成表对象 并为列索引值（columnIndex）赋值
        table = Table(anchor, header, find_area, line_box, p_reportid)
        if table.body:
            table_box.append(table)

        # 检查该表正文是否完整，以及表后面区域是否可能存在未被发现的有用的表（替代现有的检查模块）


    # @check :检查表是否完整
    try:
        check_tablebox(table_box)
    except Exception as e:
        output_lost_header(p_reportid,line_box, lost_anchor_box)
        raise e


    # 一个pdf中找出多个同类型表时，判断是否有些是无用的需要过滤掉(待检验)
    table_box = fs_pdf_tools.same_kind_table_filter(table_box)


    # @check :检查每个表的正文完整性
    for t in table_box:
        fs_pdf_check.check_integrality(t)

    return table_box

