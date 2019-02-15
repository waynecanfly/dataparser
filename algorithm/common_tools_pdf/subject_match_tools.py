# -*- coding: UTF-8 -*-
import re

from algorithm.common import tools


def getPureSbuectText(text):
    '加：公允价值变动收益（损失以“”号填列）'
    key = re.sub(r'\s', '', text.lower())
    key = re.sub(r""",|\||-|—|:|：|．|\*|\[|\]|\?|\.|\(|\)|/|#|&|'|\"|、|－|（|）|“|”|―|‖|~|，|！|¡|。|‛|‚|­|；|;|？|】|【|※|﹑|\^|〔|·|‐|‘|’|＂|＂|\+|–|／|_|>|%""", '', key)
    key = re.sub('^其中', '', key)
    key = re.sub('^加', '', key)
    discard_word = [
                    '((一)|(二)|(三)|(四)|(五)|(六)|(七)|(八)|(九)|(十))',
                    '(⒈|⒉|⒊|⒋|⒌)',
                    '(㈡|㈠)',
                    '(⑴|⑵|⑶|⑷|⑸|⑹|⑺|⑻|⑼|⑽|⑾|⑿|⒀|⒁|⒂|⒃|⒄|⒅|⒆|⒇)',
                    '１|３|附注$'
                    ]
    key = re.sub(r'\d', '', key)
    rule = tools.linkStr(discard_word, '|')
    key = re.sub(rule, '', key)
    key = re.sub('（）', '', key)
    return key


if __name__ == '__main__':
    print getPureSbuectText('３个月以上到期定期存款')
