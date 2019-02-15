# -*- coding: utf-8 -*-
class Time:
    def __init__(self):
    # 时间类型,1代表时间点,2代表时间范围
        self.time_type = None
        # 时间
        self.time_str = None
        # 如果是时间范围类型表示开始
        self.time_begin = None
        # 如果是时间范围类型表示结束
        self.time_end = None
        # 时间的格式yyyy-mm-dd等
        self.time_format = None
        # 报告期
        self.time_quarter = None
        # 时间范围长度,以月为单位
        self.time_length = None
