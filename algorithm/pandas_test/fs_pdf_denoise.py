# -*- coding:utf-8 -*-
import re


def pageIsUseful(page):
    LINE_BLOCK_NUM_THRESHOLD = 2
    LEGAL_LINE_THRESHOLD = 2
    counter = 0
    lineGroup = dict(list(page.groupby('lineIndex')))

    for line in lineGroup.values():
        if len(line) < LINE_BLOCK_NUM_THRESHOLD:
            continue
        t = line.type
        if 'digit' in list(line.type):
            counter += 1

    # print counter
    return True if counter >= LEGAL_LINE_THRESHOLD else False

def genPureText(all, x):
    linetexts = all.loc[(all.pageNum == x.pageNum) & (all.lineIndex == x.lineIndex)]['text']
    return re.sub('\s', '', re.sub('\d+', '*', ''.join(linetexts.tolist())))


def uselessPage(df):

    discard = []
    pageGroup = df.groupby('pageNum')
    for pageNum, page in pageGroup:
        if not pageIsUseful(page):
            discard.append(pageNum)
    df.loc[df.pageNum.map(lambda x: x in discard), 'isUseful'] = 0


def uselessText(df):
    REPEAT_THR = 5

    df['lineNum'] = df.apply(lambda x: df.loc[df.pageNum == x.pageNum].lineIndex.max() + 1, axis=1)

    df['denoiseIndex'] = df.apply(lambda x: x.lineIndex if x.y0>500 else x.lineIndex-x.lineNum, axis=1)

    denosieRange = df.loc[df["denoiseIndex"].isin([0,1,2,-1,-2,-3])]

    pureLineText = denosieRange.apply(lambda x: genPureText(denosieRange, x), axis=1)
    denosieRange.insert(2, 'pureLineText', pureLineText)

    groups = dict(list(denosieRange.groupby(['pureLineText', 'denoiseIndex'])))
    for groupKey in groups.keys():
        pageNums = groups[groupKey].pageNum.unique().tolist()
        if len(pageNums) >= REPEAT_THR:
            df.loc[df.apply(lambda x: (x.pageNum in pageNums) and (x.denoiseIndex == groupKey[1]), axis=1), 'isUseful'] = 0

def denoise(df):
    # take out useless page(not necessary; have some side-effect)
    uselessPage(df)

    # take out useless text
    uselessText(df)

