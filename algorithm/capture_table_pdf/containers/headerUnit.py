# -*- coding: UTF-8 -*-
import re


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
