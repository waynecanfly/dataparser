# -*- coding: UTF-8 -*-
import csv
import datetime
import re
import traceback

import MySQLdb

from algorithm.common import dbtools, configManage

# push_path = 'Z:\opd\pdf\pdf_push\p_country=HKG\p_company='
push_path = '/PDFdata/opd/pdf/pdf_push/p_country=HKG/p_company='

season_type2range = {'Q1': '3',
                     'Q2': '6',
                     'Q3': '9',
                     'FY': '12',
                     'HY': '6', }


def push(report):
    company = report[:8]
    read_path = push_path + company + '/' + report + '.csv'

    data_list = csv.reader(file(read_path, 'r'))

    # 披露日期
    disclosure_date_sql = """SELECT disclosure_date FROM `financial_statement_index` WHERE report_id = '{report}'""".format(
        report=report)
    disclosure_date_result = dbtools.query_common(disclosure_date_sql)
    disclosure_date_result = disclosure_date_result[0][0]

    # 文件地址
    path_sql = """SELECT doc_source_url, doc_local_path FROM `financial_statement_index` WHERE report_id = '{report}'""".format(
        report=report)
    path_result = dbtools.query_common(path_sql)
    path_data = path_result[0]
    source_url, local_path = path_data

    data_list = list(data_list)
    table_dict = {}
    for data in data_list:
        table_type = data[4]
        if table_type not in table_dict:
            table_dict[table_type] = [data]
        else:
            table_dict[table_type].append(data)

    for key, item in table_dict.items():
        if key == 'OCI' and 'IS' not in table_dict.keys():
            key = 'IS'
        guid = report + key
        person = get_person(guid)
        delete_message(guid)  # 正式删除的代码
        table_type = key
        first_line = item[0]  # 读取第一行，获取基本信息，时间信息暂时以第一行的为准
        company_id = first_line[1][3:]
        company_name = first_line[3]
        season_type = first_line[7]
        currency = first_line[10]
        measure_unit = first_line[11]
        time_begin = first_line[12]
        time_end = first_line[13]
        if time_begin in ('None', ''):
            time_begin = 'null'
        else:
            time_begin = "'{time_begin}'".format(time_begin=time_begin)

        if season_type in ('ESG', 'Q'):
            return

        month_range = season_type2range[season_type]

        original_sql = """INSERT into g_fs_data_original (guid, country_code, company_id, company_name, company_code, disclosure_date, start_date, end_date, month_range, fs_type_code, fs_season_type_code, doc_source_path, doc_source_url, currency_code, measure_unit_code, assigned_to) 
        VALUE('{guid}','{country_code}', '{company_id}',"{company_name}",'{company_code}','{disclosure_date}',{start_date},'{end_date}','{month_range}','{fs_type_code}','{fs_season_type}', '{doc_source_path}', '{doc_source_url}','{currency_code}','{measure_unit_code}','{assigned_to}')"""
        original_sql = original_sql.format(guid=guid, country_code='HKG', company_name=company_name,
                                           company_id=company_id, company_code=company,
                                           disclosure_date=disclosure_date_result, start_date=time_begin,
                                           end_date=time_end,
                                           month_range=month_range, fs_type_code=table_type,
                                           fs_season_type=season_type,
                                           doc_source_path=local_path, doc_source_url=source_url,
                                           currency_code=currency, measure_unit_code=measure_unit,
                                           assigned_to=person)
        fs_id_result = insert_fs_original_id(original_sql)

        detail_sql = """INSERT into g_fs_data_original_detail (fs_original_id, fs_original_guid, country_code, company_id, company_code, company_name, fiscal_year, fs_type_code, fs_season_type_code, item_name, item_label, item_value, currency_code, unit_of_measurement, end_date, date_range) VALUES"""
        for i in range(len(item)):
            data = item[i]
            fiscal_year = data[6]
            season_type = data[7]
            subject_text = data[8]
            value = data[9]
            measure_unit = data[11]
            time_begin = data[12]
            time_end = data[13]

            if time_begin not in ('', 'None'):
                data_range = time_begin + '_' + time_end
            else:
                data_range = time_end
            # 推送需要做的特殊操作：
            subject_text = subject_text.split('+_+')[-1]
            subject_code = subject_hkg(subject_text)
            value = value_hkg(value)
            if not subject_text and not value:
                continue
            values_sql = """('{fs_original_id}','{fs_original_guid}','{country_code}', '{company_id}','{company_code}',"{company_name}",'{fiscal_year}','{fs_type_code}','{fs_season_type_code}',"{item_name}","{item_label}",'{item_value}', '{currency_code}','{unit_of_measurement}','{end_date}','{data_range}'),"""
            values_sql = values_sql.format(fs_original_id=fs_id_result, fs_original_guid=guid, country_code='HKG',
                                           company_id=company_id, company_code=company, company_name=company_name,
                                           fiscal_year=fiscal_year, fs_type_code=table_type,
                                           fs_season_type_code=season_type, item_name=subject_code,
                                           item_label=subject_text, item_value=value, currency_code=currency,
                                           unit_of_measurement=measure_unit, end_date=time_end, data_range=data_range)
            detail_sql += values_sql
        detail_sql = detail_sql[:-1]  # 去掉最后多拼的一个逗号
        dbtools.query_opd_fdss_test(detail_sql)


def get_person(guid):
    sql = """select assigned_to from g_fs_data_original WHERE guid = '{guid}%'""".format(guid=guid)
    person_result = dbtools.query_opd_fdss_test(sql)
    if person_result:
        return person_result[0][0]
    else:
        return 'notAssigned'


def delete_message(guid):
    sql_id = """select id from g_fs_data_original WHERE guid = '{guid}'""".format(guid=guid)
    id_result = dbtools.query_opd_fdss_test(sql_id)
    if id_result:
        for id in id_result:
            del_detail = """DELETE from g_fs_data_original_detail WHERE fs_original_id = {id}""".format(id=id[0])
            dbtools.query_opd_fdss_test(del_detail)
            del_original = """DELETE from g_fs_data_original WHERE id = {id}""".format(id=id[0])
            dbtools.query_opd_fdss_test(del_original)


def insert_fs_original_id(sql):
    common_ip = configManage.config['database']['opd_fdss_test']['ip']
    common_user = configManage.config['database']['opd_fdss_test']['user']
    common_password = configManage.config['database']['opd_fdss_test']['password']
    common_dbname = configManage.config['database']['opd_fdss_test']['name']
    db = MySQLdb.connect(host=common_ip, user=common_user, passwd=common_password, db=common_dbname, port=3306,
                         charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        id = db.insert_id()
        db.commit()
        db.close()
        return id
    except Exception:
        db.close()
        excepttext = traceback.format_exc()
        print sql
        print excepttext
        raise Exception


companyids = ['HKG13174',
              'HKG13150',
              'HKG13190',
              'HKG13336',
              'HKG13182',
              'HKG13169',
              'HKG13277',
              'HKG13111',
              'HKG13127',
              'HKG13205',
              'HKG13252',
              'HKG13281',
              'HKG13247',
              'HKG13296',
              'HKG13245',
              'HKG13159',
              'HKG13210',
              'HKG13226',
              'HKG13209',
              'HKG13225',
              'HKG13240',
              'HKG13255',
              'HKG13105',
              'HKG13234',
              'HKG13217',
              'HKG13179',
              'HKG13292',
              'HKG13189',
              'HKG13254',
              'HKG13138',
              'HKG13148',
              'HKG13121',
              'HKG13251',
              'HKG13103',
              'HKG13267',
              'HKG13196',
              'HKG13094',
              'HKG13307',
              'HKG13222',
              'HKG13200',
              'HKG13284',
              'HKG13153',
              'HKG13313',
              'HKG13098',
              'HKG13212',
              'HKG13324',
              'HKG13224',
              'HKG13125',
              'HKG13219',
              'HKG13183']


def get_reports():
    summary_reports = []
    for companyid in companyids:
        # 这里是每家公司五张报表
        sql = """SELECT reportid from opd_pdf_status where countryid = 'HKG' and data_mark != 'ETF' and statusid in (100, -110) and companyid = '{companyid}' limit 10""".format(companyid=companyid)
        reports = dbtools.query_pdfparse(sql)
        reports = [d[0] for d in reports]
        summary_reports.extend(reports)
    return summary_reports


def subject_hkg(subject_text):
    subject_text = subject_text.split('+_+')[-1]
    subject = ''.join(re.findall('\w|\s', subject_text))
    return subject


def value_hkg(value):
    if re.findall('(n/a|-|=|\*|#|—)', value.lower()):
        return value
    if re.match('^\(.*\)$', value):
        value = '-' + value[1:-1]
    value = re.findall('-|\d|\.', value)
    return ''.join(value)


def main():
    # 获取需要推送的列表
    print 'PUSH BEGIN ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    reports = get_reports()
    # reports = ['HKG131742017000801002']
    for report in reports:
        try:
            push(report)
        except Exception as e:
            excepttext = traceback.format_exc()
            # 中途失败更新状态码
            upadte_sql = """UPDATE opd_pdf_status SET statusid = -110, status_info ='{error}' WHERE reportid = '{report}';""".format(
                report=report, error=str(excepttext))
            dbtools.query_pdfparse(upadte_sql)
            print excepttext
            print report + '-----------------------loss'
        else:
            # 推送成功更新状态码
            upadte_sql = """UPDATE opd_pdf_status SET statusid = 110, status_info = 'pushed' WHERE reportid = '{report}';""".format(
                report=report)
            dbtools.query_pdfparse(upadte_sql)
            print report + '----successful'
    print 'PUSH END ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def del_HKG():
    id_sql = """SELECT id from g_fs_data_original WHERE country_code = 'HKG'"""
    id_result = dbtools.query_opd_fdss_test(id_sql)
    if not id_result:
        return
    ids = [id[0] for id in id_result]
    for id in ids:
        del_detail_sql = """DELETE from g_fs_data_original_detail WHERE fs_original_id = '{fs_id}'""".format(fs_id=id)
        dbtools.query_opd_fdss_test(del_detail_sql)
        del_origin_sql = """DELETE from g_fs_data_original WHERE id = '{fs_id}'""".format(fs_id=id)
        dbtools.query_opd_fdss_test(del_origin_sql)
        print id


if __name__ == '__main__':
    configManage.initConfig(False)
    main()
    # del_HKG()
