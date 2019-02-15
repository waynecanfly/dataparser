# -*- coding:utf-8 -*-
import re


def judge(text):
    aim = re.sub('[\(\)\s,%\n\.]', '', text).strip()
    # 序号类型匹配
    # 类型eg:a.
    rome_re = re.compile(r'^[ivxIVX]{1,5}[\.]?$')
    digit_re = re.compile(r'^[0-9]{1,2}[\.]$')
    letter_re = re.compile(r'^[a-zA-Z][\.]$')
    # 包含括号的类型
    rome_re_2 = re.compile(r'^\(?[ivxIVX]{1,5}\)$')
    digit_re_2 = re.compile(r'^\(?0?[0-9]\)$')
    letter_re_2 = re.compile(r'^\(?[a-zA-Z](\+[a-zA-Z])*\)$')
    # begin with 0
    digit_re_3 = re.compile(r'^0[1-9]$')
    digit_re_4 = re.compile(r'^nil$')
    # 数字类型
    value_re = re.compile(r'^-?[0-9]+[\.]?[0-9]*[a-z]?$')

    #占位符判断
    p_rule =  re.compile(r'(^-|^–|^—|(不适用))+')

    # currency
    currency = ['cents']

    if rome_re.match(aim) or digit_re.match(aim) or letter_re.match(aim) or rome_re_2.match(
            text) or digit_re_2.match(text) or letter_re_2.match(text) or digit_re_3.match(text):
        return 'NumOrder'
    elif aim.isdigit() or value_re.match(aim):
        return 'digit'
    elif p_rule.match(aim) or digit_re_4.match(aim.lower()):
        return 'placeholder'  # placeholder
    elif aim in currency:
        return 'currency'
    else:
        if len(aim) > 70:
            return 'text-sentence'
        else:
            return 'text-phrase'