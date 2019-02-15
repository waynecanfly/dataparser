# -*- coding: UTF-8 -*-
import copy
import re

from algorithm.capture_table_pdf.containers.headerUnit import HeaderUnit
from algorithm.common import tools
from algorithm.common_tools_pdf import standerSubjectLib, subject_match_tools, header_match_tools


class Table:
    # def __init__(self, lastpage, page, index_header_map, header_beginindex, headerLineBox, linetableid):
    def __init__(self, title_anchor, header, table_area, linebox_total, p_reportid):
        if title_anchor['title_pageNum'] == 6:
            pass

        # 总体资源
        self.linebox_total = linebox_total
        self.table_area = table_area

        # 表结构
        self.title = title_anchor   # unit: block
        self.title_area = self.get_title_area(table_area, header, linebox_total, title_anchor)
        self.header = header
        self.body = []  # unit: line
        self.body_buffer = []



        # 表基础信息
        self.reportid = p_reportid
        self.table_type = title_anchor['table_type']
        # if isinstance(header, str):
        #     print 'herehereherehereherehereherehereherehereherehereherehereherehereherehereherehere'
        # self.pageNum = {title_anchor['title_pageNum']} | header.pageNums
        self.pageNum = title_anchor['title_pageNum']
        self.table_page_ragne = {self.pageNum}
        self.linetableid = header.linetableid


        # 需要识别的信息点
        self.isConsolidated = -1
        self.fiscal_year = None
        self.season_type = None

        # 标志信息点
        self.body_end_line_index = self.header.header_range[1]

        # 确定表正文
        self.find_fs_body()

    def get_title_area(self, table_area, header, linebox_total, title_anchor):
        title_area = []
        # 首先先不要区域内的无用信息
        for line in table_area[0: header.header_range[0]]:
            if line.is_useful:
                title_area.append(line)

        # 获取title当页第一行（需要is_useful是false才行），加入到title_area中，因为通常那一行包含了财宝的年度和季度
        aim_area = linebox_total[0: title_anchor['index']]
        aim_area.reverse()
        for a in aim_area:
            if a.pageNum  == title_anchor['title_pageNum'] and a.lineIndex == 0:
                if not a.is_useful:
                    title_area = [a] + title_area
                break
        return title_area


    def recalulate_header_range(self):
        if self.linetableid is not None:
            for i, l in enumerate(self.table_area):
                if l.linetableid is not None:
                    self.header.header_range = [i, i]
                    break
        else:
            adjust = 0
            check_range = list(self.table_area[self.header.header_range[0]:self.header.header_range[1]])
            check_range.reverse()
            for c in check_range:
                checkstr = subject_match_tools.getPureSbuectText(c.blockbox[0].text)
                if checkstr in standerSubjectLib.subjects:
                    adjust += 1
            self.header.header_range[1] = self.header.header_range[1] - adjust


    def find_fs_body(self):
        #表头范围是否确定，不确定的话需要利用科目库进行确定
        if self.header.header_range_uncertainty:
            self.recalulate_header_range()

        #开始处理表正文
        if self.linetableid is not None:
            self.body_end_line_index = self.body_with_line()
            # 列号修正. 由于有些线有轻微的错位，所以现在默认的以左边的线作为columnidex并不严谨
            self.fitting_columnindex()
        else:
            self.body_end_line_index = self.body_without_line()

    def is_subject(self,line):
        check_text = subject_match_tools.getPureSbuectText(line.blockbox[0].text)
        min_header = self.header.header_columns[min(self.header.header_columns.keys())]
        if len(check_text)>0 and check_text in standerSubjectLib.subjects and line.x1 < min_header.x1:
            return True
        else:
            return False

    def is_title_range_line(self,line):
        def pure_test(text):
            text = re.sub(r"""\s|,|\||-|—|:|：|．|\*|\[|\]|\?|\.|\(|\)|/|#|&|'|\"|_|、|－|（|）|“|”|―|‖|~|，|！|¡|。|‛|‚|­|；|;|？|】|【|※|﹑|\^|〔|·|‐|‘|’|＂|＂|\+|–""", '', text)
            return text
        if line.pageNum == self.pageNum:
            return False
        line_pure_text = pure_test(line.text)
        for titlearea_line in self.table_area[0: self.header.header_range[0]]:
            pure = pure_test(titlearea_line.text)
            if line_pure_text == pure:
                return True
        return False

    def body_with_line(self):
        for i, line in enumerate(self.table_area[self.header.header_range[1]:]):
            # 如果页头尾无用的行，直接忽略
            if not line.is_useful or self.is_useless_line(line):
                continue

            # 该行在线表内，直接添加
            if line.linetableid is not None:
                valueColumnIegal = self.checkLine(line)

                # 若在值列范围内不合法，且表正文为空，该行添加到表头
                if not valueColumnIegal and len(self.body) == 0:
                    self.header.add(line)
                else:
                    self.body.append(line)
                    self.table_page_ragne.add(line.pageNum)
            elif self.is_subject(line):
                self.body.append(line)
                self.table_page_ragne.add(line.pageNum)
            # # 解决续表除了没有标题，其它的都有导致的表不全问题
            elif self.is_title_range_line(line):
                continue
            # 表结束
            else:
                return self.header.header_range[1] + i
        return self.header.header_range[1] + i + 1

    def is_body_header(self, line):
        for b in line.blockbox:
            header = self.header.header_columns.get(b.columnIndex,None)
            if header is not None and header.identity == 'value':
                if b.text in header.text:
                    return True
        return False

    def is_useless_line(self, line):
        use_less_box = ['项目', '续前表']
        text = re.sub('\s', '', line.blockbox[0].text)
        return text in use_less_box

    def body_without_line(self):
        # 这个函数的逻辑还是过于累赘，以后需要重构
        global i
        is_break = False
        for i, line in enumerate(self.table_area[self.header.header_range[1]:]):
            # 如果页头尾无用的行，直接忽略
            if not line.is_useful or self.is_useless_line(line):
                continue
            elif '权益变动表' in line.text:
                break
            index_header_map_copy = copy.deepcopy(self.header.header_columns)

            try:
                # gen line Index。 列宽度随着body的内容变化。 最后一列不新增列
                self.genNewColumnLineInex(line)
            except Exception:
                self.header.header_columns = index_header_map_copy
                is_break = True
                break

            # 多种情况判断：有有效列，有效列中非法，body未开始； 无有效列； 有有效列，有效列中的值合法； 有有效列，有效列中非法，boay已开始
            # 有值列
            if tools.overlapRate([line.x0, line.x1], [self.header.value_min, self.header.value_max]) > 0.1:
                # 判断是否为科目
                pure_line_text = subject_match_tools.getPureSbuectText(line.text)
                # print pure_line_text
                if pure_line_text in standerSubjectLib.subjects:
                    self.body_buffer.append(line)
                    self.body = self.body + self.body_buffer
                    self.body_buffer = []
                    self.table_page_ragne.add(line.pageNum)
                # 有值列，且值列合法
                elif self.valueColumnLegal(line):
                    self.body_buffer.append(line)
                    self.body = self.body + self.body_buffer
                    self.body_buffer = []
                    self.table_page_ragne.add(line.pageNum)
                # 有值列，且值列非法，并且正文为空, 该行添加到表头
                elif len(self.body) == 0:
                    result = self.header.add_without_line(line)
                    if not result:
                        self.header.header_columns = index_header_map_copy
                        is_break = True
                        break
                # 有值列，且值列非法，并且正文不为空，判断是否为表头
                elif self.is_body_header(line):
                    continue
                else:
                    self.header.header_columns = index_header_map_copy
                    is_break = True
                    break
            # 无值列，且表正文为空
            elif len(self.body) == 0:
                # 判断line的第一个block或者整一行是不是科目，是科目或者buffer已经有值，则看作是table body，加入到bodybuffer中； 否则加入到表头中
                pureBlock0 = subject_match_tools.getPureSbuectText(line.blockbox[0].text)
                pureLine = subject_match_tools.getPureSbuectText(line.text)
                if pureLine in standerSubjectLib.subjects or pureBlock0 in standerSubjectLib.subjects or len(self.body_buffer) > 0:
                    self.body_buffer.append(line)
                else:
                    result = self.header.add_without_line(line)
                    if not result:
                        self.index_header_map = index_header_map_copy
                        is_break = True
                        break
            # 无值列，且body不为空， 暂时放到bodybuffer中
            else:
                self.body_buffer.append(line)
        return self.header.header_range[1] + (i  if is_break else i + 1)
        # return self.header.header_range[1] + (i  if is_break else i + 1) - len(self.body_buffer)


    def checkLine(self, line):
        for b in line.blockbox:
            b.columnIndexs = b.lineColumnIndex
            b.columnIndex = b.columnIndexs[0]
            for i in b.columnIndexs:
                try:
                    header = self.header.header_columns[i]
                except:
                    continue
                if header.identity == 'value' and b.type not in ('digit', 'placeholder', 'currency'):
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

    def isValueColumnPattern(self, line, block):
        if block.type not in ['text-sentence', 'text-phrase']:
            return True

        text = re.sub('人民币|元|分|\.|\d|\s|\(|\)|（|）|，|,', '', block.text)
        if text == '' and (len(self.body)!=0 or len(self.body_buffer)!=0):
            return True
        return False


    def valueColumnLegal(self, line):
        # 值列是否合法在这里进行判断，把合法的值列的模式记录下来
        value_column = [x for x in self.header.header_columns.values() if x.identity == 'value']
        for b in line.blockbox:
            for v in value_column:
                if tools.overlapRate([b.x0, b.x1], [v.x0, v.x1]) > 0.15 and not self.isValueColumnPattern(line,b):
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
            index_keys = sorted(self.header.header_columns.keys())
            for i, index in enumerate(index_keys):
                header = self.header.header_columns[index]
                if not (header.x0 > block.x1 or header.x1 < block.x0):  #重叠。 调整header宽度
                    # 在列值超过1的情况下， 引入重叠度。
                    # 检查和后面的重叠度大还是与现在的header重叠度大
                    if len(line.blockbox) > 1:
                        # 有下一列
                        if i+1 < len(index_keys):
                            nextHeader = self.header.header_columns[index_keys[i + 1]]
                            curOverlap = self.overlap([header.x0, header.x1], [block.x0, block.x1])
                            nextOverlap = self.overlap([nextHeader.x0, nextHeader.x1], [block.x0, block.x1])

                            # if nextOverlap == 1 and header.text != '' and nextHeader.text != '':
                            #     raise Exception('USELESS LINE')

                            # 一旦重叠的列中存在新增列，就把这两列合并
                            if nextOverlap != 0 and curOverlap !=0 and (header.text=='' or nextHeader.text == ''):
                                # 去掉新增列，合并header. next合并到当前，去掉next，修正以划分的body
                                # self.mergeUnit(header, nextHeader)
                                # for l in self.body + self.body_buffer:
                                #     for b in l.blockbox:
                                #         if b.columnIndex == nextHeader.columnIndex:
                                #             b.columnIndex = header.columnIndex
                                #             b.identity = header.identity
                                block.columnIndex = header.columnIndex
                                block.identity = header.identity
                                # self.header.header_columns.pop(index_keys[i + 1])
                            elif nextOverlap > curOverlap:
                                # 和当前列也有足够多的重叠，归属于当前列，列宽不做任何调整.
                                if curOverlap > 0.75 or abs(header.x1-block.x0) > abs(block.x1-nextHeader.x0):
                                    block.columnIndex = index
                                    block.identity = header.identity
                                else:
                                    # block归到下一列，两列header宽度都要调整
                                    block.columnIndex = index_keys[i + 1]
                                    block.identity = nextHeader.identity

                                    nextHeader_x0 = nextHeader.x0 if nextHeader.x0 < block.x0 else block.x0
                                    nextHeader_x1 = nextHeader.x1 if nextHeader.x1 > block.x1 else block.x1
                                    self.header.resetHeaderWidth(nextHeader,[nextHeader_x0, nextHeader_x1])
                                    header_x1 = header.x1 if header.x1 < block.x0 else block.x0-1 #隔开一个像素
                                    self.header.resetHeaderWidth(header, [header.x0, header_x1])

                            elif nextOverlap!= 0: # 和下一列还是有重叠，block归到当前列，两列header都要调整宽度
                                block.columnIndex = index
                                block.identity = header.identity

                                header_x0 = header.x0 if header.x0 < block.x0 else block.x0
                                header_x1 = header.x1 if header.x1 > block.x1 else block.x1
                                self.header.resetHeaderWidth(header, [header_x0, header_x1])
                                nextHeader_x0 = nextHeader.x0 if nextHeader.x0 > block.x1 else block.x1 + 1 # 隔开一个像素
                                self.header.resetHeaderWidth(nextHeader, [nextHeader_x0, nextHeader.x1])
                                if nextHeader.x1 < nextHeader.x0:
                                    raise Exception('HEADER_FITTING_ERROR')
                            else:   # 和下一列不重叠，block归到当前列，当前header调整
                                block.columnIndex = index
                                block.identity = header.identity
                                header_x0 = header.x0 if header.x0 < block.x0 else block.x0
                                header_x1 = header.x1 if header.x1 > block.x1 else block.x1
                                self.header.resetHeaderWidth(header, [header_x0, header_x1])
                        #无下一列
                        else:
                            block.columnIndex = index
                            block.identity = header.identity
                            #调整列宽度
                            header_x0 = header.x0 if header.x0 < block.x0 else block.x0
                            header_x1 = header.x1 if header.x1 > block.x1 else block.x1
                            self.header.resetHeaderWidth(header, [header_x0, header_x1])
                    else:
                        block.columnIndex = index
                        block.identity = header.identity
                    break
                elif header.x0 > block.x1: #在header左边， 新增一列
                    newIndex = (0 + index)/2 if i == 0 else (index_keys[i-1] + index)/2
                    self.header.header_columns[newIndex] = HeaderUnit(newIndex, block, True)
                    block.columnIndex = newIndex
                    block.identity = ''
                    break
                elif i == len(index_keys)-1:  # 在header的最后一列的右边，属于最后一列，并调整header宽度

                    block.columnIndex = index
                    block.identity = header.identity
                    # 调整header宽度
                    header_x0 = header.x0 if header.x0<block.x0 else block.x0
                    header_x1 = header.x1 if header.x1>block.x1 else block.x1
                    self.header.resetHeaderWidth(header, [header_x0, header_x1])
                    break


    # body 中的一个block只能对应一个header，当一个block对应多个header时，取重叠率最高那个
    def fitting_columnindex(self):
        for l in self.body:
            for b in l.blockbox:
                overlapMap = {}
                for k in self.header.header_columns.keys():
                    h = self.header.header_columns[k]
                    overlapMap[k] = tools.overlapRate([b.x0, b.x1], [h.x0, h.x1])
                maxKey = max(overlapMap, key=overlapMap.get)
                if max(overlapMap.values()) == 0:
                    continue
                b.columnIndex = maxKey



