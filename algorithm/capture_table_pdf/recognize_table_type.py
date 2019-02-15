# -*- coding: UTF-8 -*-
import copy

from capture_table_exceptions import StatementNotFound
from algorithm.common import dbtools
from algorithm.common_tools_pdf import title_match_tools


def getTitleText(titleblocks):
    titleText = ''
    for t in titleblocks:
        titleText = titleText + ' ' + t.text
    return titleText.strip()

def getFSdescribeFromLib():
    title_lib = {}
    sql = 'select matchcode, tabletype from title_match_lib'
    result = dbtools.query_pdfparse(sql)
    for unit in result:
        key = title_match_tools.getMatchTitleText(unit[0].encode('utf-8'))
        title_lib[key] = unit[1]
    return title_lib



def isDiscard(text):
    discard = ['notes']
    for d in discard:
        if d in text:
            return True
    return False

def recognize_tabletype(tablebox, reportid):
    # get lib
    title_lib = getFSdescribeFromLib()

    # match
    tabletypes = set()
    tabletypes = recognizeMehtod1(tablebox, title_lib, tabletypes)

    # if len(tabletypes) < 3:
    #     print 'herehereherehereherehereherehereherehereherehereherehere'
    #     recognizeMehtod2(tablebox, title_lib, tabletypes)

    # print tabletypes
    if not tabletypes:
        raise StatementNotFound('statement not found')

def titleLineConverge(titlebox):
    lineConvergeMap = {}
    for t in titlebox:
        if t.lineIndex in lineConvergeMap:
            lineConvergeMap[t.lineIndex].text = lineConvergeMap[t.lineIndex].text + ' ' + t.text
            lineConvergeMap[t.lineIndex].x0 = lineConvergeMap[t.lineIndex].x0 if lineConvergeMap[t.lineIndex].x0 < t.x0 else t.x0
            lineConvergeMap[t.lineIndex].x1 = lineConvergeMap[t.lineIndex].x1 if lineConvergeMap[t.lineIndex].x1 > t.x1 else t.x1
            lineConvergeMap[t.lineIndex].y0 = lineConvergeMap[t.lineIndex].y0 if lineConvergeMap[t.lineIndex].y0 < t.y0 else t.y0
            lineConvergeMap[t.lineIndex].y1 = lineConvergeMap[t.lineIndex].y1 if lineConvergeMap[t.lineIndex].y1 > t.x0 else t.y1
        else:
            lineConvergeMap[t.lineIndex] = copy.deepcopy(t)
    return lineConvergeMap.values()


def judgeIfTitleInlib(matchText, title_lib):
    for title in title_lib.keys():
        if matchText == title:
            dbtools.query_pdfparse(
                "update title_match_lib set num_of_use=num_of_use + 1 where matchcode='" + matchText + "'")
            return True
    return False

def recognizeMehtod1(tablebox, title_lib, tabletypes):
    for t in tablebox:
        if t.pageNum == 80:
            pass
        titleboxCutIndex = 0
        titlePageNum = 0
        if not t.title:
            continue
        t.title.reverse()
        isMatched = False
        for index, t_line in enumerate(t.title):
            for t_block in t_line.blockbox:
                matchText = title_match_tools.getMatchTitleText(t_block.text)
                if judgeIfTitleInlib(matchText, title_lib):
                    t.table_type = title_lib[matchText]
                    t_block.identity = 'title'
                    titleboxCutIndex = index
                    titlePageNum = t_line.pageNum
                    isMatched = True
                    tabletypes.add(t.table_type)
                    break
            if not isMatched:
                matchText = title_match_tools.getMatchTitleText(t_line.text)
                if judgeIfTitleInlib(matchText, title_lib):
                    t.table_type = title_lib[matchText]
                    for b in t_line.blockbox:
                        b.identity = 'title'
                    titleboxCutIndex = index
                    titlePageNum = t_line.pageNum
                    tabletypes.add(t.table_type)
                    isMatched = True
                    break
            else:
                break

        # 缩减title范围
        if isMatched:
            newTitleBox = []
            for i, tb in enumerate(t.title):
                if i <= titleboxCutIndex:
                    newTitleBox.append(tb)
            t.title = newTitleBox
            t.title.reverse()

    return tabletypes


def recognizeMehtod2(tablebox, title_lib, tabletypes):
    for t in tablebox:
        if not t.title:
            continue
        titleText = getTitleText(t.title)
        matchTitleText = title_match_tools.getMatchTitleText(titleText)

        # check if is discard
        if isDiscard(matchTitleText):
            continue

        for title in title_lib.keys():
            if title in matchTitleText:
                dbtools.query_pdfparse(
                    "update title_match_lib set num_of_use=num_of_use + 1 where matchcode='" + matchTitleText + "'")
                t.table_type = title_lib[title]
                tabletypes.add(title_lib[title])