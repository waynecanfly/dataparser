# -*- coding: UTF-8 -*-
import copy
import re

from algorithm.capture_table_pdf.containers.headerUnit import HeaderUnit


def replaceTimeAndUseless(text):
    # pureText = re.sub("[\(|\)|\s|`|\'|#|\*]", '', text).lower()  #此处空白字符为 0xe3 暂时先加上去，后续研究这一类问题
    pureText = re.sub("[\(|\)|\s|`|\'|#|:]", '', text)  #此处空白字符为 0xe3 暂时先加上去，后续研究这一类问题
    pureText = pureText.replace('（', '')
    pureText = pureText.replace('）', '')
    pureText = pureText.replace('、', '')
    pureText = pureText.replace('续', '')

    pureText = pureText.replace("：", "")

    pureText = re.sub('[0-9]', '*', pureText).lower()  # 把数字换为星号

    result = re.sub(
        '((january)|(february)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december))|((jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(jl)|(aug)|(sep)|(sept)|(oct)|(nov)|(dec))',
        '#', pureText).lower()

    result = re.sub('(一)|(二)|(三)|(四)|(五)|(六)|(七)|(八)|(九)|(十)|(零)', '*', result)
    result = re.sub('(one|two|three|four|five|six|seven|eight|night|ten)', '*', result)
    result = re.sub('(unaudited|audited|restated)', '', result)
    return result


def getMatchText(text):
    try:
        if int(text) >= 1990 and int(text) <= 2029:             # 根据合并列文字，若为合理时间返回年份正则
            return '^[1,2][0,9][0,1,2,9][0-9]$'
        else:
            return replaceTimeAndUseless(text)                  # 这个方法就是把数字换成*      把空格干掉   把月份换成#
    except ValueError:
        return replaceTimeAndUseless(text)

def mergeHeader(header, mergeOne):
    if header.identity == 'value':
        header.text = mergeOne.text + ' ' + header.text
        header.y0 = mergeOne.y0

def calculateFittingDirection(top, buttom):
    # 初步判断是否需要拟合：
    if (top.x0 < buttom.x0 and top.x1 > buttom.x1) or (
            buttom.x0 < top.x0 and buttom.x1 > top.x1):
        return 0
    # 计算错位率（实际不直接计算错位率， 通过重叠率算）
    xRange = sorted([top.x0, top.x1, buttom.x0, buttom.x1])
    overlapRate = abs(xRange[1] - xRange[2])/(top.x1 - top.x0)
    if overlapRate > 0.8:
        return 0

    direction = 1 if top.x0>buttom.x0 else -1 # 1为右边， -1 为左边
    return direction


def genHeaderByColumnBlock(columnIndex, blockbox):
    curHeader = None
    for block in blockbox:
        if curHeader:
            curHeader.addBlock(block)
        else:
            curHeader = HeaderUnit(columnIndex, block)
    return curHeader

# 列分发及值列宽度重新计算
def fittingHeaderWidth(blockbox):
    line_block_map = {}
    column_block_map = {}
    for block in blockbox:
        if isinstance(block, int):
            pass
        if block.lineIndex in line_block_map.keys():
            line_block_map[block.lineIndex].append(block)
        else:
            line_block_map[block.lineIndex] = [block]
        for columnIndex in block.columnIndexs:
            if columnIndex in column_block_map.keys():
                column_block_map[columnIndex].append(block)
            else:
                column_block_map[columnIndex] = [block]

    column_block_map_merge = copy.deepcopy(column_block_map)


    lines = sorted(line_block_map.keys())
    for i, line in enumerate(lines):
        if i+1 == len(lines):
            continue # 最后一行不做任何处理
        lineBlock = line_block_map[line]
        valueBlock = [block for block in lineBlock if block.identity == 'value']
        for block in valueBlock:
            # 已经有两个重叠的,不做任何处理
            if len(block.columnIndexs) > 1:
                continue
            if len(block.columnIndexs) == 0:
                raise Exception('column divide error')
            blockColumnIndex = block.columnIndexs[0]
            curColumnBlocks = column_block_map.get(blockColumnIndex)
            overlapNum = len(curColumnBlocks) - 1
            # 有一个重叠
            if overlapNum == 1:
                overlapBlock = curColumnBlocks[1]
                # 计算拟合方向
                direction = calculateFittingDirection(block, overlapBlock)
                if direction:
                    fittingColumnIndex = blockColumnIndex + direction
                    fittingColumns = column_block_map.get(fittingColumnIndex, 0)
                    # 判断是否需要拟合： 1. 能计算出拟合方向 2. 拟合列长度为1 3. 拟合列block再当前block下面 4. 拟合列block为value
                    if fittingColumns and len(fittingColumns) == 1 and fittingColumns[0].lineIndex>line and fittingColumns[0].identity=='value':
                        # 确定拟合.把当前block放到拟合列的第一个位置上
                        column_block_map_merge[fittingColumnIndex].insert(0, block)
            # 非最后一行不和下面的行重叠的值列
            elif overlapNum == 0:
                leftFittingIndex = blockColumnIndex-1
                rightFittingIndex = blockColumnIndex+1
                leftBlocks = column_block_map.get(leftFittingIndex, 0)
                rightBlocks = column_block_map.get(rightFittingIndex, 0)
                # 1.拟合列长度为1
                if leftBlocks and rightBlocks and len(leftBlocks) >= 1 and len(rightBlocks) >= 1:
                    left = leftBlocks[0]
                    right = rightBlocks[0]
                    # 2. 拟合列block再当前block下面 3.
                    if left.lineIndex > line and right.lineIndex > line and left.identity in ('value', '') and right.identity in ('value', ''):
                        # 符合要求，加左右两列，去掉当前列
                        column_block_map_merge[leftFittingIndex].insert(0, block)
                        column_block_map_merge[rightFittingIndex].insert(0, block)
                        column_block_map_merge.pop(blockColumnIndex)

    columnI = sorted(column_block_map_merge.keys())
    # print '=------------------------' + str(blockbox[0].pageNum)
    # for i in columnI:
    #     columns = column_block_map_merge[i]
    #     headerT = ''
    #     for c in columns:
    #         headerT = headerT + re.sub('\n', '',c.text)
    #     print headerT
    # print '=------------------------'


    # 封装成map返回过去。把列Index放大。
    index_header_map = {}
    for i in columnI:
        bigIndex = (i+1) * 10000
        columns = column_block_map_merge[i]
        header = genHeaderByColumnBlock(i, columns)
        header.columnIndex = bigIndex
        index_header_map[bigIndex] = header
        # print header.text


    #拟合值列中的重叠和空隙。PS：最后一个值列向后覆盖没有做
    headerIndexs = sorted(index_header_map.keys())
    for i,index in enumerate(headerIndexs):
        header = index_header_map[index]
        if header.identity == 'value' and i+1 < len(headerIndexs):
            nextHeader = index_header_map[headerIndexs[i + 1]]
            midPoint = abs((header.x1+nextHeader.x0)/2)
            header.x1 = midPoint
            nextHeader.x0 = midPoint+1
    return index_header_map


if __name__ == '__main__':
    result = getMatchText('负债和股东权益 (续)')
    print result

