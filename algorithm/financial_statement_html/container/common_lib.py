# -*- coding:utf-8 -*-
import re

useless_table_tails = [
    'The accompanying notes are an integral part of these statements.',
]

useless_table_tails = [re.sub(r"\s", '', i) for i in useless_table_tails]
