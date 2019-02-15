# -*- coding: UTF-8 -*-
import re


class Line:
    def __init__(self, pageNum, lineIndex, b_df, index):
        self.pageNum = pageNum
        self.lineIndex = lineIndex
        self.b_df = b_df
        self.index = index

        self.direction = b_df.direction.max()
        self.max_fontsize = b_df.size.max()
        self.text = list(b_df.text)
        self.x0 = b_df.x0.min()
        self.y0 = b_df.y0.min()
        self.x1 = b_df.x1.max()
        self.y1 = b_df.y1.max()
        self.is_useful = b_df.isUseful.max()