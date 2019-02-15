# -*- coding:utf-8 -*-

import re
from algorithm.common import tools
from algorithm.character_converge_pdf.container.word import Word


def overlapRate(firstYRange, secondYRange, firstText, secondText, nRange):
    if firstYRange[0] > secondYRange[1] or secondYRange[0] > firstYRange[1]:
        return 0
    if '`' == firstText:
        lR = pureoverlapRate(firstYRange, secondYRange)
        nR = pureoverlapRate(secondYRange, nRange)

        if lR >= nR:
            return 1
        else:
            return 0
    elif secondText == '`':
        return 1
    else:
        return pureoverlapRate(firstYRange, secondYRange)

def isuseful(word):
    dicardR = re.compile("(-{3,1000})|(\.{3,1000})")
    if word.text == '`' or dicardR.match(word.text):
        return False
    return True

def pureoverlapRate(firstYRange, secondYRange):
    borderList = (firstYRange + secondYRange)
    borderList.sort()
    firstGap = abs(firstYRange[1] - firstYRange[0])
    secondGap = abs(secondYRange[1] - secondYRange[0])
    overlapGap = abs(borderList[2] - borderList[1])
    return overlapGap / min(firstGap, secondGap) if min(firstGap, secondGap) != 0 else 1

def isKeep(text):
    pureText = re.sub('\s', '', text)
    if pureText == '':
        return False
    else:
        return True

def process(charBox):
    wordBox = []

    fc = charBox[0]
    currentW = Word(fc.pageNum, fc.text, fc.x0, fc.y0, fc.x1, fc.y1, fc.direction, fc.size, fc.x1-fc.x0 if fc.direction==1 else fc.y1-fc.y0, fc.font)
    tailC = fc
    character_width = fc.x1 - fc.x0
    is_Italic = None

    for cIndex in range(1, len(charBox)):
        c = charBox[cIndex]
        together = False

        # if c.pageNum == 125 and c.text == 'E' and currentW.text == 'CONSOLIDAT':
        #     pass
        j1 = currentW.pageNum == c.pageNum
        j2 = currentW.direction == c.direction
        j3 = currentW.size == c.size
        j4 = tools.comparexy(currentW.y0, c.y0)
        j5 = tools.comparexy(c.x0, tailC.x0)
        j6 = tailC.text == c.text
        j6 = True
        if j1 and j2 and j3 and j4 and j5 and j6:
            continue

        useless_char_box = ['_']

        if c.text in useless_char_box:
            continue

        isOneWord = tools.isOneWord(c.x0, tailC.x1, j4)
        if j1 and j2 and j3 and j4 and isOneWord:
            character_width = c.x1 - c.x0
            together = True
        if together:
            currentW.text = currentW.text + c.text
            currentW.x0 = (currentW.x0 if currentW.x0 < c.x0 else c.x0)
            currentW.x1 = (currentW.x1 if currentW.x1 > c.x1 else c.x1)
            currentW.y0 = (currentW.y0 if currentW.y0 < c.y0 else c.y0)
            currentW.y1 = (currentW.y1 if currentW.y1 > c.y1 else c.y1)
            currentW.character_width = (currentW.character_width if currentW.character_width > character_width else character_width)
        else:
            if isuseful(currentW):
                wordBox.append(currentW)
            currentW = Word(c.pageNum, c.text, c.x0, c.y0, c.x1, c.y1, c.direction, c.size, c.x1-c.x0, c.font)
        tailC = c

    if isuseful(currentW):
        wordBox.append(currentW)

    # lineIndex, columnIndex, type
    wordBoxLen = len(wordBox)
    for i, w in enumerate(wordBox):
        if i == 0:
            w.lineIndex = 0
            w.columnIndex = 0
            continue
        lw = wordBox[i-1]
        nw = wordBox[i+1 if i+1 <= wordBoxLen-1 else wordBoxLen-1]
        if w.pageNum != lw.pageNum or w.direction != lw.direction:
            w.lineIndex = 0
            w.columnIndex = 0
        else:
            overlap = overlapRate([w.y0, w.y1], [lw.y0, lw.y1], w.text, lw.text, [nw.y0, nw.y1])
            if tools.comparexy(w.y0, lw.y0) or overlap >= 0.85:
                w.lineIndex = lw.lineIndex
                w.columnIndex = lw.columnIndex + 1
            else:
                w.lineIndex = lw.lineIndex + 1
                w.columnIndex = 0

    # 封装成以pageum为key的map
    wordBoxMap = {}
    order = 0
    for w in wordBox:
        if w.pageNum not in wordBoxMap:
            order = 0
            wordBoxMap[w.pageNum] = [w]

        else:
            wordBoxMap[w.pageNum].append(w)
            order += 1
        w.order = order

    return wordBoxMap