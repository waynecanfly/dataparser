# -*- coding: UTF-8 -*-
import re

from algorithm.common import tools
from algorithm.common_tools_pdf import column_divide_tools, header_match_tools


class Header:
    def __init__(self,lines, pageNums, linetableid, header_columns, header_range):
        self.lines = lines
        self.pageNums = pageNums
        self.linetableid = linetableid
        self.header_columns = header_columns
        self.header_range = header_range

        self.value_min = 999
        self.value_max = 0

        # 初始化
        # 去掉表头合并错误的列
        self.del_wrong_headercolumn()

        self.calculateMinAndMax()

        self.header_range_uncertainty = False


    def del_wrong_headercolumn(self):
        # 先简单实现
        indexs = self.header_columns.keys()
        exist_box = {}
        for i in indexs:
            blocks = self.header_columns[i].blockbox
            if len(blocks) == 1:
                continue
            lastone = blocks[-1]

            if lastone in exist_box.values():
                # 保留一个
                clash_i = None
                for n in exist_box.keys():
                    b = exist_box[n]
                    if lastone is b:
                        clash_i = n
                        break
                delete = self.delete_one(i, clash_i)
                self.header_columns.pop(delete)
                try:
                    exist_box.pop(delete)
                except:
                    pass
            exist_box[i] = lastone




    def delete_one(self, x, y):
        x_box = self.header_columns[x].blockbox
        y_box = self.header_columns[y].blockbox
        x_overlap = tools.overlapRate([x_box[-1].x0, x_box[-1].x1], [x_box[-2].x0, x_box[-2].x1])
        y_overlap = tools.overlapRate([y_box[-1].x0, y_box[-1].x1], [y_box[-2].x0, y_box[-2].x1])
        if x_overlap<y_overlap:
            return x
        else:
            return y

    def calculateMinAndMax(self):
        for header_unit in self.header_columns.values():
            if header_unit.identity not in ['value', 'placeholder']:
                continue
            self.value_min = self.value_min if self.value_min < header_unit.x0 else header_unit.x0
            self.value_max = self.value_max if self.value_max > header_unit.x1 else header_unit.x1
            
    def add(self, line):
        if self.linetableid is not None:
            self.add_with_line(line)
        else:
            self.add_without_line(line)
        self.calculateMinAndMax()

    
    def add_with_line(self, line):
        self.lines.append(line)
        self.pageNums.add(line.pageNum)
        self.header_range[1] = self.header_range[1] + 1

        for b in line.blockbox:
            for i in b.lineColumnIndex:
                header = self.header_columns.get(i, None)
                if header is not None:
                    header.lineAddBlock(b)
                else:
                    self.header_columns[i] = HeaderUnit(i, b)

        # 过滤掉只有一行并且该行有和其它行组成一个整体的表头列
        multiLineBlock = set()
        for index in self.sortByMultiLine(self.header_columns):
            blocks = self.header_columns[index].blockbox
            if len(blocks) > 1:
                for b in blocks:
                    multiLineBlock.add(b)
            else:
                if blocks[0] in multiLineBlock:
                    self.header_columns.pop(index)

        return True
    
    def add_without_line(self, line):
        self.lines.append(line)
        self.pageNums.add(line.pageNum)
        self.header_range[1] = self.header_range[1] + 1

        # re divide column
        curHeaderBox = []
        for l in self.lines:
            for block in l.blockbox:
                curHeaderBox.append(block)

        referLine = column_divide_tools.culateColumnIndex(curHeaderBox)

        if len(referLine) < 2:
            return False

        try:
            # 列分发及值列宽度重新计算
            self.header_columns = header_match_tools.fittingHeaderWidth(curHeaderBox)
        except Exception:
            return False

        # 从正文重新增一行到表头时，增加列identity修正
        indexs = sorted(self.header_columns.keys())
        firstHeader = self.header_columns[indexs[0]]
        if firstHeader.identity in ['value', 'index']:
            for i in indexs[1:]:
                if self.header_columns[i].identity == 'index':
                    firstHeader.identity = 'useless'
                    break

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

    def resetHeaderWidth(self,header, range):
        header.x0 = range[0]
        header.x1 = range[1]
        if header.identity == 'value':
            self.value_min = self.value_min if self.value_min < header.x0 else header.x0
            self.value_max = self.value_max if self.value_max > header.x1 else header.x1

class HeaderUnit:
    #
    def __init__(self, columnIndex, block, isEmptyHeader = False):
        if isEmptyHeader:
            self.blockbox = []
            self.lineIndexs = []
            self.columnIndex = columnIndex
            self.text = ''
            self.x0 = float(block.x0)
            self.y0 = float(block.y0)
            self.x1 = float(block.x1)
            self.y1 = float(block.y1)
            self.identity = ''
            self.extraInfo = ''
            self.fontsize = block.fontsize
        else:
            self.blockbox = [block]
            self.lineIndexs = [block.lineIndex]
            self.columnIndex = columnIndex
            self.text = block.text
            self.x0 = float(block.x0)
            self.y0 = float(block.y0)
            self.x1 = float(block.x1)
            self.y1 = float(block.y1)
            self.identity = block.identity
            self.extraInfo = ''
            self.fontsize = block.fontsize

        # 识别的信息点
        self.isConsolidated = -1
        self.currency = None
        self.measureunit = None
        #'actstandards': None, 'isadjust': 1
        self.actstandards = None
        self.isadjust = 1

    def addBlock(self, block):
        self.blockbox.append(block)
        self.lineIndexs.append(block.lineIndex)
        self.text = self.text + block.text
        self.x0 = self.x0 if self.x0 < block.x0 else block.x0
        self.y0 = self.y0 if self.y0 < block.y0 else block.y0
        self.x1 = self.x1 if self.x1 > block.x1 else block.x1
        self.y1 = self.y1 if self.y1 > block.y1 else block.y1

    def lineAddBlock(self, block):
        self.blockbox.append(block)
        self.lineIndexs.append(block.lineIndex)
        self.text = self.text + block.text
        self.x0 = self.x0 if self.x0 > block.x0 else block.x0
        self.y0 = self.y0 if self.y0 < block.y0 else block.y0
        self.x1 = self.x1 if self.x1 < block.x1 else block.x1
        self.y1 = self.y1 if self.y1 > block.y1 else block.y1
