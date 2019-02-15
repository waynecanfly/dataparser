# -*- coding:utf-8 -*-

from containers.headerUnit import HeaderUnit
from algorithm.common import dbtools
from algorithm.common_tools_pdf import header_match_tools, column_divide_tools
from containers.table import Table


# def mergeBlock(header, addBlock):
#     header.text = header.text + ' ' + addBlock.text
#     header.lineIndexs.append(addBlock.lineIndex)
#     header.x0 = (addBlock.x0 if addBlock.x0 < header.x0 else header.x0)
#     header.y0 = (addBlock.y0 if addBlock.y0 < header.y0 else header.y0)
#     header.x1 = (addBlock.x1 if addBlock.x1 > header.x1 else header.x1)
#     header.y1 = (addBlock.y1 if addBlock.y1 > header.y1 else header.y1)

def sortByMultiLine(column_block_map):
    # 把跨多行的header排到前面去
    index = []
    tl = []
    for key in column_block_map.keys():
        tl.append([key, len(column_block_map[key])])
    tl = sorted(tl, key=lambda x: x[1], reverse=True)
    for t in tl:
        index.append(t[0])
    return index

def check_header_match(lines, ps, position):
    haveLine = True if lines[0].blockbox[0].linetableid is not None else False

    # blocks
    blockbox = []
    for l in lines:
        for b in l.blockbox:
            blockbox.append(b)

    column_block_map = {}
    # gen column index and converge
    if haveLine:
        for l in lines:
            for b in l.blockbox:
                for index in b.lineColumnIndex:
                    if index in column_block_map:
                        column_block_map[index].append(b)
                    else:
                        column_block_map[index] = [b]


    else:
        referLine = column_divide_tools.culateColumnIndex(blockbox)
        if len(referLine) < 2:
            return False
        # column converge
        for b in blockbox:
            for index in b.columnIndexs:
                if (index+1)*1000 in column_block_map:
                    column_block_map[(index+1)*1000].append(b)
                else:
                    column_block_map[(index+1)*1000] = [b]


    indexs = sorted(column_block_map.keys())
    valueColumnNums = 0
    matchPatterns = []
    for i, index in enumerate(indexs):
        columnText = ''
        for b in column_block_map[index]:
            columnText = columnText + b.text
        columnTextMatch = header_match_tools.getMatchText(columnText)
        isMatch = False
        for pattern in ps:
            # if blockbox[0].pageNum==20 and len(lines) == 1 and position==2:
            #     print pattern.text + ' ' + columnTextMatch
            if pattern.text == columnTextMatch:
                matchPatterns.append(pattern.text)
                isMatch = True
                for block in column_block_map[index]:
                    block.identity = pattern.identity
                if pattern.identity == 'value':
                    valueColumnNums = valueColumnNums + 1
                break
        if not isMatch:
            return False

    # 来到这里证明已经是找到了表的科目
    # 更新匹配次数, 暂时关掉，增加计算速度
    # for matchP in matchPatterns:
    #     dbtools.query_pdfparse("update opd_structure_pattern set num_of_use=num_of_use + 1 where text='" + matchP + "'")



    # 若是有线的表，直接封装返回
    if haveLine:
        multiLineBlock = set()
        index_header_map = {}
        for index in sortByMultiLine(column_block_map):
            blocks = column_block_map[index]

            # 过滤掉只有一行并且该行有和其它行组成一个整体的表头列
            if len(blocks) > 1:
                for b in blocks:
                    multiLineBlock.add(b)
            else:
                if blocks[0] in multiLineBlock:
                    continue

            curHeader = None
            for b in blocks:
                if curHeader is None:
                    curHeader = HeaderUnit(index, b)
                else:
                    curHeader.lineAddBlock(b)
            index_header_map[index] = curHeader
        if len(index_header_map) < 2:
            return False
        return index_header_map



    # 表头拟合 : 1.值列非最后一行独立组成一列时拟合 2. 值宽度重新计算，有重合的和有空隙的。（这一步或许应该在匹配前做）
    index_header_map = header_match_tools.fittingHeaderWidth(blockbox)

    # identity amend  中国不存在这种情况
    indexs = sorted(index_header_map.keys())
    firstHeader = index_header_map[indexs[0]]
    if firstHeader.identity in ['value', 'index']:
        for i in indexs[1:]:
            if index_header_map[i].identity == 'index':
                firstHeader.identity = 'useless'
                break

    if valueColumnNums >= 1:
        return index_header_map
    else:
        return False

def matchTable(pageMap, valid_page_box, patterns):
    table_box = []

    #按页寻找表
    for i, page in enumerate(valid_page_box):
        lastPage = pageMap.get(page.pageNum-1, None)

        lineBox = page.linebox
        find_position = 0
        while 1:
            foundTable = False
            for find_range_size in [5, 4, 3, 2, 1]:
                find_range = lineBox[find_position: find_position + find_range_size]

                # if page.pageNum == 11 and find_position == 2 and find_range_size == 2:
                #     pass

                # 表寻找算法入口
                find_result = check_header_match(find_range, patterns['ps'], find_position)

                if find_result:
                    table = Table(lastPage, page, find_result, find_position, find_range, lineBox[find_position].blockbox[0].linetableid)

                    for line in lineBox[find_position+find_range_size:]:
                        if table.add(line) == 'reject':
                            break
                    foundTable = True
                    table_box.append(table)
                    find_position = find_position + len(table.headerLineNums) + len(table.body)
                    break
            if not foundTable:
                find_position = find_position + 1
            if not find_position < len(lineBox):
                break

    return table_box