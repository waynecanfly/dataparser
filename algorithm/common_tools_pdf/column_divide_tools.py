# -*- coding: UTF-8 -*-


def resetRefer(refer, range):
    return [refer[0] if refer[0] < range[0] else range[0], refer[1] if refer[1] > range[1] else range[1]]

def genReferLine(blockbox):
    useful_rangebox = []
    source_rangebox = []
    referLine = []

    for b in blockbox:
        source_rangebox.append([float(b.x0), float(b.x1), b.lineIndex])

    for r in source_rangebox:
        intersectNumPerLine = {}
        for r1 in source_rangebox:
            if not (r[0] >= r1[1] or r[1] <= r1[0]):  #相交
                # 统计每行相交数量
                if r1[2] in intersectNumPerLine:
                    intersectNumPerLine[r1[2]] = intersectNumPerLine[r1[2]] + 1
                else:
                    intersectNumPerLine[r1[2]] = 1
        if len(intersectNumPerLine) == 0:
            continue
        if max(intersectNumPerLine.values()) <= 1:
            useful_rangebox.append(r)

    for i, range in enumerate(useful_rangebox):
        isNew = True
        for k, refer in enumerate(referLine):
            if not (range[0] >= refer[1] or range[1] <= refer[0]): # 相交，取范围大的
                referLine[k] = resetRefer(refer, range)
                isNew = False
                break
        if isNew:
            referLine.append(range)

    referLine = sorted(referLine, key=lambda refer: refer[0])

    referAndIndex = []

    for i, refer in enumerate(referLine):
        referAndIndex.append({
            'x0': refer[0],
            'x1': refer[1],
            'index': (i+1)*100
        })
    return referAndIndex

def culateColumnIndex(blockbox):
    # gen refer Line
    referLine = genReferLine(blockbox)

    # header recalculate column index
    for block in blockbox:
        block.columnIndexs = []
        for k, refer in enumerate(referLine):
            if not (block.x0 >= refer['x1'] or block.x1 <= refer['x0']):
                block.columnIndexs.append(refer['index'])
            elif block.x1 < refer['x0'] and len(block.columnIndexs)==0: # 特殊原因和算法问题， 导致丢失的
                lastIndex  = referLine[k-1]['index'] if k>0 else 0
                block.columnIndexs.append(int((refer['index'] + lastIndex)/2))
                break

    # index 归一化
    indexSet = set()
    for b in blockbox:
        for i in b.columnIndexs:
            indexSet.add(i)

    indexList = sorted(list(indexSet))

    indexMap = {}
    for x,index in enumerate(indexList):
        indexMap[index] = x

    for b in blockbox:
        for i in range(0, len(b.columnIndexs)):
            b.columnIndexs[i] = indexMap[b.columnIndexs[i]]

    return referLine


