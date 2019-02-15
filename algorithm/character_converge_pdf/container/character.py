# -*- coding: UTF-8 -*-
import re

from algorithm.character_converge_pdf import zh_hant_map

class Character:
    def __init__(self, pageNum, text, x0, y0, x1, y1, direction,font, size, character_width, height, orderid=0,lineIndex=-1, columnIndex=-1):
        self.pageNum = int(pageNum)
        self.text = self.processIllegalChar(text)
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.x1 = float(x1)
        self.y1 = float(y1)
        # temp = int(float(direction))
        self.direction = int(direction)  # 1 normal 0 other
        self.font = font
        self.size = float(size)
        self.character_width = float(character_width)
        self.height = float(height)
        self.orderid = int(orderid)
        self.lineIndex = int(lineIndex)
        self.columnIndex = int(columnIndex)

    def processIllegalChar(self, text):
        text = re.sub('#\|#', ',', re.sub('[\n]', '', text)).decode('utf-8')
        text = text.strip()
        text = zh_hant_map.zh_hant_map.get(text, text)
        illegalMap = {
            u'⑻': '00',
            u'，': ','
        }
        text = illegalMap.get(text, text)
        return unicode(text)