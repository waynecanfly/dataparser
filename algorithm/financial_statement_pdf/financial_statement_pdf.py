# -*- coding:utf-8 -*-
import re
import sys
import time
import traceback

import fs_pdf_tools
from algorithm.common import tools, configManage
from algorithm.common.para import Para
from algorithm.financial_statement_pdf import fs_pdf_check
from algorithm.financial_statement_pdf import fs_pdf_denoise, fs_pdf_structure, fs_handling_push
from algorithm.financial_statement_pdf.find_fs_table import find_fs_table
from algorithm.financial_statement_pdf.find_fs_title import find_fs_title
from algorithm.financial_statement_pdf.fs_pdf_check import final_check
from algorithm.financial_statement_pdf.fs_pdf_info_recognize import info_recognize
from algorithm.financial_statement_pdf.fs_pdf_packdata import pack_output_data


def process(para, istest=False):
    p_country, p_company, p_reportid = para.countryid, para.companyid, para.reportid
    try:
        # 获取数据
        root_path = configManage.config['location']['pdf_block_noline'] if para.statusid == 40 else configManage.config['location']['pdf_block']
        datapath =  root_path + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"
        datapath = datapath.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)
        blockBox = fs_pdf_tools.getSourceData(datapath)

        # 按行进行汇聚
        linebox_total = fs_pdf_tools.lineConverge(blockBox)

        # 识别出每一页开头和结尾中无用的字符串，以免影响跨页报表的查找
        fs_pdf_denoise.takeOutPageUselessBlock(linebox_total)

        # 全文识别报表标题
        title_anchor = find_fs_title(linebox_total, para.reportid, para.company_name)

        # 根据识别出来的title作为锚点，查找表
        table_box = find_fs_table(title_anchor, linebox_total, p_reportid)

        # 信息识别： 货币、数量单位、时间(年份、季度)、合并与否
        info_recognize(p_reportid, table_box)

        # 表结构整理(科目合并、一行多列科目等等)
        fs_pdf_structure.structure(table_box,para)

        # 检查
        fs_pdf_check.process(p_reportid,table_box)

        # 生成输出数据的结构
        pack_output_data(table_box, para.company_name)

        # 数据的最终检查步骤
        final_check(table_box)

        # 数据输出（数据整理输出）
        fs_pdf_tools.output(table_box, p_reportid, p_country, p_company, istest)

        # 检查是不是测试，如果时测试的话，直接返回数据，不改状态
        if istest:
            return table_box

        # 更新状态
        tools.updatePDFStatus(p_country, p_company, p_reportid, 50, '')

    except Exception as e:
        excepttext = traceback.format_exc()
        print p_reportid + '\n' + excepttext
        # 因为暂时所有的exception的处理逻辑都是一样的， 用errorcode进行情况区分即可，所以每必要区分那么多不同的报错
        if not istest:
            excepttext = re.sub('\n', ' ', excepttext)
            excepttext = re.sub('\"', '\'', excepttext)
            message =  re.sub('\n|\"|\'', '', str(e.message))
            # update_status = 31 if para.statusid == 40 and e.message in ['NOT_ALL_FOUND_TITLE', 'USELESS_PDF'] else -90
            update_status = -30 if para.statusid == 20 else -50
            tools.updatePDFStatus(p_country, p_company, p_reportid, update_status, '', message)
        else:
            return str(e.message)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)


    # fs_pdf_tools.data_counter()



    # 样本中有问题的（原来能跑出来，后来跑步出来）
    # new subject



    # all-half
    box = ['CHN102222010000301032']



    for i, l in enumerate(box):
        print str(i) + '  ========================================='
        reportid = l
        countryid = reportid[0:3]
        companyid = reportid[0:8]
        companyname = fs_pdf_tools.getCompanyName(companyid)
        # countryid, companyid, reportid, statusid, country_name, company_name, fiscal_year,season_type_code, history_status, data_mark, doc_path, doc_type, report_type, error_code = '')
        para = Para(countryid, companyid, reportid, 20, '2', companyname, '4', '5', '6', '7', 'x', '8', '9','','SC010','')

        begin = time.time()
        try:
            process(para, False)
        except  Exception as e:
            excepttext = traceback.format_exc()
            print excepttext
            tools.updatePDFStatus(countryid, companyid, reportid, -70, '')

        # outputstr = tools.linkStr([tools.linktr(x, ',') for x in configManage.new_header.values()], '\n')

        end = time.time()-begin
