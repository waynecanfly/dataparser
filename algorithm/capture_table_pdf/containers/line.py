# -*- coding: UTF-8 -*-
import re


class Line:
    def __init__(self, block):
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

    def add(self, block):
        if block.pageNum == self.pageNum and block.direction == self.direction and block.lineIndex == self.lineIndex:
            self.blockbox.append(block)
            self.max_fontsize = self.max_fontsize if self.max_fontsize > block.fontsize else block.fontsize
            self.text = str(self.text + '#_#' + block.text).strip()
            self.x0 = (block.x0 if block.x0 < self.x0 else self.x0)
            self.y0 = (block.y0 if block.y0 < self.y0 else self.y0)
            self.x1 = (block.x1 if block.x1 > self.x1 else self.x1)
            self.y1 = (block.y1 if block.y1 > self.y1 else self.y1)
            return 'accept'
        else:
            return 'reject'
