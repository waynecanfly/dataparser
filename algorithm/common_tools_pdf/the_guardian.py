# -*- coding:utf-8 -*-
from algorithm import common_tools_pdf
from algorithm.capture_table_pdf.capture_table_exceptions import TableIncomplete
from algorithm.common import configManage
from algorithm.common_tools_pdf import standerSubjectLib


def check(pagemap, tablebox, output_table_box, reportid):
    exitTableRange = []
    for t in tablebox:
        for h in t.headerLineBox:
            exitTableRange.append(str(h.pageNum) + "_" + str(h.lineIndex))
        for b in t.body:
            exitTableRange.append(str(b.pageNum) + "_" + str(b.lineIndex))
        if t.table_type != 'unknow':
            for tl in t.title:
                exitTableRange.append(str(tl.pageNum) + "_" + str(tl.lineIndex))

    for t in output_table_box:
        endPoint = [t.body[-1].pageNum, t.body[-1].lineIndex]
        checkRange = []
        findFinish = False
        for pageNum in sorted(pagemap.keys()):
            if pageNum < endPoint[0]:
                continue
            page = pagemap[pageNum]
            for l in page.linebox:
                if pageNum == endPoint[0] and l.lineIndex <= endPoint[1]:
                    continue
                elif str(l.pageNum) + "_" + str(l.lineIndex) in exitTableRange:
                    findFinish = True
                    break
                checkRange.append(l)
                if len(checkRange) >= 3:
                    findFinish = True
                    break
            if findFinish:
                break

        for cr in checkRange:
            pureS = common_tools_pdf.subject_match_tools.getPureSbuectText(cr.blockbox[0].text)
            if pureS in standerSubjectLib.subjects:
                configManage.logger.error(reportid + ' TableIncomplete: ' + cr.text + ' | ' + str(cr.pageNum))
                print reportid + ' TableIncomplete: ' + cr.text + ' | ' + str(cr.pageNum)
                raise TableIncomplete("table Incomplete")
    return True