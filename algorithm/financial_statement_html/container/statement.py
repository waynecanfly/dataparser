# -*- coding: UTF-8 -*-
import pandas as pd
import re


def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        pass
    try:
        import unicodedata
        unicodedata.numeric(s)
        return True
    except (TypeError, ValueError):
        pass
    return False


def char_count(char):
    """
    # 统计英文字母和数字的个数
    """
    char = str(char)
    int_count = 0
    str_count = 0
    other_count = 0
    for i in char:
        if i.isdigit():
            int_count += 1
        elif i.isalpha():
            str_count += 1
        else:
            other_count += 1
    total_count = int_count + str_count + other_count
    return {'int_count': int_count, 'str_count': str_count, 'other_count': other_count, 'total_count': total_count}


def char_count_rows(row_value_list):
    """
    # 统计包含英文字母和数字的列数
    """
    total_rows = len(row_value_list)
    letter_rows = 0
    num_rows = 0
    for row in row_value_list:
        if re.match(r"[a-zA-Z]", row):
            letter_rows += 1
        if is_number(re.sub(r"[()\"\'\s,.$]|(#\|#)", '', row)) or row in ['-', '–', '—']:
            num_rows += 1
    return {'num_rows': num_rows, 'letter_rows': letter_rows, 'total_rows': total_rows}


class Statement:
    def __init__(self, table_df, title_index, table_type, title_text):
        self.table_df = table_df  # 整个表格dataframe
        self.title_index = title_index  # 找到标题的行号idx
        self.table_type = table_type
        self.title_text = title_text
        self.table_lines = self.get_df_lines()  # 整个表格的每一行dataframe
        self.rearrange_column_index()
        self.tb_front_content = []  # 表前部，可能包括标题
        self.body_df = []  # 正文
        self.body_rows = []  # 正文每一列
        self.subject_df = []  # 表格左边科目
        self.subject_value_df = []  # 表格右边科目值
        self.distinguish_tb_front_content()
        self.tb_id = self.get_tb_id()
        self.valid_rows = {}  # 有用的列
        self.valid_row_ids = []  # 有用的列id
        self.recognition_info_lib = []  # 识别信息库，收集无用的列的信息，用来匹配货币符号
        self.validate_rows()
        self.header_columns = {}  # 表头
        self.distinguish_header()
        # 以下识别货币和时间信息用
        self.currency = None
        self.measureunit = None
        self.fiscal_year = None
        self.season_type = None
        self.is_valid = -1  # 是否有用报表 -1：默认(未检查)  0：无用  1：有用
        self.isConsolidated = -1  # 是否合并报表 -1：默认(合并)  0：非合并  1：关键字识别出来的合并
        self.output_value_box = None  # 用于检测模块的输出结果

    def get_df_lines(self):
        """
        按行汇聚
        :return:
        """
        lines = []
        for name, group in self.table_df.groupby('tr_identifier'):
            lines.append(group)
        return lines

    def rearrange_column_index(self):
        """
        # 根据行宽rowspan, 列宽colspan 属性重新分布列号
        """
        table_lines_arranged = []
        data_collector = []
        rowspan_on_tr_ids = []
        this_td_id = None
        this_colspan = 0
        for line in self.table_lines:
            line_columns = line.columns.values.tolist()
            line_columns.extend(['td_identifier_arranged'])
            row_counter = 0
            for index, row in line.iterrows():
                # phase 2: 增加跨行的其余数据
                if int(row.tr_identifier) in rowspan_on_tr_ids and int(row.td_identifier) == this_td_id:
                    # 跨列情况
                    if this_colspan > 1:
                        for i in range(this_colspan):
                            row_counter += 1
                            place_holder = ''
                            that_row = row.copy()
                            that_row['td_content'] = place_holder
                            that_row['td_content_separated'] = place_holder
                            that_row['rowspan'] = 0
                            that_row_values = that_row.values.tolist()
                            that_row_values.extend([row_counter])
                            data_collector.append(that_row_values)
                    # 不跨列情况
                    else:
                        row_counter += 1
                        place_holder = ''
                        that_row = row.copy()
                        that_row['td_content'] = place_holder
                        that_row['td_content_separated'] = place_holder
                        that_row['rowspan'] = 0
                        that_row_values = that_row.values.tolist()
                        that_row_values.extend([row_counter])
                        data_collector.append(that_row_values)
                # 跨行
                if row.rowspan > 1:
                    # 跨行跨列
                    if row.colspan > 1:
                        # phase 1: 增加跨行的第一列数据
                        row_counter += 1
                        this_row_values = row.values.tolist()
                        this_row_values.extend([row_counter])
                        data_collector.append(this_row_values)
                        this_tr_id = int(row.tr_identifier)
                        this_td_id = int(row.td_identifier)
                        this_colspan = int(row.colspan)
                        rowspan_on_tr_ids = []
                        for i in range(1, int(row.rowspan)):
                            rowspan_on_tr_ids.append(this_tr_id + i)
                    # 跨行不跨列
                    else:
                        # phase 1: 增加跨行的第一列数据
                        row_counter += 1
                        this_row_values = row.values.tolist()
                        this_row_values.extend([row_counter])
                        data_collector.append(this_row_values)
                        this_tr_id = int(row.tr_identifier)
                        this_td_id = int(row.td_identifier)
                        this_colspan = int(row.colspan)
                        rowspan_on_tr_ids = []
                        for i in range(1, int(row.rowspan)):
                            rowspan_on_tr_ids.append(this_tr_id + i)
                # 不跨行
                else:
                    # 不跨行跨行
                    if row.colspan > 1:
                        for i in range(row.colspan):
                            row_counter += 1
                            row_values = row.values.tolist()
                            row_values.extend([row_counter])
                            data_collector.append(row_values)
                    # 不跨行不跨行
                    else:
                        row_counter += 1
                        row_values = row.values.tolist()
                        row_values.extend([row_counter])
                        data_collector.append(row_values)
            table_lines_arranged = pd.DataFrame(data_collector, columns=line_columns)
        self.table_df = table_lines_arranged

    def distinguish_tb_front_content(self):
        # 以第一个纯数字来区分表前部和表正文
        first_tr_id = 1
        break_flag = False
        month_regex = '(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sept|oct|nov|dec)'
        for index, value in self.table_df.iterrows():
            # 找到报表的第一个纯数字，判断是否为科目的第一行
            if pd.notnull(value.td_content):
                # 美国数据需要去除美元符号$
                first_value_finder = re.sub(r"[()\"\'\s,. $]|(#\|#)", '', value['td_content'])
                if is_number(first_value_finder) or first_value_finder == '-':
                    first_tr_id = value['tr_identifier']
                    first_td_id = value['td_identifier']
                    # 找到该值前面的列列有值的行才退出
                    found_line_df = self.table_df[self.table_df['tr_identifier'] == first_tr_id]
                    if ''.join(found_line_df[found_line_df['td_identifier'] < first_td_id]['td_content'].tolist()).strip() != '':
                        break_flag = True
                    # 同时后面的字符串（去掉月份等干扰信息后）不全为数字（该行可能是年份的行）
                    check_value = ''.join(found_line_df[found_line_df['td_identifier'] > 1]['td_content'].tolist())
                    check_value = re.sub(r"notes?|[()\s A,]|{month_regex}".format(month_regex=month_regex), '', check_value, flags=re.I).strip()
                    if is_number(check_value):
                        break_flag = False
                    if break_flag:
                        break
        # 解决表格正文前面的科目识别成表头的问题
        first_tr_id = self.refine_tb_front_content(first_tr_id)

        # 区分表格前部和正文
        self.tb_front_content = self.table_df[self.table_df['tr_identifier'] < first_tr_id]
        self.body_df = self.table_df[self.table_df['tr_identifier'] >= first_tr_id]

    def get_tb_id(self):
        return int(self.body_df['tb_identifier'].iloc[0])

    def validate_rows(self):
        """
        # 判断每一列是否有用的，是否输出
        # 规则是：当前列的非空值超过设定比例 NON_EMPTY_RATIO 才判断为有用的列
        :return:
        """
        NON_EMPTY_RATIO = 0.3
        recognition_info_lib = []
        for index, row in self.body_df.groupby('td_identifier_arranged'):
            all_rows_amount = int(row['tr_identifier'].max())
            if all_rows_amount == 0:
                continue
            check_value_amount = len([x for x in row['td_content'].tolist() if x.strip() not in ['', '$']])
            if check_value_amount:
                self.valid_rows[index] = row
            else:
                # 将少于100个字符的文本数据收录到信息识别库，用于匹配货币符号
                # 将多余过长的字符去除，减少识别的用时
                invalid_info = list(set([x for x in row['td_content'].tolist() if x.strip() != '' and len(x.strip()) < 100]))
                recognition_info_lib.extend(invalid_info)
            self.body_rows.append(row)
        self.recognition_info_lib = list(set(recognition_info_lib))

        # 找到科目列和有用的值列，区分科目列和科目值列
        # 规则是：当前列的值的字母类型数量超过设定比例 STR_RATIO 判断为科目列；数字类型数量超过设定比例 INT_RATIO 判断为科目值列
        STR_RATIO = 0.5
        INT_RATIO = 0.1
        for index, row in sorted(self.valid_rows.items(), key=lambda d: d[0]):
            row_value = re.sub(r"[,.–—()\-\s]", '', ''.join([x for x in row['td_content'].tolist() if x.strip() != '']))
            char_count_res = char_count(row_value)
            char_count_rows_res = char_count_rows(row['td_content'].tolist())
            if char_count_res['total_count'] == 0:
                continue
            if char_count_rows_res['letter_rows'] / float(char_count_rows_res['total_rows']) > STR_RATIO:
                self.subject_df.append(row)
            # elif char_count_res['int_count'] / float(char_count_res['total_count']) > INT_RATIO:
            elif char_count_rows_res['num_rows']:
                self.valid_row_ids.append(index)
                self.subject_value_df.append(row)
            # 货币符号加入识别信息库
            if '$' in row_value:
                self.recognition_info_lib.append(['$'])

        self.subject_value_df = self.del_identical(self.subject_value_df, ['$'])

        # 发现美国数据的右边的括号“)”，很多情况是在另外的列（无用的列）里面，所以对科目值补全括号
        for si in self.subject_value_df:
            si_value = si['td_content'].tolist()
            si_index = si['td_content'].index
            for index, val in enumerate(si_value):
                # 去除空格和$
                val = re.sub(r'\s|\$| ', '', val)
                si_value[index] = val
                if val.strip() != '' and val[0] == '(' and ')' not in val and val[-1] != ')':
                    # 补全括号
                    si_value[index] = str(val) + ')'
            si['td_content'] = pd.Series(si_value, index=si_index)

    @staticmethod
    def del_identical(check_data, kill_signs):
        # 去除重复的列
        del_idx = []
        prev_row_index = None
        for index, row in enumerate(check_data):
            two_rows_identical = False
            if prev_row_index is None:
                prev_row_index = index
            else:
                prev_row = check_data[prev_row_index]
                prev_row_values = [x for x in prev_row['td_content'].tolist()]
                this_row_values = [x for x in row['td_content'].tolist()]
                if len(prev_row_values) != len(this_row_values):
                    continue
                kill_sign_indexes = [idx for idx, val in enumerate(prev_row_values) if val.strip() in kill_signs]
                for i in sorted(kill_sign_indexes, reverse=True):
                    try:
                        del prev_row_values[i]
                        del this_row_values[i]
                    except IndexError:
                        pass
                if prev_row_values == this_row_values:
                    two_rows_identical = True
                if two_rows_identical:
                    del_idx.append(prev_row_index)
                prev_row_index = index
        for i in sorted(del_idx, reverse=True):
            del check_data[i]
        return check_data

    def distinguish_header(self):
        """
        区分每一列header数据
        重构：根据每一列的colspan属性，计算每一列的对应的表头的值；若colspan大于0，则表示该列为多个列的表头值，分配到每一列的表头
        :return:
        """
        # 要去除的表头数据
        header_discard_lib = ['note', 'notes']
        # 表前部tb_front_content 按行号分组, 筛选出表格内的数据
        header_distinguished = []
        for index, row in self.tb_front_content.groupby('tr_identifier'):
            if row['is_table'].all() == 0:
                continue
            header_distinguished.append(row)
        if header_distinguished:
            # 按根据列宽重新排序的列分组
            header_rows = pd.concat(header_distinguished).groupby('td_identifier_arranged')
            for index, row in header_rows:
                columnIndex = row['td_identifier_arranged'].tolist()[0]
                header_text = ' '.join(row['td_content'].tolist())
                is_valid = 1 if index in self.valid_row_ids else 0
                if header_text.strip().lower() in header_discard_lib:
                    is_valid = 0
                # 封装IndexHeader对象，用于识别报表基本信息、时间信息
                self.header_columns[columnIndex] = IndexHeader(columnIndex, header_text, is_valid)

    def refine_tb_front_content(self, first_tr_id):
        check_range = range(int(first_tr_id) - 1, 0, -1)
        check_tr_id = first_tr_id
        for cr in check_range:
            check_line = self.table_df[self.table_df['tr_identifier'] == cr]
            check_line_content = ''.join(check_line[check_line['td_identifier'] > 1]['td_content'].tolist())
            check_line_content = re.sub('\xe2\x80\x8b', '', check_line_content).strip()
            if check_line_content == '':
                check_tr_id = cr
                continue
            else:
                break
        return check_tr_id


class IndexHeader:
    def __init__(self, columnIndex, text, is_valid):
        self.columnIndex = columnIndex
        self.text = text
        self.is_valid = is_valid if is_valid else 0  # 是否有用  0：无用 1：有用
        self.isConsolidated = -1  # 是否合并报表 -1：默认合并  0：母公司 1：合并
        self.time_begin = None
        self.time_end = None
