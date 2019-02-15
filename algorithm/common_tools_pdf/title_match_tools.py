# -*- coding: UTF-8 -*-
import re
import sys

from algorithm.common import tools, configManage, dbtools


def get_title_lib(company_name):
        title_lib = {}
        # sqlj = "insert into title_match_lib(title, matchcode, tabletype,language_type , user_create) values('年初到报吿期末利润表','初到报吿期末利润表', 'IS', 'CHN', 'li') "
        # result = dbtools.query_pdfparse(sqlj)
        sql = 'select matchcode, tabletype from title_match_lib'
        result = dbtools.query_pdfparse(sql)
        for unit in result:
            key = getMatchTitleText(unit[0].encode('utf-8'), company_name)
            # print key
            title_lib[key] = unit[1]
        # print '=============================='
        return title_lib

new_box = [
'2012年6月30日公司资产负债表',
'2012年12月31日公司资产负债表',
'截至2013年6月30日止6个月期间公司现金流量表',
'截至2018年6月30日止六个月期间公司利润表',
'2011年度公司利润表'
]

def getMatchTitleText(text, company_name=''):
    key = re.sub(company_name, '', text.lower())
    key = re.sub(r'\s', '', key)
    # key = re.sub(r""",|\||\-|:|\[|\]|\?|\.|\(|\)|/|#|&|'|\"|、|（|）""", '', key)
    key = re.sub(r""",|\||\-|:|\[|\]|\?|\(|\)|/|#|&|'|\"|、|（|）|\.|_| |：|’""", '', key)
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
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)

    lib = get_title_lib('')

    news = {}

    for n in new_box:
        n_list = n.split(',')
        pure_text = getMatchTitleText(n_list[1])
        # print pure_text
        if pure_text not in lib and pure_text not in news:
            lange = 'EN' if re.match('^([a-z]|[A-Z]])+$', pure_text) else 'CHN'
            n_list = n_list + [pure_text, lange]
            news[pure_text] = n_list

    for i  in news.values():
        sql = "insert into title_match_lib(title, matchcode, tabletype, language_type, reportid, countryid, user_create) value ('{title}', '{matchcode}', '{tabletype}', '{language_type}', '{reportid}', 'CHN', 'li')"
        sql = sql.format(title=i[1],matchcode=i[3],tabletype=i[2],language_type=i[4],reportid=i[0])
        dbtools.query_pdfparse(sql)