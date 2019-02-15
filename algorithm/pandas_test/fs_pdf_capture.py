# -*- coding:utf-8 -*-

# from containers.headerUnit import HeaderUnit
import pandas as pd

from algorithm.common import dbtools, tools
from algorithm.common.dbtools import query_to_df_dps
from algorithm.common_tools_pdf import header_match_tools, column_divide_tools
from algorithm.common_tools_pdf.title_match_tools import getMatchTitleText
from algorithm.pandas_test.fs_pdf_exceptions import StatementNotAllFound
from containers.table import Table
from main import pattern


def check_header_match(lines, ps):
    # 组合成一个整体的df，便于处理


    # 结构化成用户匹配的表头


    # 根据pattern进行匹配
    haveLine = True if lines[0].blockbox[0].linetableid is not None else False

    # blocks
    # blockbox = []
    # for l in lines:
    #     for b in l.blockbox:
    #         blockbox.append(b)
    #
    # column_block_map = {}
    # # gen column index and converge
    # if haveLine:
    #     for l in lines:
    #         for b in l.blockbox:
    #             for index in  b.lineColumnIndex:
    #                 if index in column_block_map:
    #                     column_block_map[index].append(b)
    #                 else:
    #                     column_block_map[index] = [b]
    #
    #
    # else:
    #     referLine = column_divide_tools.culateColumnIndex(blockbox)
    #     if len(referLine) < 2:
    #         return False
    #     # column converge
    #     for b in blockbox:
    #         for index in b.columnIndexs:
    #             if (index+1)*1000 in column_block_map:
    #                 column_block_map[(index+1)*1000].append(b)
    #             else:
    #                 column_block_map[(index+1)*1000] = [b]
    #
    #
    # indexs = sorted(column_block_map.keys())
    # valueColumnNums = 0
    # matchPatterns = []
    # for i, index in enumerate(indexs):
    #     columnText = ''
    #     for b in column_block_map[index]:
    #         columnText = columnText + b.text
    #     columnTextMatch = header_match_tools.getMatchText(columnText)
    #     isMatch = False
    #     for pattern in ps:
    #         # if blockbox[0].pageNum==4 and len(lines) == 2 and position==2:
    #         #     print pattern.text + ' ' + columnTextMatch
    #         if pattern.text == columnTextMatch:
    #             matchPatterns.append(pattern.text)
    #             isMatch = True
    #             for block in column_block_map[index]:
    #                 block.identity = pattern.identity
    #             if pattern.identity == 'value':
    #                 valueColumnNums = valueColumnNums + 1
    #             break
    #     if not isMatch:
    #         return False
    #
    # # 来到这里证明已经是找到了表的科目
    # # 更新匹配次数
    # for matchP in matchPatterns:
    #     dbtools.query_pdfparse("update opd_structure_pattern set num_of_use=num_of_use + 1 where text='" + matchP + "'")
    #
    #
    #
    # # 若是有线的表，直接封装返回
    # if haveLine:
    #     index_header_map = {}
    #     for index in sorted(column_block_map.keys()):
    #         blocks = column_block_map[index]
    #
    #         curHeader = None
    #         for b in blocks:
    #             if curHeader is None:
    #                 curHeader = HeaderUnit(index, b)
    #             else:
    #                 curHeader.lineAddBlock(b)
    #         index_header_map[index] = curHeader
    #     if len(index_header_map) < 2:
    #         return False
    #     return index_header_map
    #
    #
    #
    # # 表头拟合 : 1.值列非最后一行独立组成一列时拟合 2. 值宽度重新计算，有重合的和有空隙的。（这一步或许应该在匹配前做）
    # index_header_map = header_match_tools.fittingHeaderWidth(blockbox)
    #
    # # identity amend  中国不存在这种情况
    # indexs = sorted(index_header_map.keys())
    # firstHeader = index_header_map[indexs[0]]
    # if firstHeader.identity in ['value', 'index']:
    #     for i in indexs[1:]:
    #         if index_header_map[i].identity == 'index':
    #             firstHeader.identity = 'useless'
    #             break
    #
    # if valueColumnNums >= 1:
    #     return index_header_map
    # else:
    #     return False

def get_title_lib():
    sql = 'select matchcode, tabletype from title_match_lib'
    df = dbtools.query_to_df_dps(sql)
    return df.groupby('tabletype')
    return pattern


def find_title(line_box):
    # 获取title库
    title_group = get_title_lib()

    find_result = pd.DataFrame()

    # 中国只找一行，所以可以用for循环
    for index, line in enumerate(line_box):
        for table_type, group in title_group:
            line_text = tools.linkStr(line.text, '')
            pure_text = getMatchTitleText(line_text)
            if pure_text in list(group.matchcode):
                newone = {'position':str(index), 'text':line_text, 'type':table_type}
                find_result= find_result.append(newone, ignore_index=True)

    # 检查是否找全所有表，如果没找全，立刻抛异常
    table_types = list(find_result.get('type', []))
    j1 = 'BS' in table_types
    j2 = 'IS' in table_types
    j3 = 'CF' in table_types
    if j1 and j2 and j3:
        return find_result
    else:
        raise StatementNotAllFound(str(find_result))


def match_header(line_box):
    pass
    # get pattern
    # patterns = query_to_df_dps("select distinct text, identity from opd_structure_pattern")

def delimit_body(line_box):
    pass

def capture(line_box):
    # 第一步： 先全局找表头，找够合适的表头再做下一步计算
    title_anchor = find_title(line_box)

    # 第二步： 以表头为锚点，往下识别表头
    match_header(line_box, title_anchor)

    # 第三步： 表头识别成功后寻找正文，关键在于确定表的结束位置
    delimit_body(line_box)



    table_box = []

    #找表
    # find_position = 0
    # while 1:
    #     for find_range_size in [5, 4, 3, 2, 1]:
    #         find_range = line_box[find_position: find_position + find_range_size]
    #         find_result = check_header_match(find_range, patterns)
    #
    #             if find_result:
    #                 table = Table(lastPage, page, find_result, find_position, find_range, lineBox[find_position].blockbox[0].linetableid)
    #
    #                 for line in lineBox[find_position+find_range_size: ]:
    #                     if table.add(line) == 'reject':
    #                         break
    #                 foundTable = True
    #                 table_box.append(table)
    #                 find_position = find_position + len(table.headerLineNums) + len(table.body)
    #                 break
    #         if not foundTable:
    #             find_position = find_position + 1
    #         if not find_position < len(lineBox):
    #             break
    #
    # return table_box