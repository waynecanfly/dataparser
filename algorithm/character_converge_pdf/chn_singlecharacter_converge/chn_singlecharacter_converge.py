# -*- coding:utf-8 -*-


lib = [
    '资产负债表'
    '报表项目',
    '合并现金流量表',
    '合并资产负债表',
    '合并利润表',
    '现金流量表',
    '资产负债表',
    '利润表',
    '期末数',
    '期初数',
    '本期金额',
    '上期金额',
    '期末余额',
    '年初余额',
    '合并',
    '母公司',
    '本期发生额',
    '上期发生额',
    '本期数',
    '上年同期数',
    '上年金额',
    '年初数',
    '本年金额',
    '期初余额',
    '年末数',
    '本年发生额',
    '上年发生额',
    '年末余额',
    '年初金额',
    '上期数',
    '上年数',
    '年末金额',
    '本年数',
    '公司',
    '上年同期',
    '本期',
    '期末金额',
    '上年同期金额',
    '序号',
    '本期发生数',
    '上期发生数',
    '注释',
    '期初金额',
    '上年发生数',
    '本年发生数',
    '合并数',
    '期末',
    '期初',
    '负债和股东权益',
    '负债及股东权益',
    '注释号',
    '行次',
    '本年累计数',
    '母公司数',
    '上年累计数',
    '附注编号',
    '本年度',
    '本期累计数',
    '上年度',
    '附注号',
    '公司数',
    '附註',
    '本期累计',
    '行次注释',
    '资产',
    '项目',
    '附注',
    '资产类'
       ]

def checkIfMerge(mergeRange):
    mergeText = ''
    for b in mergeRange:
        mergeText = mergeText + b.text
    return True if mergeText in lib else False
        # for b in mergeRange[1:]:
        #     mergeRange[0].text = mergeRange[0].text + b.text

def merge(mergeRange):
    for b in mergeRange[1:]:
        mergeRange[0].text = mergeRange[0].text + b.text
        mergeRange[0].wordBox = mergeRange[0].wordBox + b.wordBox
        mergeRange[0].x0 = mergeRange[0].x0 if mergeRange[0].x0 < b.x0 else b.x0
        mergeRange[0].x1 = mergeRange[0].x1 if mergeRange[0].x1 > b.x1 else b.x1
        mergeRange[0].y0 = mergeRange[0].y0 if mergeRange[0].y0 < b.y0 else b.y0
        mergeRange[0].y1 = mergeRange[0].y1 if mergeRange[0].y1 > b.y1 else b.y1
        b.text = None

def mergeBlocks(curMergeBox):
    for i, block in enumerate(curMergeBox):
        if block.text != None:
            mergeEnd = len(curMergeBox)
            while i < mergeEnd:
                mergeRange = curMergeBox[i: mergeEnd]
                isMerge = checkIfMerge(mergeRange)
                if isMerge:
                    merge(mergeRange)
                    break
                else:
                    mergeEnd = mergeEnd - 1

def process(blockBox):
    curMergeBox = []
    position = 0
    while position + 1 <= len(blockBox):

        curBlock = blockBox[position]

        if len(curBlock.text) == 1:  # 长度为1，而且不能跨行，不能跨页(现未加不可跨页条件，以后完善)
            curMergeBox.append(curBlock)
        elif len(curMergeBox) >= 2:
            mergeBlocks(curMergeBox)
            curMergeBox = []
        else:
            curMergeBox = []
        position = position + 1
    if len(curMergeBox) >= 2:
            mergeBlocks(curMergeBox)

    # 过滤掉已经merge到别的block的blcok
    blockBox = [b for b in blockBox if b.text != None]

    return blockBox
