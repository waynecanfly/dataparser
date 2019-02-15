# -*- coding:utf-8 -*-
import re
import sys
import traceback

import fs_pdf_tools
from algorithm.common import tools, configManage
from algorithm.common.para import Para
import fs_pdf_denoise
import fs_pdf_capture
from algorithm.pandas_test.fs_pdf_exceptions import StatementNotAllFound


def process(para):
    countryid, companyid, reportid = para.countryid, para.companyid, para.reportid
    valid_page_box = []
    valid_table_box = []
    try:
        # get sources
        block_df = fs_pdf_tools.get_data(countryid, companyid, reportid)

        # denosie: useless page and useless text
        fs_pdf_denoise.denoise(block_df)

        # line convergel
        line_box = fs_pdf_tools.line_converge(block_df)


        # 提取表
        table_box = fs_pdf_capture.capture(line_box)

        tools.updatePDFStatus(countryid, companyid, reportid, 30, '')
    #
    #     # 识别表类型
    #     recognize_tabletype(table_box, p_reportid)
    #
    #     # 找到页面底部都没有结束的表继续往下一页找  --
    #     table_box = capture_table_tool.fittingNonFinishTable(table_box, pagebox)
    #
    #     # 列号修正. 由于有些线有轻微的错位，所以现在默认的以左边的线作为columnidex并不严谨
    #     capture_table_tool.fitting_columnindex(table_box)
    #
    #     # 过滤非法表格。过滤无titlte及非目标报表及body为空的报表
    #     valid_table_box = capture_table_tool.filterIllegalTable(table_box)
    #
    #     # 判断是否为独立报表，并判断报表是否找齐。 # status:33 not all found
    #     isHaveConsolidated = capture_table_tool.judgeIfHadFoundAllAimTable(valid_table_box)
    #
    #
    #     # 获取待输出报表
    #     output_table_box = [table for table in valid_table_box if table.isConsolidated == 1] if isHaveConsolidated else valid_table_box
    #
    #     # 一个pdf中找出多个同类型表时，判断是否有些是无用的需要过滤掉
    #     output_table_box = capture_table_tool.kindredTableTypeFilter(output_table_box)
    #
    #
    #     # check module. pageMap output_table_box
    #     the_guardian.check(pageMap, table_box, output_table_box, p_reportid)
    #
    #
    #
    #     # 输出表信息
    #     outputTables(output_table_box, p_country, p_company, p_reportid)
    #     if isHaveConsolidated:
    #         aloneTable = [table for table in valid_table_box if table.isConsolidated != 1]
    #         outputTables(aloneTable, p_country, p_company, p_reportid, False)
    #
    #     # 更新状态
    #     tools.updatePDFStatus(p_country, p_company, p_reportid, 30, '')
    #
    #     # 删除旧数据. 不管重跑与否，都执行一边删除标记库里面的数据
    #     dbtools.deleteDataByReportID('opd_pdf_structure_mark', p_reportid)
    #     dbtools.deleteDataByReportID('opd_pdf_identified_table', p_reportid)
    #
    #     return True
    #
    # except NoTableInPDFException as notable:
    #     excepttext = traceback.format_exc()
    #     excepttext = re.sub('\n', ' ', excepttext)
    #     excepttext = re.sub('\"', '\'', excepttext)
    #     tools.updatePDFStatus(p_country, p_company, p_reportid, 31, excepttext)
    # except TableIncomplete as tableincomplete:
    #     excepttext = traceback.format_exc()
    #     excepttext = re.sub('\n', ' ', excepttext)
    #     excepttext = re.sub('\"', '\'', excepttext)
    #     tools.updatePDFStatus(p_country, p_company, p_reportid, 37, 'Table Incomplete')
    # except StatementNotFound as found_0:
    #     excepttext = traceback.format_exc()
    #     excepttext = re.sub('\n', ' ', excepttext)
    #     excepttext = re.sub('\"', '\'', excepttext)
    #
    #     if isReRun:  # 如果是重跑的话什么都不干,把锁放开就好
    #         tools.lockoff(p_country, p_company, p_reportid)
    #     elif capture_table_tool.structureMarkIsFull(): # 如果不是重跑，且标记库满了，则不需要把数据入库到structure mark表，处理状态改成 35
    #         tools.updatePDFStatus(p_country, p_company, p_reportid, 35, excepttext)
    #     else:  # 如果不是重跑，且标记库未满，把数据入库到structure mark表，处理状态改成 33
    #         capture_table_tool.outputTableStructureMarkSource(p_country, p_company, p_reportid, valid_page_box, valid_table_box)
    #         tools.updatePDFStatus(p_country, p_company, p_reportid, 33, excepttext)
    #
    except StatementNotAllFound as notAllFound:
        message = notAllFound.message
        message = re.sub('\n', ' | ', message)
        tools.updatePDFStatus(countryid, companyid, reportid, -30, message, 'TITLE_INCOMPLETE')

    except Exception as e:
        excepttext = traceback.format_exc()
        print reportid + '\n' + excepttext
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)
        tools.updatePDFStatus(countryid, companyid, reportid, -30, excepttext)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    configManage.initConfig(False)

    reportid = 'CHN100242009000201038'
    # reportid = 'CHN100692014000201010'
    # reportid = 'CHN100212013000301022'
    countryid = reportid[0:3]
    companyid = reportid[0:8]
    para = Para(countryid, companyid, reportid, '1', '2', '3', '4', '5', '6', '7', 'x', '8', '9')
    process(para)
