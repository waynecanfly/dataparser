# -*- coding: UTF-8 -*-

class Page:
    def __init__(self, line):
        self.pageNum = line.pageNum
        self.directiontype = [line.direction]  #

        # border not distinguish direction
        self.top_border = line.y0
        self.bottom_border = line.y1
        self.left_border = line.x0
        self.right_border = line.x1

        self.linebox = [line]


    def add(self, line):
        if line.pageNum == self.pageNum :
            self.linebox.append(line)

            self.top_border = line.y1 if line.y1 >  self.top_border else self.top_border
            self.bottom_border = line.y0 if line.y0 <  self.bottom_border else self.bottom_border
            self.left_border = line.x0 if line.x0 <  self.left_border else self.left_border
            self.right_border = line.x1 if line.x1 >  self.right_border else self.right_border

            if line.direction not in self.directiontype:
                self.directiontype.append(line.direction)

            return 'accept'
        else:
            return 'reject'