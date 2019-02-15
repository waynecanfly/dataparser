# -*- coding:utf-8 -*-
import re
import traceback

import capture_table_tool
import match_table
from algorithm.common_tools_pdf import the_guardian
from capture_table_exceptions import NoTableInPDFException, StatementNotFound, \
    StatementNotAllFound, TableIncomplete
from capture_table_tool import outputTables
from algorithm.common import tools, configManage, dbtools
from recognize_table_type import recognize_tabletype

def process(para, isReRun=False):
    p_country, p_company, p_reportid = para.countryid, para.companyid, para.reportid
    valid_page_box = []
    valid_table_box = []
    try:
        # get patterns
        patterns = capture_table_tool.getPatterns()

        datapath = configManage.config['location']['pdf_block'] + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"
        datapath = datapath.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)

        # get sources
        blockBox = capture_table_tool.getSourceData(datapath)

        # line converge
        linebox_total = capture_table_tool.lineConverge(blockBox)

        # page converge
        pagebox = capture_table_tool.pageConverge(linebox_total)

        # take out end and begin useless block
        capture_table_tool.takeOutPageUselessBlock(pagebox)


        # 过滤无用page
        valid_page_box = capture_table_tool.filterPage(pagebox)
        # valid_page_box = pagebox

        pageMap = capture_table_tool.getPageMap(pagebox)

        # 提取表
        table_box = match_table.matchTable(pageMap, valid_page_box, patterns)

        # 识别表类型
        recognize_tabletype(table_box, p_reportid)

        # 找到页面底部都没有结束的表继续往下一页找  --
        table_box = capture_table_tool.fittingNonFinishTable(table_box, pagebox)

        # 列号修正. 由于有些线有轻微的错位，所以现在默认的以左边的线作为columnidex并不严谨
        capture_table_tool.fitting_columnindex(table_box)

        # 过滤非法表格。过滤无titlte及非目标报表及body为空的报表
        valid_table_box = capture_table_tool.filterIllegalTable(table_box)

        # 判断是否为独立报表，并判断报表是否找齐。 # status:33 not all found
        isHaveConsolidated = capture_table_tool.judgeIfHadFoundAllAimTable(valid_table_box)


        # 获取待输出报表
        output_table_box = [table for table in valid_table_box if table.isConsolidated == 1] if isHaveConsolidated else valid_table_box

        # 一个pdf中找出多个同类型表时，判断是否有些是无用的需要过滤掉
        output_table_box = capture_table_tool.kindredTableTypeFilter(output_table_box)


        # check module. pageMap output_table_box
        the_guardian.check(pageMap, table_box, output_table_box, p_reportid)



        # 输出表信息
        outputTables(output_table_box, p_country, p_company, p_reportid)
        if isHaveConsolidated:
            aloneTable = [table for table in valid_table_box if table.isConsolidated != 1]
            outputTables(aloneTable, p_country, p_company, p_reportid, False)

        # 更新状态
        tools.updatePDFStatus(p_country, p_company, p_reportid, 30, '')

        # 删除旧数据. 不管重跑与否，都执行一边删除标记库里面的数据
        dbtools.deleteDataByReportID('opd_pdf_structure_mark', p_reportid)
        dbtools.deleteDataByReportID('opd_pdf_identified_table', p_reportid)

        return True

    except NoTableInPDFException as notable:
        excepttext = traceback.format_exc()
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)
        tools.updatePDFStatus(p_country, p_company, p_reportid, 31, excepttext)
    except TableIncomplete as tableincomplete:
        excepttext = traceback.format_exc()
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)
        tools.updatePDFStatus(p_country, p_company, p_reportid, 37, 'Table Incomplete')
    except StatementNotFound as found_0:
        excepttext = traceback.format_exc()
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)

        if isReRun:  # 如果是重跑的话什么都不干,把锁放开就好
            tools.lockoff(p_country, p_company, p_reportid)
        elif capture_table_tool.structureMarkIsFull(): # 如果不是重跑，且标记库满了，则不需要把数据入库到structure mark表，处理状态改成 35
            tools.updatePDFStatus(p_country, p_company, p_reportid, 35, excepttext)
        else:  # 如果不是重跑，且标记库未满，把数据入库到structure mark表，处理状态改成 33
            capture_table_tool.outputTableStructureMarkSource(p_country, p_company, p_reportid, valid_page_box, valid_table_box)
            tools.updatePDFStatus(p_country, p_company, p_reportid, 33, excepttext)

    except StatementNotAllFound as notAllFound:
        excepttext = traceback.format_exc()
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)

        if isReRun:  # 如果是重跑的话什么都不干,把锁放开就好
            tools.lockoff(p_country, p_company, p_reportid)
        elif capture_table_tool.structureMarkIsFull(): # 如果不是重跑，且标记库满了，则不需要把数据入库到structure mark表，处理状态改成 35
            tools.updatePDFStatus(p_country, p_company, p_reportid, 35, excepttext)
        else:  # 如果不是重跑，且标记库未满，把数据入库到structure mark表，处理状态改成 33
            capture_table_tool.outputTableStructureMarkSource(p_country, p_company, p_reportid, valid_page_box, valid_table_box)
            tools.updatePDFStatus(p_country, p_company, p_reportid, 33, excepttext)

    except Exception as e:
        excepttext = traceback.format_exc()
        print p_reportid + '\n' + excepttext
        excepttext = re.sub('\n', ' ', excepttext)
        excepttext = re.sub('\"', '\'', excepttext)
        tools.updatePDFStatus(p_country, p_company, p_reportid, -30, excepttext)