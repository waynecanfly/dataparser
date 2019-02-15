# -*- coding: UTF-8 -*-
import csv
import datetime
import re
import sys
import traceback

from algorithm.common import dbtools, configManage, tools
from algorithm.common.para import Para
from algorithm.financial_statement_pdf import fs_pdf_tools
from algorithm.financial_statement_pdf.fs_push_tools import get_company_leader, delete_bf_push, \
    special_handling_subject, special_handling_value, get_disclosure_date_result, update_aft_push, delete_bf_push_test, \
    get_company_leader_test

push_path = 'X:\pdf\pdf_table_new\p_country=CHN\p_company='

season_type2range = {'Q1': '3',
                     'Q2': '6',
                     'Q3': '9',
                     'FY': '12',
                     'HY': '6'}
class PushException(Exception):
    def __init__(self, message):
        Exception.__init__(self, message)
        self.message = message

def push(report,country,company):
    company = report[:8]
    read_path = push_path + company + '/' + report + '.csv'

    data_list = csv.reader(file(read_path, 'r'))
    # 文件地址
    path_sql = "SELECT doc_source_url, doc_local_path FROM `financial_statement_index` WHERE report_id = '{}'".format(report)
    path_result = dbtools.query_common(path_sql)
    path_data = path_result[0]
    source_url, local_path = path_data

    pageNum = None
    table_type = None

    isConSet = set()
    data_list_new = []
    for line in data_list:
        isConSet.add(line[-1])
        data_list_new.append(line)


    if len(isConSet) > 1:
        # 获取
        temp_map = {
            "-1_0" : -1,
            "-1_1" : 1,
            "0_1" : 1,
            "-1_0_1" : 1
        }
        aim_value = temp_map['_'.join(sorted(list(isConSet)))]
        data_list_new = [x for x in data_list_new if int(x[-1]) == aim_value]

    data_list_new = list(data_list_new)
    table_dict = {}
    for data in data_list_new:
        table_type = data[4]
        if table_type not in table_dict:
            table_dict[table_type] = [data]
        else:
            table_dict[table_type].append(data)


    for key, item in table_dict.items():
        guid = report + key
        table_type = key
        first_line = item[0]
        company_name = first_line[3]
        table_type = key
        fiscal_year = first_line[6]
        season_type = first_line[7]
        item_label = first_line[8]
        value = first_line[9]
        header_currency = first_line[10]
        header_measureunit = first_line[11]
        time_begin = first_line[12]
        time_end = first_line[13]

        is_locked = 0
        now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        gmt_create = now_time
        user_create = 'cf'

        month_range = season_type2range[season_type]

        if time_end.endswith('02-31'):
            time_end = re.sub('31', '28', time_end)

        # 获取报表负责人
        person = get_company_leader(guid)
        # 标记已完成的不推
        checkifdone_sql = "SELECT is_check_done from g_fs_data_original where guid='{}'".format(guid)
        result = dbtools.query_opd_fdss(checkifdone_sql)
        if result:
            is_check_done = result[0][0]
            if is_check_done == 'Y':
                continue
            elif is_check_done == 'N':
                # 推数据前执行删除
                delete_bf_push(guid)
                configManage.logger.info(guid + 'deleted')
        # 披露日期
        disclosure_date_result = get_disclosure_date_result(report)
        # 披露日期为空的用截至日期填上
        if disclosure_date_result == None:
            disclosure_date_result = time_end

        if key != 'BS':
            data_sql = """INSERT into g_fs_data_original (guid, country_code, company_name, company_code, disclosure_date,fiscal_year, start_date, end_date, month_range, fs_type_code, fs_season_type_code, doc_source_path, doc_source_url, currency_code, measure_unit_code,is_locked,assigned_to,gmt_create,user_create)
            VALUES('{guid}','{country_code}','{company_name}','{company_code}','{disclosure_date}','{fiscal_year}','{start_date}','{end_date}','{month_range}','{fs_type_code}','{fs_season_type}','{doc_source_path}','{doc_source_url}','{currency_code}','{measure_unit_code}','{is_locked}','{assigned_to}','{gmt_create}','{user_create}')"""
            data_sql = data_sql.format(guid=guid, country_code='CHN', company_name=company_name,
                                       company_code=company,
                                       disclosure_date=disclosure_date_result, fiscal_year=fiscal_year, start_date=time_begin,
                                       end_date=time_end,
                                       month_range=month_range, fs_type_code=table_type,
                                       doc_source_path=local_path, doc_source_url=source_url,
                                       fs_season_type=season_type,
                                       currency_code=header_currency, measure_unit_code=header_measureunit, is_locked=is_locked,
                                       gmt_create=gmt_create, user_create=user_create, assigned_to=person)
        else:
            data_sql = """INSERT into g_fs_data_original (guid, country_code, company_name, company_code, disclosure_date,fiscal_year, end_date, month_range, fs_type_code, fs_season_type_code,doc_source_path, doc_source_url, currency_code, measure_unit_code,is_locked,assigned_to,gmt_create,user_create)
            VALUES('{guid}','{country_code}','{company_name}','{company_code}','{disclosure_date}','{fiscal_year}','{end_date}','{month_range}','{fs_type_code}','{fs_season_type}','{doc_source_path}','{doc_source_url}','{currency_code}','{measure_unit_code}','{is_locked}','{assigned_to}','{gmt_create}','{user_create}')"""
            data_sql = data_sql.format(guid=guid, country_code='CHN', company_name=company_name,
                                       company_code=company,
                                       disclosure_date=disclosure_date_result, fiscal_year=fiscal_year,
                                       end_date=time_end,
                                       month_range=month_range, fs_type_code=table_type,
                                       doc_source_path=local_path, doc_source_url=source_url,
                                       fs_season_type=season_type,
                                       currency_code=header_currency, measure_unit_code=header_measureunit, is_locked=is_locked,
                                       gmt_create=gmt_create, user_create=user_create, assigned_to=person)
        # print data_sql
        dbtools.query_opd_fdss(data_sql)


        fs_id_sql = "SELECT id from g_fs_data_original where guid = '{}'".format(guid)  # 新的id
        fs_id_result = dbtools.query_opd_fdss(fs_id_sql)
        fs_id_result = fs_id_result[0][0]

        detail_sql = """INSERT into g_fs_data_original_detail (fs_original_id, fs_original_guid, country_code, company_code, company_name, fiscal_year, fs_type_code, fs_season_type_code, item_name, item_label, item_value, unit_of_measurement, end_date, date_range) VALUES"""
        for i in range(len(item)):
            data = item[i]
            fiscal_year = data[6]
            season_type = data[7]
            item_label = data[8]
            subject_text = special_handling_subject(item_label)
            value = data[9]
            item_value = special_handling_value(value)
            header_measureunit = data[11]
            time_begin = data[12]
            time_end = data[13]
            if time_end.endswith('02-31'):
                time_end = re.sub('31', '28', time_end)
            if time_begin not in ('', 'None'):
                data_range = time_begin + '_' + time_end
            else:
                data_range = time_end
            values_sql = """('{fs_original_id}','{fs_original_guid}','{country_code}','{company_code}','{company_name}','{fiscal_year}','{fs_type_code}','{fs_season_type_code}','{item_name}','{item_label}','{item_value}','{unit_of_measurement}','{end_date}','{data_range}'),"""
            values_sql = values_sql.format(fs_original_id=fs_id_result, fs_original_guid=guid, country_code='CHN',
                                           company_code=company, company_name=company_name, fiscal_year=fiscal_year,
                                           fs_type_code=table_type, fs_season_type_code=season_type,
                                           item_name=subject_text, item_label=item_label, item_value=item_value,
                                           unit_of_measurement=header_measureunit, end_date=time_end, data_range=data_range)
            detail_sql += values_sql
        detail_sql = detail_sql[:-1]# 去掉最后一个逗号
        # print detail_sql
        dbtools.query_opd_fdss(detail_sql)

def process(para):
    report = para.reportid
    country = para.countryid
    company = para.companyid

    configManage.logger.info('PUSH BEGIN ' + report + ' : ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    try:
        # 推送
        push(report,country, company)
        print report + 'pushed'
        # 更新状态
        tools.updatePDFStatus(country, company, report, 110, '')
        print report + 'updated'
    except PushException as e:
        excepttext = e.message
        tools.updatePDFStatus(country, company, report, -110, excepttext)
    except Exception as e:
        excepttext = traceback.format_exc()
        print excepttext
        print report + 'loss'
        # 更新状态
        tools.updatePDFStatus(country, company, report, -110, '')
    configManage.logger.info('PUSH END ' + report + ' : ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))



if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)
    sql = "select reportid from opd_pdf_status where countryid = 'CHN' and statusid in (50)"""
    reports = dbtools.query_pdfparse(sql)
    idlist = [d[0] for d in reports]
    idlist = ['CHN1333767690381']
    for l in idlist:
        reportid = l
        # print reportid
        countryid = reportid[0:3]
        companyid = reportid[0:8]
        companyname = fs_pdf_tools.getCompanyName(companyid)
        # countryid, companyid, reportid, statusid, country_name, company_name, fiscal_year,season_type_code, history_status, data_mark, doc_path, doc_type, report_type, error_code = '')
        para = Para(countryid, companyid, reportid, 20, '2', companyname, '4', '5', '6', '7', 'x', '8', '9')

        process(para)
    # 一系列数据状态更新
    update_aft_push()