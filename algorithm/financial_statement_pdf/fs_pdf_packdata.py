# -*- coding:utf-8 -*-
import re

from algorithm.common import tools, configManage
from algorithm.common_tools_pdf import subject_match_tools


def getidstr(box):
    box.sort()
    result = ''
    for b in box:
        result = result + str(id(b))
    return result

def weak_header_fitting(table, out_columnindex):
    if len(out_columnindex) % 2 != 0:
        return True

    thc = table.header.header_columns

    for i, index in enumerate(out_columnindex):
        header = thc[index[0]]
        refer_header = thc[out_columnindex[i-1][0]] if (i+1) % 2 == 0 else thc[out_columnindex[i+1][0]]

        header.time_begin = header.time_begin if header.time_begin!='' else refer_header.time_begin
        header.time_end = header.time_end if header.time_end!='' else refer_header.time_end
        header.currency = header.currency if header.currency is not None else refer_header.currency
        header.measureunit = header.measureunit if header.currency is not None else refer_header.measureunit

def gen_out_lineindex(table):
    out_lineindex = []
    for lStr in table.subject_map_merged:
        l = lStr.split('_')
        l = [int(x) for x in l]
        out_lineindex.append(l)

    # 暂时去掉值无科目校验，遇到这种情况，值会直接被过滤掉

    # for index in table.body_line_map.keys():
    #     is_in = False
    #     for ol in out_lineindex:
    #         if index in ol or (len(ol)>1 and index > ol[0] and index < ol[1]):
    #             is_in = True
    #             break
    #     if not is_in:
    #         if index > table.body_max_lineindex:
    #             break
    #         else:
    #             raise Exception('VALUE_NO_SUBJECT')
            # 中国的绝大多数不存在值无科目，因此可以在此报错
    out_lineindex.sort(key=lambda x: x[0])
    return out_lineindex

def gen_out_columnindex(table):
    header_block_column_map = {}
    for headerSingle in table.header.header_columns.values():
        # 非值列或调整前值列不进行输出
        if headerSingle.identity != 'value' or headerSingle.isadjust == -1:
            continue
        else:
            headerblockidstr = getidstr(headerSingle.blockbox)
            if headerblockidstr not in header_block_column_map:
                header_block_column_map[headerblockidstr] = [headerSingle.columnIndex]
            else:
                header_block_column_map[headerblockidstr].append(headerSingle.columnIndex)

    out_columnindex = header_block_column_map.values()
    out_columnindex.sort(key=lambda x: x[0])
    return out_columnindex

def get_value(table, lindex, cindex, header):
    def get_pure(text):
        return  re.sub(
            r"""\s|\d|,|\||-|—|:|：|．|\*|\[|\]|\?|\.|\(|\)|/|#|&|'|\"|、|－|（|）|“|”|―|‖|~|，|！|¡|。|‛|‚|­|；|;|？|】|【|※|﹑|\^|〔|·|‐|‘|’|＂|＂|\+|–|／|_""",
            '', text)

    r_min = min(lindex)
    r_max = max(lindex)
    line_indexs = sorted(table.body_line_map.keys())

    value = ''

    for l in line_indexs:
        if l <= r_max and l>=r_min:
            line = table.body_line_map[l]
            for block in line:
                if block.columnIndex in cindex:
                    value = value + block.text

    value = re.sub(',| ', '', value)
    value_pure = get_pure(value)
    if value_pure != '' and value_pure in get_pure(header.text):
        value = ''

    return re.sub(r'-{3,}$','',value)

def pack(table, out_lineindex, out_columnindex, countryid, companyid, reportid, companyName):
    output_value_box = []
    for lindex in out_lineindex:
        # 获取科目
        subject = table.subject_map_merged.get(tools.linkStr(lindex, '_'), None)
        if subject == '项目':
            continue
        for cindex in out_columnindex:
            # 获取表头（表头包含所有的元信息，包括时间、货币等等）
            header = table.header.header_columns[cindex[0]]

            # 获取值
            value = get_value(table, lindex, cindex, header)

            new_value = [countryid, companyid, reportid, companyName, table.table_type, table.pageNum, header.fiscal_year,
             header.season_type, subject, value, header.currency, header.measureunit, header.time_begin,
             header.time_end, lindex[0], tools.linkStr(cindex, '|'), header.isConsolidated]

            new_value = [x if x is not None else '' for x in new_value]

            # 装进集合
            output_value_box.append(new_value)
    # x = tools.linkStr([tools.linkStr(x, ',') for x in output_value_box], '\n')
    # print x
    table.output_value_box = output_value_box

def special_process(table):
    indexs_map = {}
    newindex_value_map = {}
    for index in table.subject_map_merged.keys():
        value = table.subject_map_merged[index]
        new_index = max([int(y) for y in index.split('_')])
        indexs_map[new_index] = index
        newindex_value_map[new_index] = value

    for newindex in sorted(indexs_map.keys()):
        index = indexs_map[newindex]


    order_box = sorted([max([int(y) for y in x.split('_')]) for x in table.subject_map_merged.keys()])
def check_subject(table):
    count_map = {}
    for s in table.subject_map_merged.values():
        pure_s = subject_match_tools.getPureSbuectText(s)
        if pure_s not in count_map:
            count_map[pure_s] = [table.reportid.encode('utf-8'), s.encode('utf-8'), pure_s.encode('utf-8'), table.table_type, table.pageNum, 1]
        else:
            count_map[pure_s][-1] += 1
    for v in count_map.values():
        if v[-1] >1:
            # print "[12-16],".encode('utf-8') + tools.linkStr(v, ',')
            configManage.logger.info("[12-16]," + tools.linkStr(v, ','))

def pack_output_data(table_box, companyName):
    # 以下几个属性时临死的，等整个体系重构之后就不再往下一步推送这种东西
    reportid = table_box[0].reportid
    countryid = reportid[0:3]
    companyid = reportid[0:8]
    # companyName = fs_pdf_tools.getCompanyName(companyid)

    for table in table_box:
        # 一. 生成输出行index（有值無科目的会在这里过滤掉）
        out_lineindex = gen_out_lineindex(table)

        # 二. 生成输出列index（这里要防止多与的线导致列的重复）
        out_columnindex = gen_out_columnindex(table)

        # 三. header信息(时间)回填，某些value列无header（大多数出现再英文报表中）；
        #     或者多层复合的header中，顶层的block偏向某一列，导致另外一列信息缺失(中文英文都回出现)
        weak_header_fitting(table, out_columnindex)

        # 四. 特殊科目处理统计（临时代码）
        # special_process(table)

        # check_subject(table)

        # 五. 开始打包数据
        pack(table, out_lineindex, out_columnindex, countryid, companyid, reportid, companyName)