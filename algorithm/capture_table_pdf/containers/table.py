# -*- coding: UTF-8 -*-
import copy
import re

from algorithm.capture_table_pdf.containers.headerUnit import HeaderUnit
from algorithm.common_tools_pdf import header_match_tools, column_divide_tools, standerSubjectLib, subject_match_tools


class Table:
    def __init__(self, lastpage, page, index_header_map, header_beginindex, headerLineBox, linetableid):
        if page.pageNum == 4:
            pass
        self.bodyFoundFinish = False
        self.table_type = 'unknow'
        self.lastpage = lastpage
        self.page = page
        self.pageNum = page.pageNum
        self.index_header_map = index_header_map
        self.headerLineBox = headerLineBox
        self.headerRange = [headerLineBox[0].lineIndex, headerLineBox[-1].lineIndex]
        self.headerLineNums = [x.lineIndex for x in headerLineBox]

        self.title = []   # unit: block
        self.body = []  # unit: line
        self.unknow = []  # unit: line
        self.body_buffer = []

        self.isOnlyHaveHeader = None

        self.findTitle(header_beginindex)

        self.isConsolidated = -1  # 1 yes 0 no  -1 unknow

        self.linetableid = linetableid

    def findTitle(self, header_beginindex):

        title_linebox = self.page.linebox[0: header_beginindex]

        if len(title_linebox) == 0:
            self.isOnlyHaveHeader = True
        else:
            self.isOnlyHaveHeader = False

        # 如果本页剩余的title少于5行，则往上一页再找5行
        title_linebox = self.lastpage.linebox[-5:] + title_linebox if self.lastpage is not None and len(title_linebox) < 5 else title_linebox

        title_linebox.reverse()
        # title region
        title_linebox = title_linebox[0: 6]
        title_linebox.reverse()

        for l in title_linebox:
            self.title.append(l)

    def checkLine(self, line):
        for b in line.blockbox:
            b.columnIndexs = b.lineColumnIndex
            b.columnIndex = b.columnIndexs[0]
            for i in b.columnIndexs:
                try:
                    header = self.index_header_map[i]
                except:
                    continue
                if header.identity == 'value' and b.type not in ('digit', 'placeholder', 'currency'):
                    return False
        return True

    def addToHeader(self, line):
        self.headerRange[1] = line.lineIndex
        self.headerLineNums.append(line.lineIndex)
        for b in line.blockbox:
            for i in b.lineColumnIndex:
                header = self.index_header_map.get(i, None)
                if header is not None:
                    header.lineAddBlock(b)
                else:
                    self.index_header_map[i] = HeaderUnit(i, b)

        multiLineBlock = set()
        for index in self.sortByMultiLine(self.index_header_map):
            blocks = self.index_header_map[index].blockbox
            if len(blocks) > 1:
                for b in blocks:
                    multiLineBlock.add(b)
            else:
                if blocks[0] in multiLineBlock:
                    self.index_header_map.pop(index)

        return True


    def sortByMultiLine(self, column_block_map):
        # 把跨多行的header排到前面去
        index = []
        tl = []
        for key in column_block_map.keys():
            tl.append([key, len(column_block_map[key].blockbox)])
        tl = sorted(tl, key=lambda x: x[1], reverse=True)
        for t in tl:
            index.append(t[0])
        return index


    def add(self, line):
        # if line.pageNum == 18 and line.text=='（一）以后不能重分类进损益的其他综合收益':
        if line.pageNum == 76:
            print line.text
        # 有线的表直接处理
        if self.linetableid is not None and line.blockbox[0].linetableid is not None:
            isHaveValueColumn = self.checkLine(line)
            if not isHaveValueColumn and len(self.body) == 0:
                self.addToHeader(line)
            else:
                self.body.append(line)
            return len(self.body)
            # if line.blockbox[0].linetableid is not None:
            #     if self.checkLine(line):  # 值是否合法,合法直接加到body中
            #         self.body.append(line)
            #         return len(self.body)
            #     elif len(self.body) == 0: # 值不合法且之前没找到正文，line加到header中
            #         self.addToHeader(line)
            #         return len(self.body)
            #     elif line.pageNum!=self.body[-1].pageNum or (len(self.body_buffer)!=0 and line.pageNum!=self.body_buffer[-1].pageNum):   # 值不合法且之前找到正文，且跨页。直接去掉不要
            #         return len(self.body)
            #     else: # 值不合法且之前找到正文，且linetableid一致。可能是数字判断错了，直接加到body中
            #         self.body.append(line)
            #         return len(self.body)
            # else:
            #     self.setTableFinish()
            #     return 'reject'
        elif self.linetableid is not None and line.blockbox[0].linetableid is None:
            self.setTableFinish()
            return 'reject'

        index_header_map_copy = copy.deepcopy(self.index_header_map)

        try:
            # gen line Index。 列宽度随着body的内容变化。 最后一列不新增列
            self.genNewColumnLineInex(line)
        except Exception:
            self.setTableFinish()
            self.index_header_map = index_header_map_copy
            return 'reject'

        # 多种情况判断：有有效列，有效列中非法，body未开始； 无有效列； 有有效列，有效列中的值合法； 有有效列，有效列中非法，boay已开始
        checkResult = self.haveValueColumn(line)
        if checkResult:
            if self.valueColumnLegal(line, checkResult):
                self.body_buffer.append(line)
                self.body = self.body + self.body_buffer
                self.body_buffer = []
            elif len(self.body) == 0:
                result = self.addLineToHeader(line, index_header_map_copy)
                if not result:
                    self.index_header_map = index_header_map_copy
                    return 'reject'
            else:
                self.setTableFinish()
                self.index_header_map = index_header_map_copy
                return 'reject'
        elif len(self.body) == 0:
            # 判断line的第一个block是不是科目，不是的话不加到body中
            pureBlock0 = subject_match_tools.getPureSbuectText(line.blockbox[0].text)
            if pureBlock0 in standerSubjectLib.subjects or len(self.body_buffer) > 0:
                self.body_buffer.append(line)
            else:
                result = self.addLineToHeader(line, index_header_map_copy)
                if not result:
                    self.index_header_map = index_header_map_copy
                    return 'reject'
        else:
            self.body_buffer.append(line)

        return len(self.body)

    def addLineToHeader(self, line, index_header_map_copy):
        self.headerLineBox.append(line)
        if line.pageNum == 68:
            pass
        # re divide column
        curHeaderBox = []
        for l in self.headerLineBox:
            for block in l.blockbox:
                curHeaderBox.append(block)

        referLine = column_divide_tools.culateColumnIndex(curHeaderBox)

        if len(referLine) < 2:
            return False

        # column converge
        # index_header_map_new = {}
        # for b in curHeaderBox + line.blockbox:
        #     for index in b.columnIndexs:
        #         if (index + 1) * 1000 in index_header_map_new:
        #             self.mergeUnit(index_header_map_new[(index + 1) * 1000], b)
        #         else:
        #             index_header_map_new[(index + 1) * 1000] = HeaderUnit((index + 1) * 1000, b)
        try:
            self.index_header_map = header_match_tools.fittingHeaderWidth(curHeaderBox)
        except Exception:
            return False
        return True


    # direction, , font, word_gap, lineIndex, type,
    def mergeUnit(self, header, addOne):
        header.text = header.text + ' ' + addOne.text
        header.x0 = (addOne.x0 if addOne.x0 < header.x0 else header.x0)
        header.y0 = (addOne.y0 if addOne.y0 < header.y0 else header.y0)
        header.x1 = (addOne.x1 if addOne.x1 > header.x1 else header.x1)
        header.y1 = (addOne.y1 if addOne.y1 > header.y1 else header.y1)
        header.identity = header.identity if header.identity != '' else addOne.identity
        if hasattr(addOne, 'lineIndex'):
            header.lineIndexs.append(addOne.lineIndex)

    def haveValueColumn(self, line):
        min = 999999
        max = 0
        for header in self.index_header_map.values():
            if header.identity != 'value':
                continue
            min = min if min < header.x0 else header.x0
            max = max if max > header.x1 else header.x1
        result =  not (line.x0 > max or line.x1 < min) #是否重叠
        if result:
            return [min, max]
        else:
            return False

    def isValueColumnPattern(self, line, block):
        if block.type not in ['text-sentence', 'text-phrase']:
            return True

        # if '，' in block.text:
        #     print str(line.pageNum) + '  ' + str(line.text)

        text = re.sub('人民币|元|\.|\d|\s|\(|\)|（|）|，|,', '', block.text)
        if text == '':
            return True
        return False


    def valueColumnLegal(self, line, minAndMax):
        # 值列是否合法在这里进行判断，把合法的值列的模式记录下来
        for b in line.blockbox:
            if b.x1 > minAndMax[0] and not self.isValueColumnPattern(line,b):
                return False
        return True

    def overlap(self, first, second):
        if not (first[0] > second[1] or first[1] < second[0]):
            firstRange = first[1] - first[0]
            box = sorted(first + second)
            return (box[2] - box[1])/firstRange
        else:
            return 0

    def genNewColumnLineInex(self, line):
        # if line.pageNum == 33 and '其中：归属于母公司股东的净利润#_#(11,851,600.88)#_#(10,508,817.08)#_#1,892,615.03#_#1,492,548.71' in line.text:
        #     print line.text
        for block in line.blockbox:
            index_keys = sorted(self.index_header_map.keys())
            for i, index in enumerate(index_keys):
                header = self.index_header_map[index]
                if not (header.x0 > block.x1 or header.x1 < block.x0):  #重叠。 调整header宽度
                    # 在列值超过1的情况下， 引入重叠度。
                    # 检查和后面的重叠度大还是与现在的header重叠度大
                    if len(line.blockbox) > 1:
                        # 有下一列
                        if i+1 < len(index_keys):
                            nextHeader = self.index_header_map[index_keys[i + 1]]
                            curOverlap = self.overlap([header.x0, header.x1], [block.x0, block.x1])
                            nextOverlap = self.overlap([nextHeader.x0, nextHeader.x1], [block.x0, block.x1])

                            # if nextOverlap == 1 and header.text != '' and nextHeader.text != '':
                            #     raise Exception('USELESS LINE')

                            # 一旦重叠的列中存在新增列，就把这两列合并
                            if nextOverlap != 0 and curOverlap !=0 and (header.text=='' or nextHeader.text == ''):
                                # 去掉新增列，合并header. next合并到当前，去掉next，修正以划分的body
                                self.mergeUnit(header, nextHeader)
                                modifyColumnIndex = nextHeader.columnIndex
                                for l in self.body + self.body_buffer:
                                    for b in l.blockbox:
                                        if b.columnIndex == nextHeader.columnIndex:
                                            b.columnIndex = header.columnIndex
                                            b.identity = header.identity
                                block.columnIndex = header.columnIndex
                                block.identity = header.identity
                                self.index_header_map.pop(index_keys[i + 1])
                            elif nextOverlap > curOverlap:
                                # 和当前列也有足够多的重叠，归属于当前列，列宽不做任何调整
                                if curOverlap > 0.75:
                                    block.columnIndex = index
                                    block.identity = header.identity
                                else:
                                    # block归到下一列，两列header宽度都要调整
                                    block.columnIndex = index_keys[i + 1]
                                    block.identity = nextHeader.identity
                                    nextHeader.x0 = nextHeader.x0 if nextHeader.x0 < block.x0 else block.x0
                                    nextHeader.x1 = nextHeader.x1 if nextHeader.x1 > block.x1 else block.x1
                                    header.x1 = header.x1 if header.x1 < block.x0 else block.x0-1 #隔开一个像素
                            elif nextOverlap!= 0: # 和下一列还是有重叠，block归到当前列，两列header都要调整宽度
                                block.columnIndex = index
                                block.identity = header.identity
                                header.x0 = header.x0 if header.x0 < block.x0 else block.x0
                                header.x1 = header.x1 if header.x1 > block.x1 else block.x1
                                nextHeader.x0 = nextHeader.x0 if nextHeader.x0 > block.x1 else block.x1 + 1 # 隔开一个像素
                            else:   # 和下一列不重叠，block归到当前列，当前header调整
                                block.columnIndex = index
                                block.identity = header.identity
                                header.x0 = header.x0 if header.x0 < block.x0 else block.x0
                                header.x1 = header.x1 if header.x1 > block.x1 else block.x1
                        #无下一列
                        else:
                            block.columnIndex = index
                            block.identity = header.identity
                            #调整列宽度
                            header.x0 = header.x0 if header.x0 < block.x0 else block.x0
                            header.x1 = header.x1 if header.x1 > block.x1 else block.x1
                    else:
                        block.columnIndex = index
                        block.identity = header.identity
                    break
                elif header.x0 > block.x1: #在header左边， 新增一列
                    newIndex = (0 + index)/2 if i == 0 else (index_keys[i-1] + index)/2
                    self.index_header_map[newIndex] = HeaderUnit(newIndex, block, True)
                    block.columnIndex = newIndex
                    block.identity = ''
                    break
                elif i == len(index_keys)-1:  # 在header的最后一列的右边，属于最后一列，并调整header宽度
                    # newIndex = index + 1000
                    # self.index_header_map[newIndex] = HeaderUnit(block.lineIndex, newIndex, '', block.x0, block.y0, block.x1, block.y1, block.fontsize)

                    block.columnIndex = index
                    block.identity = header.identity
                    # 调整header宽度
                    header.x0 = header.x0 if header.x0<block.x0 else block.x0
                    header.x1 = header.x1 if header.x1>block.x1 else block.x1

                    # block.columnIndex = newIndex
                    # block.identity = ''
                    break


    # 列index归一化
    def setTableFinish(self):
        self.bodyFoundFinish = True
        # 检查bodybuffer， 去掉宽度过宽的



