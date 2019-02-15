# -*- coding: UTF-8 -*-
import csv
import os
import re
import sys

import MySQLdb


def query_opd_fdss_test(sql):
    common_ip = "10.100.4.88"
    common_user = "u_opd_fdss"
    common_password = "u_opd_fdss"
    common_dbname = "opd_fdss"
    db = MySQLdb.connect(host=common_ip, user=common_user, passwd=common_password, db=common_dbname, port=3306, charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        db.commit()
        db.close()
        return data
    except Exception:
        print sql
        db.close()
        raise Exception


def getRelation():
    rela_map = {}
    sql = "select item_name,item_label,item_code,level,parent_code,fs_type_code,country_code,txnmy_opd_code,company_code,fiscal_year,fs_season_type_code,end_date from g_taxonomy_country_draft_usa where country_code='USA'"
    result = query_opd_fdss_test(sql)
    for r in result:
        key = r[2] + '_' + r[5]
        rela_map[key] = r
    return rela_map



def main():

    # 获取对应关系
    rela = getRelation()

    label_box = {}

    collect_box = []

    not_match_box = []

    f = open('./collect.csv', 'w+')
    out = csv.writer(f)

    counter = 0
    # read file
    read_location = 'c:/temp/xbrl/'
    read_location = '/home/xbrl/us_csv/'
    for root, dirs, files in os.walk(read_location):
        # print dirs
        for one_file in files:
            file_name = os.path.join(root, one_file)
            counter += 1
            print counter

            with open(file_name, 'r') as fo:
                cr = list(csv.reader(fo))
                for line in cr:
                    aimline = [re.sub('\s', '', line[3]), line[13], line[4], re.sub("\s|'|\"|\(|\)", '', line[4].lower()),line[14], line[11], line[12], line[7]]
                    key = aimline[0] + '_' + aimline[1]
                    pure_label_key = aimline[3] +  '_' + aimline[1]

                    if key in rela:
                        t_code = rela[key][7]
                        if pure_label_key not in label_box or (pure_label_key in label_box and t_code not in label_box[pure_label_key]):


                            if pure_label_key in label_box:
                                label_box[pure_label_key].append(t_code)
                            else:
                                label_box[pure_label_key] = [t_code]

                            value = aimline + list(rela[key])
                            collect_box.append(value)
                            out.writerow(value)


    # 插入数据
    # for cd in collect_box:
    #     sql = """INSERT INTO g_taxonomy_country_draft_usa_copy (item_name,item_label,company_code,fiscal_year,fs_season_type_code,end_date) value ("cd[0]",NOW());"""
    f.close()

def insert():
    # [itname, type, label, 干净label, 公司, 年份，季度, endday]
    # item_name, item_label, item_code, level, parent_code, fs_type_code, country_code, txnmy_opd_code, company_code, fiscal_year, fs_season_type_code, end_date

    code_map = {
         'BS': 1002058,
         'IS': 1002254,
         'CF': 1005860,
         'OCI': 1000434
    }

    value_box = []
    with open('./collect.csv', 'r+') as f:
        reader = csv.reader(f)
        for l in reader:
            cur_max = code_map[l[1]] + 1
            code = 'USA' + l[1] + str(cur_max)
            code_map[l[1]] = cur_max
            end_date = l[7] if l[7] != '' else '1949-10-01'
            valueStr = "'{}','{}','{}','{}','{}',{},'{}','{}',{},'{}','{}','{}','{}'".format(code,l[3], re.sub("'|\"", '',l[2]), l[0], l[4], l[5], l[6], end_date, l[11], l[12], l[1], l[14], l[15])
            value_box.append(valueStr)


    position = 0
    is_over = False
    while 1:
        if is_over:
            break

        print position

        endpoint = position + 1000
        if endpoint > len(value_box):
            is_over=True

        this_value = value_box[position: endpoint]

        values = '),('.join(this_value)
        sql = """INSERT INTO g_taxonomy_country_draft_usa_copy (code,item_name,item_label,item_code,company_code,fiscal_year,fs_season_type_code,end_date,level,parent_code,fs_type_code,country_code,txnmy_opd_code) values ({values})""".format(
            values=values)
        query_opd_fdss_test(sql)

        position = endpoint


    # values = '),('.join(value_box)
    #
    # sql = """INSERT INTO g_taxonomy_country_draft_usa_copy (code,item_name,item_label,item_code,company_code,fiscal_year,fs_season_type_code,end_date,level,parent_code,fs_type_code,country_code,txnmy_opd_code) values ({values})""".format(values = values)
    #
    # print sql

    # query_opd_fdss_test(sql)


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')
    main()

    insert()
