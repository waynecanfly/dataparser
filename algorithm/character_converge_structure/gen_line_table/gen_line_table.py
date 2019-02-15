# -*- coding:utf-8 -*-
import copy
import sys

from algorithm.character_converge_structure.container.PageSeg import PageSeg
from algorithm.character_converge_structure.container.line import Line
from algorithm.character_converge_structure.container.linetable import LineTable
from algorithm.character_converge_structure.gen_line_table import gen_line_table_tools
from algorithm.common import tools


def gen_table_y_range(linebox):
    # setp 1： 获取所有垂直线，并获取相应的起始点
    v_line_map = {}

    for l in linebox:
        if l.direction == 1:
            if l.x0 not in v_line_map:
                v_line_map[l.x0] = [l]
            else:
                v_line_map[l.x0].append(l)

    directionLines = {}
    for l in linebox:
        aim = [l.y0, l.y1]

        if aim[0] not in directionLines:
            directionLines[aim[0]] = aim[1]
        else:
            directionLines[aim[0]] = directionLines[aim[0]] if directionLines[aim[0]] > aim[1] else aim[1]

    # setp 2
    beginPoints = sorted(directionLines.keys())
    lineSegment = [[beginPoints[0], directionLines[beginPoints[0]]]]

    for b in beginPoints:
        begin = b
        end = directionLines[b]
        curSeg = lineSegment[-1]
        if begin > curSeg[1] and abs(begin - curSeg[1]) > 2:  # 超过三个像素认为断开，不相交，生成新线段
            lineSegment.append([begin, end])
        else:
            curSeg[1] = curSeg[1] if curSeg[1] > end else end
    return lineSegment


def get_word_height(wordbox):
    height = 0
    for w in wordbox:
        height = height + abs(w.y1 - w.y0)
    return height / len(wordbox)


def tableFilter(t, word_height):
    # rule1： 表范围不能太小，不然通常就是一根线
    if not (abs(t.top - t.bottom) > 5 and abs(t.left-t.right) > 5):
        return False

    # rule2: 垂直和水平线的数量都要大于2
    if len(t.h_segment_map)<3 or len(t.v_segment_map) < 3:
        return False

    # rule3 : 两根水平直线距离不能超过该页平均字符高度的5倍
    box = sorted(t.h_segment_map.keys())
    lenght = len(box)
    for i, h in enumerate(box):
        if i+1 >= lenght:
            break
        gap = abs(box[i+1] - h)
        if gap > word_height * 7 and len(t.h_segment_map)<3 and len(t.v_segment_map) < 2:
            return False

    return True


def filterUselessLine(lineboxMap):
    for pagenum in lineboxMap.keys():
        linebox = []
        for line in lineboxMap[pagenum]:
            if abs(line.x0) < 3 or abs(line.y0) < 3:
                print [line.x0, line.x1, line.y0, line.y1]
                # lineboxMap[pagenum].remove(line)
            else:
                linebox.append(line)
        lineboxMap[pagenum] = linebox
        if len(lineboxMap[pagenum]) == 0:
            lineboxMap.pop(pagenum)


def overlapNum(check_seg, seg_box):
    overlap_count = 0
    for v in seg_box:
        for seg in v:
            if seg[0]<=check_seg[0] and seg[1]>=check_seg[1]:
                overlap_count += 1
    return overlap_count

def gen_gap_thr(gaps):
    if len(gaps) == 1:
        return 0
    try:
        del gaps[-2]
        del gaps[-1]
        del gaps[0]
    except:
        return sys.maxint
    if len(gaps) < 2:
        return sys.maxint
    gap_thr = sum(gaps)/len(gaps) * 3
    return gap_thr

def split_by_H(h_seg_map):
    v_points = sorted(h_seg_map.keys())
    vpoint_lastpoint_gap = {}
    for i in range(0, len(v_points)):
        cur_p = v_points[i]
        if i+1 == len(v_points):
            vpoint_lastpoint_gap[cur_p] = sys.maxint
            break
        last_p = v_points[i+1]
        gap = last_p - cur_p
        vpoint_lastpoint_gap[cur_p] = gap

    seg_start_point = None
    gap_thr = gen_gap_thr(sorted(vpoint_lastpoint_gap.values()))

    result = []

    for point in sorted(vpoint_lastpoint_gap.keys()):
        gap = vpoint_lastpoint_gap[point]
        if gap <= gap_thr and seg_start_point is None:
            seg_start_point = point
        elif gap > gap_thr and seg_start_point is not None:
            result.append([seg_start_point, point])
            seg_start_point = None

    return result


def split_by_V(v_seg_map):
    legal_overlap_thr = 2
    table_v_seg_box = []  # 每一段代表一个table的垂直范围

    seg_point = set()
    for segs in v_seg_map.values():
        for seg in segs:
            seg_point = seg_point | set(seg)
    seg_point = sorted(list(seg_point))
    legal_start_point = None
    startpoint = seg_point[0]
    for i in range(1, len(seg_point)):
        point = seg_point[i]
        check_seg = [startpoint, point]
        # 计算check_seg和所有垂直线段的重叠数，如果重叠数少于2， 则该check_seg所表示的范围不应该由表，则断开
        ov_num = overlapNum(check_seg, v_seg_map.values())
        if ov_num < legal_overlap_thr and legal_start_point is not None:
            table_v_seg_box.append([legal_start_point, startpoint])
            legal_start_point = None
        elif ov_num >=legal_overlap_thr and legal_start_point is None:
            legal_start_point = startpoint
        # 如果时最后一个点，且上一段时有效的，则应生成新的垂直有效线段
        if i+1 == len(seg_point) and ov_num >=legal_overlap_thr :
            table_v_seg_box.append([legal_start_point, point])

        startpoint = point
    return table_v_seg_box


def gen_table_v_seg(page_seg):
    if not page_seg.v_seg_map or not page_seg.h_seg_map:
        return []
    # 以垂直线段作为标准进行划分
    v_seg_by_v = split_by_V(page_seg.v_seg_map)

    # 以水平线段作为标准进行划分
    # v_seg_by_h = split_by_H(page_seg.h_seg_map)
    v_seg_by_h = v_seg_by_v


    # 以垂直线分出的范围为准，水平线分出的范围起分割的作用
    table_v_seg_box = []

    for seg_by_v in v_seg_by_v:
        for seg_by_h in v_seg_by_h:
            if not (seg_by_h[0] >= seg_by_v[1] or seg_by_h[1] <= seg_by_v[0]): # 符合这个条件表示有交集
                points = sorted(seg_by_v + seg_by_h)
                table_v_seg_box.append([points[1], points[2]])

    table_v_seg_box.reverse()
    return table_v_seg_box

def check_if_legal(new_table):
    # if new_table.pageNum == 38:
    #     pass
    # 横向、纵向线数量
    if not (len(new_table.h_segment_map)>=2):
    # if not (len(new_table.h_segment_map)>=2 and len(new_table.v_segment_map)>3):
        return False

    # 纵向的线最小值限制：纵向线最小值不应该大于200
    # if min(new_table.v_segment_map.keys()) > 200:
    #     return False

    # 横向线最靠近顶端处，若小于600，则此时该表往上大概率还有文本，则该表应为完整的一张表，此时，横向的线至少应有三条
    # x = len(new_table.v_segment_map)
    # y = len(new_table.h_segment_map)
    # z = max(new_table.h_segment_map.keys())
    # if max(new_table.h_segment_map.keys()) < 600 and len(new_table.h_segment_map) < 3 and len(new_table.v_segment_map)<4:
    #     return False

    return True


def gen_line_tables(page_seg_map, wordBoxMap):
    linetableMap = {}
    for pn in page_seg_map.keys():
        if pn == 24:
            pass
        page_seg = page_seg_map[pn]

        table_range_seg = gen_table_v_seg(page_seg)  # 每一段代表一个table的垂直范围

        if not table_range_seg:
            continue

        linetableMap[pn] = []

        # 根据table_v_seg生成line_table
        for i, table_range in enumerate(table_range_seg):
            h_box = {}
            v_box = {}
            for h_point in page_seg.h_seg_map.keys():
                if h_point >= table_range[0]-2 and h_point <= table_range[1]+2:
                    h_box[h_point] = page_seg.h_seg_map[h_point]
            for v_point in page_seg.v_seg_map.keys():
                v_seg_box = page_seg.v_seg_map[v_point]
                for v_seg in v_seg_box:
                    if not (v_seg[0]>=table_range[1] or v_seg[1]<=table_range[0]):
                        points = sorted(v_seg + table_range)
                        if v_point not in v_box:
                            v_box[v_point] = [[points[1], points[2]]]
                        else:
                            v_box[v_point].append([points[1], points[2]])

            new_table = LineTable(pn, i, v_box, h_box)

            if check_if_legal(new_table):
                linetableMap[pn].append(new_table)

    return linetableMap


def gen_direction_line(lineboxMap):
    for pn in lineboxMap.keys():
        if pn == 4:
            pass
        linebox_str = set()
        for line in lineboxMap[pn]:
            linebox_str.add(tools.linkStr([line.pageNum, line.x0, line.y0, line.x0, line.y1, 1], '_'))
            linebox_str.add(tools.linkStr([line.pageNum, line.x1, line.y0, line.x1, line.y1, 1], '_'))
            linebox_str.add(tools.linkStr([line.pageNum, line.x0, line.y0, line.x1, line.y0, 0], '_'))
            linebox_str.add(tools.linkStr([line.pageNum, line.x0, line.y1, line.x1, line.y1, 0], '_'))
        lineboxMap[pn] = []
        for l_str in linebox_str:
            paras = l_str.split('_')
            new_line = Line(paras[0], paras[1], paras[2], paras[3], paras[4], paras[5])
            lineboxMap[pn].append(new_line)


def gen_page_seg(lineboxMap):
    page_seg_map = {}
    for pn in lineboxMap.keys():
        linebox = lineboxMap[pn]
        page_seg_map[pn] = PageSeg(pn, linebox)
    return page_seg_map

def process(p_country, p_company, p_reportid, wordBoxMap):
    # 获取原始信息
    lineboxMap = gen_line_table_tools.getLineInfoSource(p_country, p_company, p_reportid)

    # 对值进行四舍五入
    gen_line_table_tools.mergeDigitValue(lineboxMap)

    # 生成单一方向的线。由x0,x1,y0,y1生成方向相同的(x或y相同)的线
    gen_direction_line(lineboxMap)

    # 按方向生成线段
    page_seg_map = gen_page_seg(lineboxMap)

    # 按条件拆分成线表
    line_table_box_map = gen_line_tables(page_seg_map, wordBoxMap)

    # 过滤掉无表的页码
    for pn in line_table_box_map.keys():
        if len(line_table_box_map[pn]) == 0:
            line_table_box_map.pop(pn)

    return line_table_box_map