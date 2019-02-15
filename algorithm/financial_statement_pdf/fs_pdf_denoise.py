# -*- coding:utf-8 -*-
import re

from algorithm.capture_table_pdf.containers.page import Page


def pageConverge(linebox_total):
    pagebox = []
    curPage = Page(linebox_total[0])
    for i in range(1, len(linebox_total)):
        l = linebox_total[i]
        if curPage.add(l) == 'reject':
            pagebox.append(curPage)
            curPage = Page(l)
    pagebox.append(curPage)
    return pagebox


def takeOutPageUselessBlock(linebox_total):
    # 按页码汇聚
    pagebox = pageConverge(linebox_total)
    REPEAT_THR = 3
    pageTop3AndLast3LineMap = {0:[], 1:[], 2:[], -1:[], -2:[], -3:[]}
    for page in pagebox:
        try:
            pageTop3AndLast3LineMap[0].append(page.linebox[0]) if page.linebox[0].y0 > 500 else ''
            pageTop3AndLast3LineMap[1].append(page.linebox[1]) if page.linebox[1].y0 > 500 else ''
            pageTop3AndLast3LineMap[2].append(page.linebox[2]) if page.linebox[2].y0 > 500 else ''
            pageTop3AndLast3LineMap[-1].append(page.linebox[-1]) if page.linebox[-1].y0 < 500 else ''
            pageTop3AndLast3LineMap[-2].append(page.linebox[-2]) if page.linebox[-2].y0 < 500 else ''
            pageTop3AndLast3LineMap[-3].append(page.linebox[-3]) if page.linebox[-3].y0 < 500 else ''
        except Exception:
            pass

    pageLineTakeOutMap = {}
    for lineNum in pageTop3AndLast3LineMap.keys():
        lines = pageTop3AndLast3LineMap[lineNum]
        pageLineTakeOutMap[lineNum] = []
        classifyMap = {}
        # classify
        for l in lines:
            try:
                withoutdigitText = re.sub('\s', '', re.sub('\d+', '*', l.text)).encode('utf-8')
            except:
                withoutdigitText = l.text
            if withoutdigitText not in classifyMap:
                classifyMap[withoutdigitText] = [l]
            else:
                classifyMap[withoutdigitText].append(l)
        for linesPerKind in classifyMap.values():
            kindAmonut = len(linesPerKind)
            # if (kindAmonut > 5) or (kindAmonut / pageAmonut >= 0.4 and kindAmonut>2):
            if kindAmonut > REPEAT_THR:
                for l in linesPerKind:
                    pageLineTakeOutMap[lineNum].append(l.pageNum)

    for page in pagebox:
        pageNum = page.pageNum

        if pageNum in pageLineTakeOutMap[2] and pageNum in pageLineTakeOutMap[1] and pageNum in pageLineTakeOutMap[0]:
            page.linebox[2].is_useful = False

        if pageNum in pageLineTakeOutMap[1] and pageNum in pageLineTakeOutMap[0]:
            page.linebox[1].is_useful = False

        if pageNum in pageLineTakeOutMap[0]:
            page.linebox[0].is_useful = False


        if pageNum in pageLineTakeOutMap[-3] and pageNum in pageLineTakeOutMap[-2] and pageNum in pageLineTakeOutMap[-1]:
            page.linebox[-3].is_useful = False
        if pageNum in pageLineTakeOutMap[-2] and pageNum in pageLineTakeOutMap[-1]:
            page.linebox[-2].is_useful = False
        if pageNum in pageLineTakeOutMap[-1]:
            page.linebox[-1].is_useful = False