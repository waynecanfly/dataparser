# -*- coding: UTF-8 -*-
import re

class Word:
    def __init__(self, pageNum, text, x0, y0, x1, y1, direction, size, character_width, font, type='', lineIndex=-1, columnIndex=-1):
        self.pageNum = int(pageNum)
        self.text = re.sub('[\n]', '', text)
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.direction = int(direction)
        self.size = float(size)
        self.character_width = float(character_width)
        self.type = str(type)  #type : adj adv ...
        self.lineIndex = int(lineIndex)
        self.columnIndex = int(columnIndex)
        self.font = font


    def judgeType(self):
        pass
        # aim = re.sub('[\\)\s]', '', self.text)
        # if self.columnIndex == 0:
        # #hava .
        #     rome_re = re.compile(r'^[ivxIVX]{1,5}[\.]?$')
        #     digit_re = re.compile(r'^[0-9]{1,2}[\.]$')
        #     letter_re = re.compile(r'^[a-zA-Z][\.]$')
        #     #hava ()
        #     rome_re_2 = re.compile(r'^\(?[ivxIVX]{1,5}\)$')
        #     digit_re_2 = re.compile(r'^\(?[0-9]{1,2}\)$')
        #     letter_re_2 = re.compile(r'^\(?[a-zA-Z]\)$')
        #     #begin with 0
        #     digit_re_3 = re.compile(r'^0[1-9]$')
        #
        #     if rome_re.match(aim) or digit_re.match(aim) or letter_re.match(aim):
        #         self.type = 'NumOrder'
        #     elif rome_re_2.match(self.text) or digit_re_2.match(self.text) or letter_re_2.match(self.text) or digit_re_3.match(self.text):
        #         self.type = 'NumOrder'



