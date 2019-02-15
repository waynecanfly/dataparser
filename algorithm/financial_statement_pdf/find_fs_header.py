# -*- coding: UTF-8 -*-
import re

from algorithm.common import tools, configManage
from algorithm.common_tools_pdf import column_divide_tools, header_match_tools
from algorithm.financial_statement_pdf.containers.header import HeaderUnit, Header


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

def checkIdentity(index_header_map):
    # 根据特殊值进行检验
    indexs = sorted(index_header_map.keys())
    for i,index in  enumerate(indexs):
        header = index_header_map[index]
        if re.sub('\s', '', header.text) == '项目' and i != 0:
            return False

    # 根据identity进行检验
    identity_box = []
    for index in sorted(index_header_map.keys()):
        identity_box.append(index_header_map[index].identity)
    identity_str = tools.linkStr(identity_box, ',')

    illegal = ['^(subject,subject)']
    result  = re.findall(tools.linkStr(illegal, '|'), identity_str)

    if not result:
        return True
    else:
        return False



def header_match(p_reportid,lines, patterns, position):
    # 若起始行为无用行，则直接返回False
    if not lines[0].is_useful:
        return False
    # 这个函数以后需要重构
    haveLine = True if lines[0].blockbox[0].linetableid is not None else False

    # blocks
    blockbox = []
    pageNums = set()
    for l in lines:
        if not l.is_useful:
            continue
        for b in l.blockbox:
            pageNums.add(b.pageNum)
            blockbox.append(b)

    # # 如果是线表，且跨页。需要重新计算列号
    if haveLine and len(pageNums) == 2:
        first_page_block = []
        firstPage = min(pageNums)
        secondPage = max(pageNums)
        firstpage_indexmap = {}
        secondpage_indexmap = {}
        for b in blockbox:
            try:
                indexsStr = tools.linkStr(sorted(b.lineColumnIndex), '_')
            except:
                # 有线，跨页，第二页存在不在线表里的行
                return False
            if b.pageNum == firstPage:
                first_page_block.append(b)
                if indexsStr in firstpage_indexmap:
                    firstpage_indexmap[indexsStr][0] = min([b.x0, firstpage_indexmap[indexsStr][0]])
                    firstpage_indexmap[indexsStr][1] = max([b.x1, firstpage_indexmap[indexsStr][1]])
                else:
                    firstpage_indexmap[indexsStr] = [b.x0, b.x1]
            if b.pageNum == secondPage:
                if indexsStr in secondpage_indexmap:
                    secondpage_indexmap[indexsStr][0] = min([b.x0, secondpage_indexmap[indexsStr][0]])
                    secondpage_indexmap[indexsStr][1] = max([b.x1, secondpage_indexmap[indexsStr][1]])
                else:
                    secondpage_indexmap[indexsStr] = [b.x0, b.x1]
        fitting_map = {}
        for f_i in firstpage_indexmap.keys():
            f_range = firstpage_indexmap[f_i]
            for s_i in secondpage_indexmap.keys():
                s_range = secondpage_indexmap[s_i]
                overlap = tools.overlapRate(f_range, s_range)
                if overlap > 0.8:
                    if f_i not in fitting_map:
                        fitting_map[f_i] = [s_i]
                    else:
                        fitting_map[f_i].append(s_i)
        for b in first_page_block:
            indexsStr = tools.linkStr(sorted(b.lineColumnIndex), '_')
            if indexsStr in fitting_map:
                fitting_value =[int(x) for x in sorted(list(set(tools.linkStr(fitting_map[indexsStr], '_').split('_'))))]
                b.lineColumnIndex = fitting_value
                b.columnIndexs = b.lineColumnIndex
                b.columnIndex = b.lineColumnIndex[0]
    elif haveLine and len(pageNums) > 2:
        return False

    column_block_map = {}
    # gen column index and converge
    if haveLine:
        for b in blockbox:
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

    for box in column_block_map.values():
        box.sort(key=lambda x: (x.total_lineindex, x.lineIndex))

    indexs = sorted(column_block_map.keys())
    valueColumnNums = 0
    matchPatterns = []
    for i, index in enumerate(indexs):
        columnText = ''
        for b in column_block_map[index]:
            columnText = columnText + b.text
        columnTextMatch = header_match_tools.getMatchText(columnText)
        isMatch = False
        for p in patterns:
            # if blockbox[0].pageNum==49 and len(lines) == 1 and position==3:
            #     print p['text'] + ' ' + columnTextMatch
            if p['text'] == columnTextMatch:
                matchPatterns.append(p['text'])
                isMatch = True
                for block in column_block_map[index]:
                    block.identity = p['identity']
                if p['identity'] == 'value':
                    valueColumnNums = valueColumnNums + 1
                break
        if not isMatch:
            # 输出[new]
            try:
                if lines[0].linetableid is not None and len(column_block_map) >= 3 and index != 0:
                    for l in lines:
                        for b in l.blockbox:
                            if b.type == 'digit':
                                return False

                    pattern_text_box = []
                    for p in patterns:
                        pattern_text_box.append(p['text'])
                    for n in indexs[i:]:
                        blocks = column_block_map[indexs[n]]
                        column_text = ''
                        for b in blocks:
                            column_text = column_text + b.text

                        pure_text = header_match_tools.getMatchText(column_text)
                        if pure_text not in pattern_text_box:
                            if pure_text not in configManage.new_header:
                                configManage.new_header[pure_text] = [p_reportid, lines[0].pageNum, len(lines), column_text, pure_text, 1]
                            else:
                                configManage.new_header[pure_text][-1] += 1
            except:
                pass


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
            if len(blocks) > 1:
                for b in blocks:
                    multiLineBlock.add(b)

        for index in sortByMultiLine(column_block_map):
            blocks = column_block_map[index]

            # 过滤掉只有一行并且该行有和其它行组成一个整体的表头列
            if len(blocks) == 1 and blocks[0] in multiLineBlock:
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

    # identity amend  中国也存在这种情况
    indexs = sorted(index_header_map.keys())
    firstHeader = index_header_map[indexs[0]]
    if firstHeader.identity in ['value', 'index']:
        for i in indexs[1:]:
            if index_header_map[i].identity == 'index':
                firstHeader.identity = 'useless'
                break

    # 通过identity检查是否合理
    result = checkIdentity(index_header_map)

    if not result:
        return False


    if valueColumnNums >= 1:
        return index_header_map
    else:
        return False


def gen_header(find_range, find_result, header_range):
    pageNums = set()
    for l in find_range:
        pageNums.add(l.pageNum)
    linetableid = find_range[0].linetableid
    return Header(find_range, pageNums, linetableid, find_result, header_range)


def find_fs_header(p_reportid,find_area, patterns):
    # area_len = len(find_area)
    # 限定查找范围，表和表头之间不应超过十行
    area_len = min(len(find_area), 10)
    for find_position in range(0, area_len):
        for find_range_size in [5, 4, 3, 2, 1]:
            # 若剩余查找区域小于该此查找范围，则不进行查找
            if find_position + find_range_size > area_len:
                continue

            # 确定该次表头匹配的范围
            begin = find_position
            end = find_position + find_range_size
            find_range = find_area[begin: end]


            # 表头匹配算法
            find_result = header_match(p_reportid,find_range, patterns, find_position)

            # 找到表头后立刻返回
            if find_result:
                # 封装成header对象，其实这个应该在前面的步骤就封装好才合适的，暂时先这样，不然改动太大
                header = gen_header(find_range, find_result, [begin, end])
                return header
            else: # 根据某些特征，判断是否没有继续查找下去的必要（则确定该标题下没有我们要的表）[暂时]
                pass

    return 'NOT FOUND'