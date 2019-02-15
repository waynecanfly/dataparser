# -*- coding:utf-8 -*-
import csv

from algorithm.character_converge_pdf.container.line import Line

from algorithm.common import configManage


def mergeDigitValue(lineboxMap):
    for pageNum in lineboxMap.keys():
        for line in lineboxMap[pageNum]:
            line.x0 = round(line.x0)
            line.y0 = round(line.y0)
            line.x1 = round(line.x1)
            line.y1 = round(line.y1)


        # 以下先不要
        # digitSet = set()
        # for line in lineboxMap[pageNum]:
        #     line.x0 = round(line.x0)
        #     line.y0 = round(line.y0)
        #     line.x1 = round(line.x1)
        #     line.y1 = round(line.y1)
        #     digitSet.add(line.x0)
        #     digitSet.add(line.y0)
        #     digitSet.add(line.x1)
        #     digitSet.add(line.y1)
        #
        # digitList = sorted(digitSet)
        # digMergeMap = {digitList[0]:[]}
        # curDigt = digitList[0]
        # for i, digit in enumerate(digitList):
        #     d = digit - curDigt
        #     if d <=2 :
        #         digMergeMap[curDigt].append(digit)
        #     else:
        #         curDigt = digit
        #         digMergeMap[digit] = [digit]
        # mergeKeyValueMap = {}
        # for key in digMergeMap.keys():
        #     value = digMergeMap[key]
        #     for v in value:
        #         mergeKeyValueMap[v] = key
        #
        # for line in lineboxMap[pageNum]: #顺便判断线是横线还是竖线
        #     # if pageNum == 5:
        #     #     print str(line.x0) + ',' + str(line.y0) + ',' + str(line.x1) + ',' + str(line.y1) + ',' + str(line. width)  + ',' + str(line. height)
        #
        #     line.x0 = mergeKeyValueMap[line.x0]
        #     line.y0 = mergeKeyValueMap[line.y0]
        #     line.x1 = mergeKeyValueMap[line.x1]
        #     line.y1 = mergeKeyValueMap[line.y1]


def soureToSegment(lineboxMap):



    # setp 2 :
    for p in lineboxMap.keys():
        linebox = lineboxMap[p]


    # print 'd'






    # print 'd'

            # height = x.height if x.height>0 else 0
            # width = x.width if x.width>0 else 0
            # if height!=0 and width !=0:
            #     print str(height) + ' ' + str(width)



def getLineInfoSource(p_country, p_company, p_reportid):
    datapath = configManage.config['location']['pdf_line'] + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"
    datapath = datapath.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)

    lineboxMap = {}
    try:
        with open(datapath, 'rb') as f:
            content = csv.reader(f)
            for data in content:
                pageNum = int(data[0])
                newLine = Line(pageNum, data[1], data[2], data[3], data[4], data[5])
                # 过滤掉有复述的线
                if newLine.x0 < 0 or newLine.x1 < 0 or newLine.y0 < 0 or newLine.y1 < 0:
                    continue

                if pageNum not in lineboxMap:
                    lineboxMap[pageNum] = [newLine]
                else:
                    lineboxMap[pageNum].append(newLine)
        return lineboxMap
    except:
        return {}


def genLineSegment(linebox, direction):
    split_thr = 5
    # setp 1
    aimbox = []
    for l in linebox:
        temp = [l.y0, l.y1] if direction == 1 else [l.x0, l.x1]
        aimbox.append(temp)

    # setp 1.5  排序
    aimbox = sorted(aimbox, key=lambda x : x[0])

    segLines = {aimbox[0][0]: aimbox[0][1]}
    curSeg = [aimbox[0][0], aimbox[0][1]]
    for aim in aimbox:
        if aim[0] > curSeg[1] and abs(aim[0] - curSeg[1])>split_thr:
            curSeg = [aim[0], aim[1]]  # 新线段起点
            segLines[curSeg[0]] = curSeg[1]
        else:
            curSeg[1] = curSeg[1] if curSeg[1] > aim[1] else aim[1]
            segLines[curSeg[0]] = curSeg[1]

    segBox = []
    for begin in segLines:
        segBox.append([begin, segLines[begin]])

    # 过滤掉点
    segBox = [x for x in segBox if x[0] != x[1]]
    return segBox