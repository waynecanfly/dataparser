# -*- coding: UTF-8 -*-


class Line:
    def __init__(self, pageNum, x0, y0, x1, y1, direction=-1):
        self.pageNum = int(pageNum)
        self.x0 = float(x0)
        self.y0 = float(y0)
        self.x1 = float(x1)
        self.y1 = float(y1)
        self.direction = int(direction) # 0横线  1 竖线

