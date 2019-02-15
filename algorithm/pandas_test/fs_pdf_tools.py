# -*- coding: UTF-8 -*-
import pandas as pd

from algorithm.common import configManage
from containers.line import Line

c_name = ['pageNum', 'text', 'x0', 'y0', 'x1', 'y1', 'direction', 'size', 'font', 'word_gap', 'lineIndex', 'type', 'linetableid', 'talbeLineIndexs', 'talbeColumnIndexs', 'a']

def get_data(countryid, companyid, reportid):
    datapath = configManage.config['location'][
                   'pdf_block'] + "/p_country={p_country}/p_company={p_company}/{p_reportid}.csv"
    datapath = datapath.format(p_country=countryid, p_company=companyid, p_reportid=reportid)
    df = pd.read_csv(filepath_or_buffer =datapath, header=None, names=c_name)
    # df = pd.read_csv(datapath)
    # some init
    df['isUseful'] = 1
    df['index'] = df.index
    return df

def line_converge(block_df):
    line_box = []
    index = 0
    for key, group in block_df.groupby(['pageNum', 'lineIndex']):
        line_box.append(Line(key[0], key[1], group, index))
        index = index + 1
    return line_box