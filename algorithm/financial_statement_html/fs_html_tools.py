# -*- coding: UTF-8 -*-
import csv
import os
import re

import pandas as pd

from algorithm.common import dbtools, configManage, tools
from algorithm.financial_statement_html import title_match_tools_usa
from algorithm.financial_statement_html.container import common_lib
from algorithm.financial_statement_html.container.statement import Statement


def get_source_data(p_country, p_company, p_reportid):
    datapath = configManage.config['html_location'][
                   'opd_source_html'] + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"
    datapath = datapath.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)
    # debug flag
    # datapath = 'C:\\temp\\usa_html\\' + p_reportid + '.csv'
    source_df = pd.read_csv(datapath, header=None, names=get_line_keys())
    source_df['idx'] = source_df.index
    source_df.fillna('', inplace=True)
    return source_df


def get_line_keys():
    keys = ['line_identifier',
            'is_table',
            'tb_identifier',
            'tr_identifier',
            'td_identifier',
            'td_content',
            'td_content_separated',
            'colspan',
            'rowspan'
            ]
    return keys


def get_table_box(source_df):
    table_box = []
    table_lines = source_df[source_df['is_table'] == 1]
    for name, group in table_lines.groupby('tb_identifier'):
        table_box.append(group)
    if not table_box:
        raise Exception('TABLE_NOT_FOUND')
    # 去除少于10行的表格
    # for i in range(len(table_box))[::-1]:
    #     if int(table_box[i]['tr_identifier'].max()) < 10:
    #         del table_box[i]

    return table_box


def get_df_lines(dataframe):
    """
    按行汇聚
    :return:
    """
    lines = []
    for name, group in dataframe.groupby('tr_identifier'):
        lines.append(group)
    return lines


def split_table(table_lines, para, CHECK_LINES_SETTING=3):
    """
    检查同一个html表格里面是否有多个报表，拆分报表
    :param table_lines: 表格每一行dataframe
    :param CHECK_LINES_SETTING: 检查空行数设置，超过3行就判断为html表格里面有其他报表
    :return: list table_lines列表  如果符合拆分规则，返回多个表格的每一行数据列表；否则返回原来的一个表格每一行数据列表
    """
    # 美国数据不需要拆表
    if para.countryid == 'USA':
        return [table_lines]
    # rule 1 step 1: 判断是否有连续三行空行
    blankline_counter = 0
    break_point_indexes = []
    for index, value in enumerate(table_lines):
        # 一行数据全部为空
        if ''.join(value['td_content'].tolist()).strip() == '':
            blankline_counter += 1
        else:
            if blankline_counter >= CHECK_LINES_SETTING:
                # 发现了断点
                break_point_indexes.append(index)
            blankline_counter = 0

    if not break_point_indexes:
        return [table_lines]

    # rule 1 step 2: 按照断点拆分表，保存到sub_table_box属性中。以便后续封装成FinancialStatementItem对象
    subtable_box = []
    begin = 0
    for b in break_point_indexes:
        subtable_box.append(table_lines[begin: b])
        begin = b
    subtable_box.append(table_lines[begin:])
    return subtable_box
    # rule2 step 1: 根据标题拆分表格(to do)


def gen_whole_table_by_lines(table_lines):
    """
    根据每一行内容生成整个报表内容
    :param table_lines:
    :return:
    """
    table_df = pd.DataFrame()
    for i in table_lines:
        table_df = table_df.append(i)
    return table_df


def find_title_in(table_df, title_lib, para, SEARCH_BLOCK_LINES=5):
    """
    在表格内找标题
    :param table_df: 表格dataframe
    :param title_lib: 标题库
    :param SEARCH_BLOCK_LINES: 查找的行数
    :return: list [找到标题的行号index, 表类型，标题文本]
    """
    # 待优化：目前发现有些表格的标题在表格正文中，报表识别不出来
    # 需要识别整个表格内容，再拆表。
    cur_lineIndex = 1
    for index, value in table_df.iterrows():
        # 按行查找
        if cur_lineIndex != value['tr_identifier']:
            # x = table['tr_identifier']== cur_lineIndex
            aim_dfs = table_df.loc[table_df['tr_identifier'] == cur_lineIndex]
            line_text = ' '.join(aim_dfs['td_content'].tolist())
            # print line_text
            check_text = title_match_tools_usa.getMatchTitleText(line_text)
            if check_text in title_lib:
                return [aim_dfs['idx'].tolist(), title_lib[check_text], line_text]
            cur_lineIndex = value['tr_identifier']
        # 按单元格（一行中的一列）查找
        check_text = title_match_tools_usa.getMatchTitleText(value['td_content'])
        if check_text in title_lib:
            return [[value['idx']], title_lib[check_text], value['td_content']]
        # 增加 value['td_content_separated'].split('#|#') 每一个元素的查找标题
        # 因为value['td_content']里面会有多个标签的内容导致识别不了
        # value['td_content_separated'].split('#|#') 则是td每一行的内容
        if '#|#' in value['td_content_separated']:
            check_text_separated = value['td_content_separated'].split('#|#')
            for cts in check_text_separated:
                ct = title_match_tools_usa.getMatchTitleText(cts)
                if ct in title_lib:
                    return [[value['idx']], title_lib[ct], ct]

        if cur_lineIndex > SEARCH_BLOCK_LINES:
            break
    return []


def find_title_out(table_df, source_df, title_lib, para, SEARCH_BLOCK_CHARS=200):
    """
    在表格外找标题
    :param table_df: 表格dataframe
    :param source_df: 整个文件dataframe
    :param title_lib: 标题库
    :param SEARCH_BLOCK_CHARS: 查找的字符数
    :return: list [找到标题的行号index, 表类型，标题文本]
    """
    find_range = source_df.loc[source_df['idx'] < table_df['idx'].min()]

    # 退出条件标志
    found_char_amount = 0
    find_box = []
    for index, value in find_range[::-1].iterrows():
        # 找到上一个表格就结束
        if value['is_table'] == 1:
            break
        if value['td_content'].strip() == '':
            continue
        find_box.append(value)
        check_text = re.sub(r'\s', '', value['td_content'])
        found_char_amount = found_char_amount + len(check_text)
        if found_char_amount > SEARCH_BLOCK_CHARS:
            break

    find_box.reverse()
    # position_box = range(0, len(find_box) + 1)
    reversed_position = range(len(find_box), -1, -1)
    for i in reversed_position:
        for k in reversed_position:
            if k == i:
                break
            check_range = find_box[i:k]
            # 识别标题
            line_index = []
            line_text = ''
            for cr in check_range:
                line_index = line_index + [cr['idx']]
                line_text = line_text + cr['td_content']
            check_text = title_match_tools_usa.getMatchTitleText(line_text)
            if check_text in title_lib:
                return [line_index, title_lib[check_text], line_text]
    return []


def find_title(table_df, source_df, title_lib, para):
    """
    # 根据标题库识别标题
    :param table: 表格dataframe
    :param source_df:  整个文件dataframe
    :param title_lib:  标题库
    :return: list [找到标题的行号index, 表类型，标题文本]
    """
    # 1. 先在表内找
    # 美国的数据暂时不在表内找标题(跑完一次数据之后，重跑就不能再注释了)
    # if para.countryid != 'USA':
    result = find_title_in(table_df, title_lib, para)
    # 2. 再在表外找
    if not result:
        result = find_title_out(table_df, source_df, title_lib, para)
    return result


def get_table_outer_area(title_index, table_df, source_df):
    first_line_idx = title_index[0]
    last_line_idx = table_df.iloc[-1]['idx'] + 1
    target_df = source_df.iloc[first_line_idx: last_line_idx]
    return target_df


def get_statement_box(source_df, table_box, para):
    # 获取标题库
    title_lib = get_title_lib()
    # 过滤美国无用的标题
    if para.countryid == 'USA':
        title_filtered_usa = ['financialstatements', 'comprehensiveincome', 'quarterlyresults', 'financialresults']
        for tt in title_filtered_usa:
            if tt in title_lib:
                del title_lib[tt]
    statement_box = []
    table_box_separated = []
    # 拆表
    for table in table_box:
        # 按行汇聚
        table_lines = get_df_lines(table)
        # 拆分
        sub_table_box = split_table(table_lines, para)
        table_box_separated = table_box_separated + sub_table_box

    for table_lines in table_box_separated:
        # 生成整个table的dataframe
        table_df = gen_whole_table_by_lines(table_lines)
        # 根据标题库识别标题
        find_title_result = find_title(table_df, source_df, title_lib, para)

        # 封装到statuemnt对象
        if find_title_result:
            title_index = find_title_result[0]
            table_type = find_title_result[1]
            title_text = find_title_result[2]
            # table_df增加表格外的标题到正文部分的内容再传入
            table_df = get_table_outer_area(title_index, table_df, source_df)
            statement_box.append(Statement(table_df, title_index, table_type, title_text))

    statement_box = pre_check_statement(statement_box)
    return statement_box


def get_consolidated_condensed_form(text):
    """
    # 根据标题判断是否合并报表，简明报表
    # 'isConsolidated': -1 => 默认; 1 => 合并
    # 'isCondensed': -1 => 默认; 1 => 简明
    """
    result = {'isConsolidated': -1, 'isCondensed': -1}
    pure_text = re.sub(r"\s", '', text).lower()

    consolidated_keywords = ['consolidated', 'consolidate']
    condensed_keywords = ['condensed', 'condense']
    for csk in consolidated_keywords:
        if csk in pure_text:
            result['isConsolidated'] = 1
            break
    for cdk in condensed_keywords:
        if cdk in pure_text:
            result['isCondensed'] = 1
            break
    return result


def filter_useless_table(aim_statement_box):
    """
    # 1.去除在位置上距离三大报表集合位置很远的疑似无用的表格
    # 2.去掉condensed简明报表
    """
    group_distance_thr = 7
    tableGroup = []
    for table in aim_statement_box:
        if len(tableGroup) == 0:
            tableGroup.append([table])
        elif abs(table.tb_id - tableGroup[-1][-1].tb_id) < group_distance_thr:
            tableGroup[-1].append(table)
        else:
            tableGroup.append([table])

    # 如果某一个table组中包含了所有目标报表的话，丢弃其它组的报表
    aimset = {'BS', 'IS', 'CF'}
    probable_group_1st = probable_group_2nd = probable_group_3rd = probable_group_4th = None
    for i, group in enumerate(tableGroup):
        tableTypeSet = set()
        group_consolidated_form = []
        group_condensed_form = []
        is_consolidated_group = False
        is_condensed_group = False

        for t in group:
            t_form = get_consolidated_condensed_form(t.title_text)
            group_consolidated_form.append(t_form['isConsolidated'])
            group_condensed_form.append(t_form['isCondensed'])
            tableTypeSet.add(t.table_type)
        if len(set(group_consolidated_form)) == 1 and 1 in set(group_consolidated_form):
            is_consolidated_group = True
        if len(set(group_condensed_form)) == 1 and 1 in set(group_condensed_form):
            is_condensed_group = True

        # 优先级为1的组: 找全了三大报表，并且组合不是简明报表，而是综合报表
        if aimset.issubset(tableTypeSet) and not is_condensed_group and is_consolidated_group:
            probable_group_1st = group
        # 优先级为2的组：找全了三大报表，并且组合是综合报表
        if aimset.issubset(tableTypeSet) and is_consolidated_group:
            probable_group_2nd = group
        # 优先级为3的组：找全了三大报表，第一次的符合条件的组：不管是综合报表组合还是简明报表组合
        if aimset.issubset(tableTypeSet) and not probable_group_3rd:
            probable_group_3rd = group
        # 优先级为4的组：找全了三大报表，最后一次的符合条件的组
        if aimset.issubset(tableTypeSet):
            probable_group_4th = group

    if probable_group_1st:
        return probable_group_1st
    if probable_group_2nd:
        return probable_group_2nd
    if probable_group_3rd:
        return probable_group_3rd
    if probable_group_4th:
        return probable_group_4th

    return aim_statement_box


def pre_check_statement(statement_box):
    # 筛选出有正常的列的报表
    aim_statement_box = []
    for st in statement_box:
        # 过滤掉疑似解析出来无用的报表
        if not st.header_columns or not st.valid_row_ids:
            continue
        if int(max(st.header_columns.keys())) < int(max(st.valid_row_ids)):
            # raise Exception('HEADER_MISMATCHING')
            continue
        if st.header_columns and len(st.valid_row_ids) > 1 and st.subject_df:
            st.is_valid = 1
            aim_statement_box.append(st)
        else:
            st.is_valid = 0

    # 判断是否找全表格
    if aim_statement_box:
        validate_lib = ['BS', 'CF', 'IS']
        validate_box = []
        for ast in aim_statement_box:
            if ast.table_type in validate_lib:
                validate_box.append(ast.table_type)
            # 检查表头列是否不匹配
            # if int(max(ast.header_columns.keys())) < int(max(ast.valid_row_ids)):
            #     raise Exception('HEADER_MISMATCHING')
            #     pass

        if 'BS' not in validate_box or 'CF' not in validate_box or 'IS' not in validate_box:
            raise Exception('STATEMENT_NOT_ALL_FOUND')
    else:
        raise Exception('STATEMENT_NOT_FOUND')

    # 过滤掉疑似无用报表
    aim_statement_box = filter_useless_table(aim_statement_box)

    return aim_statement_box


def get_title_lib():
    title_lib = {}
    sql = """select matchcode, tabletype from title_match_lib where language_type='EN'"""
    result = dbtools.query_pdfparse(sql)
    for unit in result:
        if re.match(u"[\u4e00-\u9fa5]", unicode(unit[0])):
            continue
        key = title_match_tools_usa.getMatchTitleText(unit[0].encode('utf-8'))
        title_lib[key] = unit[1]
    return title_lib


def merge_it(subject_box, subject_to_merge):
    for k, v in subject_box.items():
        for kk, vv in subject_to_merge.items():
            if kk == k:
                if v.strip() != '':
                    subject_box[k] = v
                    continue
                elif vv.strip() != '':
                    subject_box[k] = vv
                    continue
    return subject_box


def get_subject_merged_dict(statement, subject_value_merged):
    """
    返回合并后的科目和行号
    """
    subject_box = {}
    for i, v in statement.subject_df[0].iterrows():
        subject_box[int(v['tr_identifier'])] = v['td_content']
    for sd in statement.subject_df[1:]:
        subject_to_merge = {}
        for i, v in sd.iterrows():
            subject_to_merge[int(v['tr_identifier'])] = v['td_content']
        subject_box = merge_it(subject_box, subject_to_merge)

    subject_merged_dict = {}
    check_idx = None
    check_status = 0
    for tr_id, val in subject_box.items():
        if val.strip() == '':
            subject_merged_dict[tr_id] = {tr_id: val}
            continue
        # 去除多余的表格内容
        if re.sub(r"\s", '', val) in common_lib.useless_table_tails:
            continue

        if val[0].isupper() and ''.join(
                subject_value_merged[subject_value_merged['tr_identifier'] == tr_id][
                    'td_content'].tolist()).strip() == '':
            check_idx = tr_id
            subject_merged_dict[tr_id] = {tr_id: val}
            check_status = 1
        # elif (val[0].islower() or val[0].isdigit()) and check_idx and check_status:
        elif val[0].islower() and check_idx and check_status:
            subject_merged_dict[check_idx].update({tr_id: val})
        else:
            subject_merged_dict[tr_id] = {tr_id: val}
            check_status = 0
    return subject_merged_dict


def fill_value(line_container, this_td_id, subject_value):
    for line in line_container[::-1]:
        if line[11].isupper() and line[12].strip() == '' and line[10] == this_td_id:
            line[12] = subject_value
            return True
    return False


def get_all_table_data(statement_box, para):
    """
    # 获取所有表格数据，生成待输出数据
    字段说明：
    国家id
    公司id
    reportid
    公司名
    报表类型
    年份
    季度
    全局行号(一个table当做一行)
    tableid
    table行id
    table列id
    table科目
    table科目值
    货币符号
    货币单位
    开始时间
    结束时间
    是否合并报表
    """
    all_table_data = []
    one_table_data = []
    for statement in statement_box:
        subject_value_merged = pd.DataFrame()
        for subject in statement.subject_value_df:
            subject_value_merged = subject_value_merged.append(subject)
        subject_value_merged = subject_value_merged.sort_values(by=['idx', 'td_identifier_arranged'])
        # 科目合并
        subject_merged_dict = get_subject_merged_dict(statement, subject_value_merged)

        line_container = []
        for sub_index, sub_value in subject_value_merged.iterrows():
            this_tr_id = sub_value['tr_identifier']
            this_td_id = sub_value['td_identifier_arranged']
            this_line_id = sub_value['line_identifier']
            this_tb_id = sub_value['tb_identifier']
            this_header = statement.header_columns[this_td_id]
            if not this_header.is_valid:
                continue
            if this_tr_id not in subject_merged_dict:
                continue
            subject = []
            for s in sorted(subject_merged_dict[int(this_tr_id)].items(), key=lambda d: d[0]):
                subject.append(s[1])
            subject = ' '.join(' '.join(subject).split())

            # 科目值
            if len(subject_merged_dict[int(this_tr_id)]) > 1:
                # 科目值取合并科目字典的最大行号和当前列号的值
                subject_value_tr_id = max(subject_merged_dict[int(this_tr_id)].keys())
                try:
                    subject_value = subject_value_merged[(subject_value_merged['tr_identifier'] == subject_value_tr_id) & (subject_value_merged['td_identifier_arranged'] == this_td_id)]['td_content'].values[0]
                except:
                    subject_value = ''
            else:
                subject_value = sub_value['td_content']

            # 处理BS表科目值没有对应科目的情况：往上找最近的全大写且没数值的科目进行填充
            if statement.table_type == 'BS' and subject.strip() == '' and subject_value.strip() != '':
                if fill_value(line_container, this_td_id, subject_value):
                    continue
                # else:
                #     raise Exception('VALUE_NO_MATCHING_SUBJECT')

            # 过滤空行
            if subject.strip() == '' and subject_value.strip() == '':
                continue

            # 解决科目跨列，科目值错误问题
            if re.sub(r"\s", '', subject) == subject_value:
                subject_value = ''
            currency = this_header.currency
            measureunit = this_header.measureunit
            time_begin = this_header.time_begin
            time_end = this_header.time_end
            is_con = this_header.isConsolidated
            line_container.append([
                para.countryid,
                para.companyid,
                para.reportid,
                para.company_name,
                statement.table_type,
                statement.fiscal_year,
                statement.globalSeasonType,
                this_line_id,
                this_tb_id,
                this_tr_id,
                this_td_id,
                subject,
                subject_value,
                currency,
                measureunit,
                time_begin,
                time_end,
                is_con
            ])
        # 每一个报表的数据添加到output_value_box属性
        statement.output_value_box = line_container
        one_table_data.append(line_container)

    for sub in one_table_data:
        all_table_data += sub
    return all_table_data


def write_file(csv_name, data):
    with open(csv_name, "wb") as wf:
        table_writer = csv.writer(wf)
        table_writer.writerows(data)


def output_data(all_table_data, para, istest):
    csvsavepath = configManage.config['html_location']['html_push'] + "/p_country={p_country}/p_company={p_company}/"
    csvsavepath = csvsavepath.format(p_country=para.countryid, p_company=para.companyid)
    # debug flag
    # csvsavepath = './new_debug/'
    if istest:
        csvsavepath = './test_result/'
    tools.makeDirs(csvsavepath)

    if len(all_table_data):
        op_file_name = csvsavepath + para.reportid + ".csv"
        write_file(op_file_name, all_table_data)
        tools.update_html_status(para.countryid, para.companyid, para.reportid, 100, 'FILE_GENERATED')
    else:
        tools.update_html_status(para.countryid, para.companyid, para.reportid, -30, '', 'STATEMENT_DATA_EMPTY')
