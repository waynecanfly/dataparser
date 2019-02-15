# -*- coding:utf-8 -*-

import re
import sys

from algorithm.character_converge_pdf import judge_text_type
from algorithm.character_converge_pdf.container.block import Block
from algorithm.common import tools


def overlapRate(firstYRange, secondYRange):
    if firstYRange[0] > secondYRange[1] or secondYRange[0] > firstYRange[1]:
        return 0
    else:
        borderList = (firstYRange + secondYRange)
        borderList.sort()
        firstGap = abs(firstYRange[1] - firstYRange[0])
        secondGap = abs(secondYRange[1] - secondYRange[0])
        overlapGap = abs(borderList[2] - borderList[1])
        return overlapGap / min(firstGap, secondGap) if min(firstGap, secondGap) != 0 else 1


def genBlockWithWordbox(wordBox, country):
    newBlock = Block(wordBox[0], country)
    for i in range(1, len(wordBox)):
        newBlock.addNewWord(wordBox[i])
        newBlock.type = judge_text_type.judge(newBlock.text)
    return newBlock

def addNewBlock(box, block, country):
    # if block.pageNum == 62:
    #     pass
    # 此函数用于拆开连续重复的文本如： 上年统计上年统计  拆成不同的两个
    curWBox = []
    reWBox = []
    curWtext = set()
    reWtext = set()

    for w in block.wordBox:
        rule = '((january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december))|((jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(jl)|(aug)|(sep)|(sept)|(oct)|(nov)|(dec))'
        text  = re.sub(rule, '#', w.text.lower())
        text = re.sub('[0-9]', '*', text)
        text = re.sub('\s', '', text)

        if text not in curWtext:
            curWBox.append(w)
            curWtext.add(text)
        else:
            reWBox.append(w)
            reWtext.add(text)

    if curWtext == reWtext:
        box.append(genBlockWithWordbox(curWBox, country))
        box.append(genBlockWithWordbox(reWBox, country))
    else:
        box.append(block)

def blockConvergeNoTable(wordBox, country, beginLineNum):
    for i, w in enumerate(wordBox):
        if i == 0:
            w.lineIndex = beginLineNum
            w.columnIndex = 0
            continue
        lw = wordBox[i - 1]
        if  w.direction != lw.direction:
            w.lineIndex = lw.lineIndex + 1
            w.columnIndex = 0
        else:
            overlap = overlapRate([w.y0, w.y1], [lw.y0, lw.y1])
            if tools.comparexy(w.y0, lw.y0) or overlap >= 0.6:  # 这个值甚至可以再严格一点,表中文到时重新分行
                w.lineIndex = lw.lineIndex
                w.columnIndex = lw.columnIndex + 1
            else:
                w.lineIndex = lw.lineIndex + 1
                w.columnIndex = 0

    #word to block & recognize block type: NumOrder, phrase, sentence,value ...
    blockBox_total = []
    curBlock = Block(wordBox[0], country)

    for i in range(1, len(wordBox)):
        w = wordBox[i]
        if curBlock.status == 'close':
            # addNewBlock(blockBox_total,curBlock, country)
            blockBox_total.append(curBlock)
            curBlock = Block(w, country)
        else:
            result = curBlock.add(w)
            if result == 'reject':
                # addNewBlock(blockBox_total, curBlock, country)
                blockBox_total.append(curBlock)
                curBlock = Block(w, country)
    # addNewBlock(blockBox_total, curBlock, country)
    blockBox_total.append(curBlock)

    blockBox = [block for block in blockBox_total if re.sub('\s', '', block.text)!='']

    return blockBox


def overlapRate_compare_first(firstYRange, secondYRange):
    if firstYRange[0] > secondYRange[1] or secondYRange[0] + 2> firstYRange[1]:
        return 0
    borderList = (firstYRange + secondYRange)
    borderList.sort()
    firstGap = abs(firstYRange[1] - firstYRange[0])
    overlapGap = abs(borderList[2] - borderList[1])
    return overlapGap / firstGap if firstGap != 0 else 1

def getLineOrder(w, aimRange, checkRange, lines, segmentMap, lineOrderMap, lineTable, isX=False):
    # if w.orderid >= 47687:
    #     print 'd'
    # setp 1 : X
    # aimPoint = (aimRange[0] + aimRange[1]) / 2
    # 单个字符的word通常是一些符号，当这些符号在线的边上时，解出来的范围很容易比看起来的更靠右边，所以这种情况下，当分析的时X轴的参考点不能取中点，要取左边的点
    # if len(w.text) <= 1 and isX:
    #     aimPoint = aimRange[0]
    # elif len(w.text) <= 1 and not isX:
    #     aimPoint = aimRange[1]


    checkRange = [round(checkRange[0]) + 1, round(checkRange[1]) - 1]

    aimLines = []
    for l in lines:
        lSeg = segmentMap.get(l)
        for seg in lSeg:
            # seg[0] <= checkRange[0] and seg[1] >= checkRange[1]
            over_lap = tools.overlapRate(seg, checkRange)
            if over_lap> 0.3:  # 只要相交超过百分之30就行
                aimLines.append(l)
                break

    if aimLines == []:
        aimLines = lines  # 有风险，不能这么做

    # 生成目标线范围
    match_range_order_map = {}
    aimLines = sorted(aimLines)
    for i, l in enumerate(aimLines):
        if i+1 == len(aimLines):
            break
        border1 = l
        border2 = aimLines[i+1]
        border1_order = lineOrderMap[border1]
        border2_order = lineOrderMap[border2]
        match_range_order_map[str(border1_order) + '_' + str(border2_order)] = [border1, border2]


    overlap_with_aimrange = {}

    for k in match_range_order_map:
        v = match_range_order_map[k]
        overlap_with_aimrange[overlapRate_compare_first(aimRange, v)] = k

    max_overlap_key = overlap_with_aimrange[max(overlap_with_aimrange.keys())].split('_')
    max_overlap_key = [int(x) for x in max_overlap_key]
    return max_overlap_key
    # for i, l in enumerate(aimLines):
    #     if i+2 == len(aimLines):
    #         # if tools.overlapRate(aimRange, [l, aimLines[i + 1]]) > 0:
    #         return [lineOrderMap[l], lineOrderMap[aimLines[i+1]]]
    #
    #
    #     if l <= aimPoint and aimLines[i+1] >= aimPoint:  # 以后考虑改成用重叠率进行衡量
    #         return [lineOrderMap[l], lineOrderMap[aimLines[i+1]]]

def blockConvergeWithTable(wordBox, lineTable, beginLineNum):
    blockbox = []
    # step 0: 准备行列号
    h_ypoint_list = sorted(lineTable.h_segment_map.keys(), reverse=True)
    h_value_order_map = {}
    h_order_value_map = {}
    for i, h in enumerate(h_ypoint_list):
        h_value_order_map[h] = i
        h_order_value_map[i] = h

    v_xpoint_list = sorted(lineTable.v_segment_map.keys())
    min_order = sys.maxint
    max_order = 0
    v_value_order_map = {}
    v_order_value_map = {}
    for i, h in enumerate(v_xpoint_list):
        v_value_order_map[h] = i
        v_order_value_map[i] = h
        min_order = i if i < min_order else min_order
        max_order = i if i > max_order else max_order

    # setp 1: 给每个word分配行列号, 顺序id, 重置位置值
    h_ypoint_list.reverse()
    for w in wordBox:
        # getLineOrder 需要重构，这里也不需要调用两次传那么多参数
        w.v_order = getLineOrder(w, [w.x0, w.x1], [w.y0, w.y1], v_xpoint_list, lineTable.v_segment_map, v_value_order_map, lineTable, True)
        w.h_order = getLineOrder(w, [w.y0, w.y1], [w.x0, w.x1], h_ypoint_list, lineTable.h_segment_map, h_value_order_map, lineTable)
        w.h_order.reverse()
        w.orderID = str(w.h_order[0]) + '_' + str(w.h_order[1]) + '_' + str(w.v_order[0]) + '_' + str(w.v_order[1])


    # setp 2: 按行列号分组，合并成block, block, x0,y0,x1,y1由行号设置. block里要有tableid码，以及行号列号
    orderIdMap = {}
    for w in wordBox:
        if w.orderID not in orderIdMap:
            orderIdMap[w.orderID] = [w]
        else:
            orderIdMap[w.orderID].append(w)

    for key in orderIdMap.keys():
        values = orderIdMap[key]
        values = sorted(values, key= lambda v: v.orderid)
        blockbox.append(Block(values, None, (lineTable.id, v_order_value_map, h_order_value_map, beginLineNum)))

        # 若values里的word左右两边为线为最左和最后的，则value里的每一个word单独成一个block, 且不计算进表内(规则废弃)
        # left_order = key.split('_')[2]
        # right_order = key.split('_')[3]
        # if int(left_order) == min_order and int(right_order) == max_order:
        #     for v in values:
        #         nb = Block([v], None, (lineTable.id,  v_order_value_map, h_order_value_map, beginLineNum))
        #         nb.lineTableId = None
        #         blockbox.append(nb)
        # else:
        #     blockbox.append(Block(values, None, (lineTable.id,  v_order_value_map, h_order_value_map, beginLineNum)))

    # 排序
    blockbox.sort(cmp=blockSoreFunc)

    return blockbox

def blockSoreFunc(a, b):
    # -1 位置不变，1调换位置，a，b的顺序不是原集合的顺序
    if a.talbeLineIndexs[0] < b.talbeLineIndexs[0]:
        return -1
    elif a.talbeLineIndexs[0] > b.talbeLineIndexs[0]:
        return 1
    elif a.talbeColumnIndexs[0] < b.talbeColumnIndexs[0]:
        return -1
    elif a.talbeColumnIndexs[0] > b.talbeColumnIndexs[0]:
        return 1
    else:
        return 1

def wordBlongTable(word, lineTable):
    for t in lineTable:
        if (word.y0 >= t.bottom and word.y1 <= t.top) or tools.overlapRate([word.y0, word.y1], [t.bottom, t.top]) > 0.3: # 和bottom相交的也认为时表的一部分
            return t.id
    return 'NO_TABLE'

def converge_with_line(wordbox, linetable, country):
    # splitWordboxMap = []
    page_blockbox = []
    curBelong = None
    curWordBox = []
    curStartLine = 0
    for w in wordbox:
        # if w.pageNum == 54:
        #     print w.text + '  ' + str(w.orderid)
        belong = wordBlongTable(w, linetable)
        if curBelong == None:
            # new curbox
            curBelong = belong
            curWordBox = [w]
        elif belong != curBelong:
            blockbox = None
            if curBelong != 'NO_TABLE':
                # 处理当强box
                try:
                    blockbox = blockConvergeWithTable(curWordBox, [t for t in linetable if t.id == curBelong][0],
                                                      curStartLine)
                except:
                    blockbox = blockConvergeNoTable(curWordBox, country, curStartLine)
                if blockbox is None:
                    pass
                page_blockbox = page_blockbox + blockbox
            else:
                # 处理当强box
                blockbox = blockConvergeNoTable(curWordBox, country, curStartLine)
                page_blockbox = page_blockbox + blockbox

            # new curbox
            curBelong = belong
            curWordBox = [w]
            curStartLine = blockbox[-1].lineIndex + 1
        elif belong == curBelong:
            # 当前word和属于当前区域的wordbox，直接添加
            curWordBox.append(w)

    # 处理页码最后的文本块
    if curBelong != 'NO_TABLE':
        # 处理当前box
        blockbox = []
        try:
            blockbox = blockConvergeWithTable(curWordBox, [t for t in linetable if t.id == curBelong][0],
                                              curStartLine)
        except:
            blockbox = blockConvergeNoTable(curWordBox, country, curStartLine)
        page_blockbox = page_blockbox + blockbox
    else:
        # 处理当强box
        blockbox = blockConvergeNoTable(curWordBox, country, curStartLine)
        page_blockbox = page_blockbox + blockbox
    return page_blockbox

def process(wordBoxMap, lineTableBox, country):
    # 行列划分
    allBlockBox = []
    for pageNum in sorted(wordBoxMap.keys()):
        if pageNum == 125:
            pass
        wordbox = wordBoxMap[pageNum]
        linetable = lineTableBox.get(pageNum, None)
        if linetable != None:
            allBlockBox = allBlockBox + converge_with_line(wordbox, linetable, country)
        else:
            blockbox = blockConvergeNoTable(wordbox, country, 0)
            allBlockBox = allBlockBox + blockbox

    return allBlockBox
