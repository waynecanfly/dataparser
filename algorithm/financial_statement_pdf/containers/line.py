# -*- coding: UTF-8 -*-
import re


class Line:
    def __init__(self, block, total_lineindex):
        self.total_lineindex = total_lineindex
        self.pageNum = block.pageNum
        self.direction = block.direction
        self.lineIndex = block.lineIndex

        self.max_fontsize = block.fontsize
        self.text = block.text
        self.x0 = block.x0
        self.y0 = block.y0
        self.x1 = block.x1
        self.y1 = block.y1

        self.top_gap = -1
        self.bottom_gap = -1
        self.left_gap = -1
        self.right_gap = -1


        self.block_gap = -1  # has not be use in earlier stage
        self.blockbox = [block]

        self.linetableid = block.linetableid
        self.is_useful = True

        self.line_index_range = set(block.lineLineIndex) if block.linetableid is not None else {block.lineIndex}

        block.total_lineindex = total_lineindex

    def add(self, block):
        this_line_range = set(block.lineLineIndex) if block.linetableid is not None else {block.lineIndex}
        j1 = block.pageNum == self.pageNum
        j2 = block.direction == self.direction
        j3 = len(this_line_range & self.line_index_range)>0
        j4 = self.linetableid == block.linetableid
        if j1 and j2 and j3 and j4:
            self.blockbox.append(block)
            self.max_fontsize = self.max_fontsize if self.max_fontsize > block.fontsize else block.fontsize
            self.text = str(self.text + '#_#' + block.text).strip()
            self.x0 = (block.x0 if block.x0 < self.x0 else self.x0)
            self.y0 = (block.y0 if block.y0 < self.y0 else self.y0)
            self.x1 = (block.x1 if block.x1 > self.x1 else self.x1)
            self.y1 = (block.y1 if block.y1 > self.y1 else self.y1)
            self.line_index_range = self.line_index_range | this_line_range
            block.total_lineindex = self.total_lineindex
            return 'accept'
        else:
            # 由于一行中原始lineindex不一定一样，所以当和成一行之后要对blockbox进行排序, text也要按正确顺序重新生成
            self.blockbox.sort(key=lambda x: x.x0)
            textlist = []
            for b in self.blockbox:
                textlist.append(b.text)
            self.text = '#_#'.join(textlist)
            return 'reject'
