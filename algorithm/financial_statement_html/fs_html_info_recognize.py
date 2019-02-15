# -*- coding: UTF-8 -*-
from algorithm.common.recognize_timeinfo import time_analyse


# header = {
#     "columnIndex":2,
#     "text":"期末余额",
#     "time_begin": "",
#     "time_end": ""
#     "currency": ""
#     "time_end": ""
#     "time_end": ""
# }
#
# table = {
#     "table_type": "BS",
#     "page_number": "1",
#     "title_text": "资产负债表",
#     "header_list": [header,...]
# }
#
# information_dic = {
#     "report_id": "CHN10001**********",
#     "tablebox": [table,...]
# }
from algorithm.financial_statement_html import recognize_baseinfo


def gen_para(reportid, table_map):
    table_box = []
    for id in table_map.keys():
        t = table_map[id]
        table_para = {}
        table_para['id'] = id
        table_para['table_type'] = t.table_type
        table_para['page_number'] = None
        table_para['isConsolidated'] = t.isConsolidated

        tb_front_content_ddp = []
        for i in t.tb_front_content['td_content'].tolist():
            if i not in tb_front_content_ddp:
                tb_front_content_ddp.append(i)
        title_area_text = ' '.join(tb_front_content_ddp)

        # 美国html需要用识别信息库去识别货币符号
        recognition_info = ''
        for info in t.recognition_info_lib:
            recognition_info += ''.join(info)
        table_para['title_text'] = title_area_text + recognition_info

        header_box = []
        for h_index in sorted(t.header_columns.keys()):
            header = t.header_columns[h_index]
            header_box.append({'columnIndex': header.columnIndex, 'text': header.text, 'time_begin': '', 'time_end': ''})
        table_para['header_list'] = header_box

        table_box.append(table_para)

    para = {'report_id': reportid, 'tablebox': table_box}
    return para


def recognize_info(reportid, tablebox):
    # tablebox转换成tablemap，方便识别后信息进行回天
    table_map = {}
    for index, table in enumerate(tablebox):
        table_map[index] = table

    # 生成识别所用的
    para = gen_para(reportid, table_map)

    # 时间识别(识别结果直接附在入参上)
    time_analyse.process(para)

    # 合并、母公司识别； 货币； 数量单位识别
    recognize_baseinfo.process(para)

    # 根据识别出来的信息回填到table对象中
    for t_result in para['tablebox']:
        table = table_map[t_result['id']]
        table.fiscal_year = t_result['fiscal_year']
        table.globalSeasonType = t_result['season_type']
        table.isConsolidated = t_result['isConsolidated']
        for h_result in t_result['header_list']:
            curHeader = table.header_columns[h_result['columnIndex']]
            curHeader.time_begin = h_result['time_begin']
            curHeader.time_end = h_result['time_end']
            curHeader.isConsolidated = h_result['isCon']
            curHeader.currency = h_result['currency']
            curHeader.measureunit = h_result['measureunit']

    return True

