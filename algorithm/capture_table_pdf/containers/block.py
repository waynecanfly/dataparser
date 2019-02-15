# -*- coding: UTF-8 -*-
import re


class Block:
    #
    def __init__(self, pageNum, text, x0, y0, x1, y1, direction, fontsize,font, word_gap, lineIndex, type, linetableid, lineLineIndex, lineColumnIndex, identity=''):
        self.pageNum = int(pageNum)
        self.text = text
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.direction = int(direction)
        self.fontsize = float(fontsize)
        self.word_gap = float(word_gap)
        self.lineIndex = int(lineIndex)
        self.type = re.sub('[\n]', '', type)
        self.top_gap = float(-1)
        self.bottom_gap = float(-1)
        self.left_gap = float(-1)
        self.right_gap = float(-1)
        self.font = font
        self.identity = identity

        self.linetableid = linetableid if linetableid != 'None' else None
        self.lineLineIndex = [int(x) for x in lineLineIndex.split('|')] if lineLineIndex != '' else ''
        self.lineColumnIndex = [int(x) for x in lineColumnIndex.split('|')] if lineColumnIndex != '' else ''