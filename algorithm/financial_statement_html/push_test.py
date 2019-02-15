# -*- coding: UTF-8 -*-
import csv
import re
import traceback

import MySQLdb

from algorithm.common import dbtools, configManage

# push_path = 'Z:\opd\html\html_push\p_country=USA\p_company='
push_path = '/PDFdata/opd/html/html_push/p_country=USA/p_company='

season_type2range = {'Q1': '3',
                     'Q2': '6',
                     'Q3': '9',
                     'FY': '12',
                     'HY': '6',}


def add_str(s):
    s = str(s)
    try:
        if re.findall('"', s):
            return s
    except:
        pass
    s = '"' + str(s) + '"'
    return s


def query_opd_fdss_test(sql):
    common_ip = configManage.config['database']['opd_fdss_test']['ip']
    common_user = configManage.config['database']['opd_fdss_test']['user']
    common_password = configManage.config['database']['opd_fdss_test']['password']
    common_dbname = configManage.config['database']['opd_fdss_test']['name']
    db = MySQLdb.connect(host=common_ip, user=common_user, passwd=common_password, db=common_dbname, port=3306, charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        insert_id = db.insert_id()
        db.commit()
        db.close()
        return {'data': data, 'insert_id': insert_id}
    except Exception:
        db.close()
        raise Exception

def push(report):
    company = report[:8]
    read_path = push_path + company + '/' + report + '.csv'

    data_list = csv.reader(file(read_path, 'r'))

    # 披露日期
    disclosure_date_sql = "SELECT doc_downloaded_timestamp FROM `financial_statement_index` WHERE report_id = {}".format(
        "'" + report + "'")
    disclosure_date_result = dbtools.query_common(disclosure_date_sql)
    disclosure_date_result = disclosure_date_result[0][0]
    disclosure_date_result = add_str(disclosure_date_result)

    company = add_str(company)
    pageNum = None
    table_type = None
    cur_table_type = None
    for data in data_list:
        line = data
        company_name = line[3]
        table_type = line[4]
        fiscal_year = line[5]
        season_type = line[6]
        subject_text = line[11]
        # subject_text = subject_text.split('+_+')[-1]
        value = line[12]
        if '(' in value and ')' in value:
            value = '-' + str(re.sub(r"[()]", '', value))
        currency = line[13]
        measure_unit = line[14]
        time_begin = line[15]
        time_end = line[16]

        if season_type in ('ESG', 'Q'):
            return

        isConsolidated = line[-1]
        month_range = season_type2range[season_type]
        guid = report + table_type

        if time_end.endswith('02-31'):
            time_end = re.sub('31', '28', time_end)
        if time_begin not in ('', 'None'):
            data_range = time_begin + '_' + time_end
        else:
            data_range = time_end

        guid = add_str(guid)
        company_name = add_str(company_name)
        time_begin = add_str(time_begin)
        time_end = add_str(time_end)
        month_range = add_str(month_range)
        season_type = add_str(season_type)
        currency = add_str(currency)
        measure_unit = add_str(measure_unit)
        data_range = add_str(data_range)
        subject_text = add_str(subject_text)
        subject_lable = add_str(re.sub(r"\s", '', subject_text))
        value = add_str(value) if value else value

        if cur_table_type != line[4]:  # 页码不同，类型不同，新表开始
            table_type = add_str(line[4])
            cur_table_type = line[4]
            if table_type != '"BS"':
                data_sql = 'INSERT into g_fs_data_original (guid, country_code, company_name, company_code, disclosure_date, start_date, end_date, month_range, fs_type_code, fs_season_type_code, currency_code, measure_unit_code) ' \
                           'VALUES({guid},{country_code},{company_name},{company_code},{disclosure_date},{start_date},{end_date},{month_range},{fs_type_code},{fs_season_type},{currency_code},{measure_unit_code})'
                data_sql = data_sql.format(guid=guid, country_code="'USA'", company_name=company_name,
                                           company_code=company,
                                           disclosure_date=disclosure_date_result, start_date=time_begin,
                                           end_date=time_end,
                                           month_range=month_range, fs_type_code=table_type, fs_season_type=season_type,
                                           currency_code=currency, measure_unit_code=measure_unit)
            else:
                data_sql = 'INSERT into g_fs_data_original (guid, country_code, company_name, company_code, disclosure_date, end_date, month_range, fs_type_code, fs_season_type_code, currency_code, measure_unit_code) ' \
                           'VALUES({guid},{country_code},{company_name},{company_code},{disclosure_date},{end_date},{month_range},{fs_type_code},{fs_season_type},{currency_code},{measure_unit_code})'
                data_sql = data_sql.format(guid=guid, country_code='"USA"', company_name=company_name,
                                           company_code=company,
                                           disclosure_date=disclosure_date_result,
                                           end_date=time_end,
                                           month_range=month_range, fs_type_code=table_type, fs_season_type=season_type,
                                           currency_code=currency, measure_unit_code=measure_unit)
            ins_original_res = query_opd_fdss_test(data_sql)

            # fs_id_sql = 'SELECT id from g_fs_data_original ORDER BY id desc limit 1'  # 新的id
            #
            # fs_id_result = query_opd_fdss_test(fs_id_sql)
            # fs_id_result = fs_id_result[0][0]
            fs_id_result = ins_original_res['insert_id']


        table_type = add_str(table_type)
        detail_sql = 'INSERT into g_fs_data_original_detail (fs_original_id, fs_original_guid, country_code, company_code, company_name, fiscal_year, fs_type_code, fs_season_type_code, item_name, item_label, item_value, currency_code, unit_of_measurement, end_date, date_range)' \
                     'VALUES({fs_original_id},{fs_original_guid},{country_code},{company_code},{company_name},{fiscal_year},{fs_type_code},{fs_season_type_code},{item_name},{item_label},{item_value},{currency_code},{unit_of_measurement},{end_date},{data_range})'
        detail_sql = detail_sql.format(fs_original_id=fs_id_result, fs_original_guid=guid, country_code='"USA"',
                                       company_code=company, company_name=company_name, fiscal_year=fiscal_year,
                                       fs_type_code=table_type, fs_season_type_code=season_type,
                                       item_name=subject_lable, item_label=subject_text, item_value=value,
                                       currency_code=currency,
                                       unit_of_measurement=measure_unit, end_date=time_end, data_range=data_range)
        if value and subject_text:
            query_opd_fdss_test(detail_sql)


def main():
    configManage.initConfig(False)
    # 获取需要推送的列表
    company_list = [
        'USA13568',
        'USA11726',
        'USA14646',
        'USA11238',
        'USA13455',
        'USA11536',
        'USA15016',
        'USA10503',
        'USA10530',
        'USA10622',
    ]

    sql_com = "('" + "','".join(sorted(company_list)) + "')"

    sql = "SELECT reportid from opd_pdf_status where countryid = 'USA' and statusid = 100 and companyid in {sql_com}".format(sql_com=sql_com)
    reports = dbtools.query_pdfparse(sql)
    reports = [d[0] for d in reports]
    for report in reports:
        try:
            push(report)
            print report
        except Exception as e:
            excepttext = traceback.format_exc()
            print excepttext
            print 'loss' + report
            sql_1 = "DELETE from g_fs_data_original WHERE guid like '" + report + "%';"
            sql_2 = "DELETE from g_fs_data_original_detail WHERE fs_original_guid like '" + report + "%';"
            # 中途失败删除相关记录
            dbtools.query_opd_fdss_test(sql_1)
            dbtools.query_opd_fdss_test(sql_2)


if __name__ == '__main__':
    main()

