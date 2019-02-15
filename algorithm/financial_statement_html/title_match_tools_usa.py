# -*- coding: UTF-8 -*-
import re
import sys

from algorithm.common import tools


def getMatchTitleText(text):
    key = re.sub(r'\s', '', text.lower())
    # key = re.sub(r""",|\||\-|:|\[|\]|\?|\.|\(|\)|/|#|&|'|\"|、|（|）""", '', key)
    key = re.sub(r""",|\||\-|:|\[|\]|\?|\(|\)|/|#|&|'|\"|、|（|）|\.|_| |：|…|’""", '', key)
    discard_word = ['asat',
                    'ason',
                    'fortheyearendedon',
                    'fortheyearended',
                    'fortheyearendeddecember',
                    'fortheyearending',
                    'fortheyear',
                    'theyearended',
                    'fortheperiodended',
                    'attheendoftheyear',
                    'consolidated',
                    'contd',
                    'revised',
                    'yearended',
                    'atdecember',
                    '((januar)|(februar)|(march)|(april)|(may)|(june)|(july)|(august)|(september)|(october)|(november)|(december))',
                    '((january)|(february)|(märz)|(april)|(mai)|(juni)|(juli)|(august)|(september)|(oktober)|(november)|(dezember))',
                    '((jan)|(feb)|(mar)|(apr)|(may)|(jun)|(jul)|(jl)|(aug)|(sep)|(sept)|(oct)|(nov)|(dec))',
                    '((一)|(二)|(三)|(四)|(五)|(六)|(七)|(八)|(九)|(十))',
                    # 'on$',
                    'and$',
                    '续表',
					'续',
                    '年',
					 '月',
					 '日',
                    'continued',
                    'unaudited',
                    'audited',
                    'condensed',
                    'interim',
                    'company',
                    ]
    key = re.sub(r'no\.\d+', '', key)
    key = re.sub(r'[0-9]{1,2}th|[0-9]{1,2}st', '', key)
    key = re.sub(r'\d', '', key)
    rule = tools.linkStr(discard_word, '|')
    key = re.sub(rule, '', key)
    return key


if __name__ == '__main__':
    print getMatchTitleText('CONSOLIDATED STATEMENTS OF CASH FLOWS (…/CONT’D)')
