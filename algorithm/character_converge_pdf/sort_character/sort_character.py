# -*- coding:utf-8 -*-
import csv
import operator
import re

from algorithm.character_converge_pdf.character_converge_exceptions import SourceColumnNumError
from algorithm.character_converge_pdf.container.character import Character
from algorithm.common import tools, configManage


def charSortFun(second, first):
    # if second.pageNum==4:
    #     pass
    OVERLAP_P = 0.6
    # 1 stay -1 change
    # pagenum direction x0,y0
	# 货币单位需要特殊处理，只要和其它的字符有相交就认为是在同一行。印度货币单位会被解析成`

    # print '---------------------------------------'
    # print first.text + '    ' + str(first.x0) + '    ' + str(first.x1) + '    ' + str(first.y0) + '    ' + str(first.y1) + '   ' + str(first.pageNum)
    # print second.text + '    ' + str(second.x0) + '    ' + str(second.x1) + '    ' + str(second.y0) + '    ' + str(second.y1) + '   ' + str(second.pageNum)

    if first.pageNum > second.pageNum:
        return -1
    elif first.pageNum < second.pageNum:
        return 1
    elif first.pageNum == second.pageNum:
        if first.direction > second.direction:
            return 1
        elif first.direction < second.direction:
            return -1
        elif first.direction == second.direction:
            overlap = tools.overlapRate([first.y0, first.y1], [second.y0, second.y1], 0)
            if (tools.comparexy(first.y0, second.y0) or overlap >= OVERLAP_P) and first.x0 > second.x0:  # 在统一行， 且1再2的右边，换位
                return -1
            elif first.y0 < second.y0 and overlap < OVERLAP_P: # 不在同一行，且1在2的下面，换位置
                return -1
            else:  # 其它情况，则，if 和 elif的反义，不用换位置
                return 1


def process_and_judge(data, cBox):
    # 判断长度是否正确
    # if len(data) != 11:
    #     raise Exception('COLUMN_NUM_ERROR')
    # 封装成新字符
    newC = Character(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7], data[8], data[9], data[10])

    # 处理字符值及判断字符是否有用
    useless_char_box = ['_']
    newC.text = re.sub('\s|　', '', newC.text)
    newC.text = newC.text.replace('\xc2\xa0', '')
    newC.text = newC.text.replace('', '')
    newC.text = newC.text.replace('#|#', ',')
    # 去掉cid字符及去掉cid字符
    if newC.text == '' or '(cid:' in newC.text or newC.text in useless_char_box:
        raise Exception('CONTINUE')

    return newC

def get_rid_overlap_chara(cBox):
    new_char_box = []
    for i, curC in enumerate(cBox):
        if i==0:
            continue

        lastC = cBox[i-1]

        # 判断字符是否为重复字符的条件
        j1 = lastC.pageNum == curC.pageNum
        j2 = lastC.direction == curC.direction
        j3 = lastC.size == curC.size
        j4 = tools.comparexy(lastC.y0, curC.y0)
        # j4 = lastC.y0 == curC.y0
        j5 = tools.comparexy(lastC.x0, curC.x0)
        # j5 = lastC.x0 == curC.x0
        j6 = lastC.text == curC.text

        # 去掉重叠在一起的字符
        if j1 and j2 and j3 and j4 and j5 and j6:
            continue
        else:
            new_char_box.append(curC)
    del cBox
    return new_char_box

def gen_index(cBox):
    for i, w in enumerate(cBox):
        if i == 0:
            w.lineIndex = 0
            w.columnIndex = 0
            continue
        lw = cBox[i - 1]
        if w.pageNum != lw.pageNum or w.direction != lw.direction:
            w.lineIndex = 0
            w.columnIndex = 0
        else:
            overlap = tools.overlapRate([w.y0, w.y1], [lw.y0, lw.y1],0)
            if tools.comparexy(w.y0, lw.y0) or overlap >= 0.85:
                w.lineIndex = lw.lineIndex
                w.columnIndex = lw.columnIndex + 1
            else:
                w.lineIndex = lw.lineIndex + 1
                w.columnIndex = 0

def process(p_country, p_company, p_reportid):
    datapath = configManage.config['location']['pdf_source'] + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"
    datapath = datapath.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)


    cBox = []
    with open(datapath, 'rb') as f:
        content = csv.reader(f)
        for data in content:
            try:
                newC = process_and_judge(data, cBox)
                cBox.append(newC)
            except Exception as e:
                if e.message == 'CONTINUE':
                    continue
                else:
                    raise Exception('CHARACTER_CONVERAGE_ERROR')


    cBox.sort(cmp=charSortFun)

    # 去掉重叠字符
    cBox = get_rid_overlap_chara(cBox)

    # 生成lineIndex
    gen_index(cBox)

    char_map = {}
    for i, c in enumerate(cBox):
        c.orderid = i
        if c.pageNum not in char_map:
            char_map[c.pageNum] = [c]
        else:
            char_map[c.pageNum].append(c)

    return char_map
