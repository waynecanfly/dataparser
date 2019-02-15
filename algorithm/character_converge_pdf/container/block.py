# -*- coding: UTF-8 -*-

from algorithm.character_converge_pdf import judge_text_type
from algorithm.common import tools


class Block:
    def __init__(self, initData, country='', otherPara = ''):
        if isinstance(initData, list):
            fWord = initData[0]
            tableid, v_order_value_map, h_order_value_map, beginLine  = otherPara

            self.x0 = v_order_value_map[fWord.v_order[0]]
            self.x1 = v_order_value_map[fWord.v_order[1]]
            self.y1 = h_order_value_map[fWord.h_order[0]]
            self.y0 = h_order_value_map[fWord.h_order[1]]

            self.pageNum = fWord.pageNum
            self.direction = fWord.direction
            self.size = fWord.size
            self.font = fWord.font
            self.word_gap = -1  # has not be use in earlier stage

            self.lineIndex = fWord.h_order[0] + beginLine

            self.text = ''
            for w in initData:
                self.text = self.text + w.text
            self.type = judge_text_type.judge(self.text)  # type : NumOrder, phrase, sentence,value ...

            self.lineTableId = str(self.pageNum) + '_' + str(tableid)
            self.talbeLineIndexs = [x + beginLine for x in range(fWord.h_order[0],fWord.h_order[1])]
            self.talbeColumnIndexs = [x for x in range(fWord.v_order[0],fWord.v_order[1])]

            self.wordBox = initData
            self.status = 'close'
        else:
            self.pageNum = initData.pageNum
            self.direction = initData.direction
            self.size = initData.size
            self.font = initData.font
            self.word_gap = -1  # has not be use in earlier stage

            self.lineIndex = initData.lineIndex

            self.text = initData.text.strip()
            self.type = judge_text_type.judge(self.text)  # type : NumOrder, phrase, sentence,value ...
            self.x0 = initData.x0
            self.y0 = initData.y0
            self.x1 = initData.x1
            self.y1 = initData.y1
            self.wordBox = [initData]
            self.status = 'open'
            # 中文0.5，英文以后再调。其实可以把这个值限定得很严格，避免掉文本块错误的粘在一起的情况，然后落单的那些再通过。库里的记录再做汇聚
            self.CONVERGE_THR = 0.8

            if self.type == 'NumOrder':
                self.status = 'close'

            self.lineTableId = None
            self.talbeLineIndexs = []
            self.talbeColumnIndexs = []

    def isSameFontsize(self, word):
        if self.text == '`':
            self.size = word.size
            return True
        elif word.text == '`':
            return True
        else:
            return float('%.2f' % float(self.size)) == float('%.2f' % float(word.size))

    def addNewWord(self,word):
        self.wordBox.append(word)
        self.text = str(self.text + word.text).strip()
        self.x0 = (word.x0 if word.x0 < self.x0 else self.x0)
        self.y0 = (word.y0 if word.y0 < self.y0 else self.y0)
        self.x1 = (word.x1 if word.x1 > self.x1 else self.x1)
        self.y1 = (word.y1 if word.y1 > self.y1 else self.y1)


    def add(self, word):
        # if word.orderid > 24145:
        #     print word.text + ' ' + str(word.orderid)

        if self.pageNum == word.pageNum and self.direction == word.direction and self.lineIndex == word.lineIndex:
            wordGap = word.x0 - self.x1
            thr1 = self.wordBox[-1].character_width * self.CONVERGE_THR
            # thr2 = self.wordBox[-1].character_width * 1.75

            if not (self.x0 > word.x1 or self.x1 < word.x0):
                self.wordBox.append(word)
                self.text = str(self.text + word.text).strip()
                self.x0 = (word.x0 if word.x0 < self.x0 else self.x0)
                self.y0 = (word.y0 if word.y0 < self.y0 else self.y0)
                self.x1 = (word.x1 if word.x1 > self.x1 else self.x1)
                self.y1 = (word.y1 if word.y1 > self.y1 else self.y1)
                return 'accept'
            # elif wordGap <= thr1 or (wordGap < thr2 and self.isSameFontsize(word)):
            elif wordGap <= thr1 or tools.isOneWord(word.x0, self.wordBox[-1].x1, True):
                self.wordBox.append(word)
                self.text = str(self.text + word.text).strip()
                self.x0 = (word.x0 if word.x0 < self.x0 else self.x0)
                self.y0 = (word.y0 if word.y0 < self.y0 else self.y0)
                self.x1 = (word.x1 if word.x1 > self.x1 else self.x1)
                self.y1 = (word.y1 if word.y1 > self.y1 else self.y1)
                return 'accept'
            else:
                self.status = 'close'
                self.type = judge_text_type.judge(self.text)
                return 'reject'
        else:
            self.status = 'close'
            self.type = judge_text_type.judge(self.text)
            return 'reject'
