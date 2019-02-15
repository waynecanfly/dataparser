# -*- coding:utf-8 -*-
from algorithm.character_converge_structure.gen_line_table.gen_line_table_tools import genLineSegment


class PageSeg:
    def __init__(self, pageNum, linebox):
        if pageNum==1:
            pass
        self.pageNum = int(pageNum)
        self.linebox = linebox

        self.v_seg_map = {}
        self.h_seg_map = {}

        self.init()

    def init(self):
        v_line_map = {}
        h_line_map = {}
        # setp 1： 获取所有垂直线，并获取相应的起始点
        for l in self.linebox:
            if l.direction == 1:
                if l.x0 not in v_line_map:
                    v_line_map[l.x0] = [l]
                else:
                    v_line_map[l.x0].append(l)
            else:
                if l.y0 not in h_line_map:
                    h_line_map[l.y0] = [l]
                else:
                    h_line_map[l.y0].append(l)

        # step 2 : 拟合接近的线
        v_line_map = self.merge(v_line_map)
        h_line_map = self.merge(h_line_map)


        # step 3 : 生成线段
        for key in v_line_map.keys():
            seg = genLineSegment(v_line_map[key], 1)
            seg = [s for s in seg if abs(s[1] - s[0]) > 3]
            if seg:
                self.v_seg_map[key] = seg
        for key in h_line_map.keys():
            seg = genLineSegment(h_line_map[key], 0)
            seg = [s for s in seg if abs(s[1]-s[0])>5]
            if seg:
                self.h_seg_map[key] = seg

        # 去掉过于贴边的线段
        self.get_rid_of_useless(self.v_seg_map)
        self.get_rid_of_useless(self.h_seg_map)

    def get_rid_of_useless(self, box):
        key_box = box.keys()
        for key in key_box:
            if key <=3:
                box.pop(key)
        return box

    def merge(self, line_map):
        points = sorted(line_map.keys())
        merge_box = []
        for i, p in enumerate(points):
            if i + 1 >= len(points):
                break
            next_point = points[i + 1]
            d = next_point - p
            if d <= 2:
                if len(merge_box) != 0 and p in merge_box[-1]:
                    merge_box[-1].append(next_point)
                else:
                    merge_box.append([p, next_point])
        for merge in merge_box:
            linebox = []
            for merge_one in merge:
                linebox = linebox + line_map[merge_one]
                line_map.pop(merge_one)
            new_key = round(sum(merge) / len(merge))
            line_map[new_key] = linebox

        return line_map
