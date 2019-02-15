# -*- coding: UTF-8 -*-

class LineTable:
    def __init__(self, pageNum, id, v_segment_map, h_segment_map):
        self.pageNum = int(pageNum)
        self.id = id

        self.v_segment_map = v_segment_map
        self.h_segment_map = h_segment_map

        self.left = None
        self.right = None
        self.bottom = None
        self.top = None

        try:
            self.selfInit()
        except:
            pass

    def selfInit(self):
        xs = set()
        ys = set()
        for key in self.h_segment_map:
            ys.add(key)
            for seg in self.h_segment_map[key]:
                xs = xs | set(seg)
        for key in self.v_segment_map:
            xs.add(key)
            for seg in self.v_segment_map[key]:
                ys = ys | set(seg)

        # # 计算边框
        xs = sorted(list(xs))
        self.left = xs[0]
        self.right = xs[-1]
        ys = sorted(list(ys))
        self.bottom = ys[0]
        self.top = ys[-1]
        #
        # self.mergeLineValue(v_box + h_box, v_mergeMap, h_mergeMap)
        #
        # # 线补充，表四周边框要有线


        if abs(self.left - min(self.v_segment_map.keys())) < 5:
            self.v_segment_map.pop(min(self.v_segment_map.keys()))
        self.v_segment_map[self.left] = [[self.bottom, self.top]]

        if abs(self.right - max(self.v_segment_map.keys())) < 5:
            self.v_segment_map.pop(max(self.v_segment_map.keys()))
        self.v_segment_map[self.right] = [[self.bottom, self.top]]

        if abs(self.bottom - min(self.h_segment_map.keys())) < 5:
            self.h_segment_map.pop(min(self.h_segment_map.keys()))
        self.h_segment_map[self.bottom] = [[self.left, self.right]]

        if abs(self.top - max(self.h_segment_map.keys())) < 5:
            self.h_segment_map.pop(max(self.h_segment_map.keys()))
        self.h_segment_map[self.top] = [[self.left, self.right]]