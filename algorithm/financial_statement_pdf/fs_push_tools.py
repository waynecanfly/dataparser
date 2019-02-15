# -*- coding:utf-8 -*-
import re
import sys

from algorithm.common import dbtools, tools, configManage


def update_aft_push():

    # 更新公司数据状态
    sql1 = "UPDATE g_company SET has_data = 1 WHERE `code` IN (SELECT DISTINCT company_code FROM g_fs_data_original) AND has_data = 0;"
    # print sql1
    dbtools.query_opd_fdss(sql1)
    sql2 = "UPDATE g_company SET has_data = 0 WHERE `code` NOT IN (SELECT DISTINCT company_code FROM g_fs_data_original) AND has_data = 1;"
    dbtools.query_opd_fdss(sql2)

    # 更新公司已完成状态is_completed
    sql3 = "UPDATE g_company SET is_completed = 0 WHERE `code` NOT IN (SELECT t2.company_code FROM(SELECT count(t1.is_check_done) cnt,t1.is_check_done,t1.company_code \
		FROM (SELECT company_code,is_check_done FROM `g_fs_data_original` GROUP BY company_code,is_check_done) t1 GROUP BY t1.company_code HAVING cnt = 1) t2 WHERE t2.is_check_done = 'Y') AND is_completed = 1;"
    dbtools.query_opd_fdss(sql3)

    #更新报表归属
    sql4 = "UPDATE g_company SET assigned_to = 'notAssigned' WHERE assigned_to IS NULL OR assigned_to = '';"
    dbtools.query_opd_fdss(sql4)
    sql5 = "UPDATE g_fs_data_original t1 LEFT JOIN (SELECT `code`,assigned_to FROM g_company) t2 ON t1.company_code = t2.`code` SET t1.assigned_to = t2.assigned_to WHERE t1.is_check_done = 'N' " \
           "and (t1.assigned_to IS NULL OR t1.assigned_to = '' OR t1.assigned_to = 'notAssigned');"
    dbtools.query_opd_fdss(sql5)

    # 更新季度类型、报表类型sort
    sql6 = "update g_fs_data_original set fs_season_type_code_sort = 1 where fs_season_type_code = 'Q1';"
    sql7 = "update g_fs_data_original set fs_season_type_code_sort = 2 where fs_season_type_code = 'Q2';"
    sql8 = "update g_fs_data_original set fs_season_type_code_sort = 3 where fs_season_type_code = 'Q3';"
    sql9 = "update g_fs_data_original set fs_season_type_code_sort = 4 where fs_season_type_code = 'Q4';"
    sql10 ="update g_fs_data_original set fs_season_type_code_sort = 5 where fs_season_type_code = 'FY';"
    dbtools.query_opd_fdss(sql6)
    dbtools.query_opd_fdss(sql7)
    dbtools.query_opd_fdss(sql8)
    dbtools.query_opd_fdss(sql9)
    dbtools.query_opd_fdss(sql10)

    sql11 = "update g_fs_data_original set fs_type_code_sort = 1 where fs_type_code = 'BS';"
    sql12 = "update g_fs_data_original set fs_type_code_sort = 2 where fs_type_code = 'IS';"
    sql13 = "update g_fs_data_original set fs_type_code_sort = 3 where fs_type_code = 'CF';"
    sql14 = "update g_fs_data_original set fs_type_code_sort = 4 where fs_type_code = 'OCI';"
    dbtools.query_opd_fdss(sql11)
    dbtools.query_opd_fdss(sql12)
    dbtools.query_opd_fdss(sql13)
    dbtools.query_opd_fdss(sql14)
    print '数据状态更新完成'


def special_handling_subject(text):
    key = re.sub(r'\s', '', text.lower())
    key = re.sub(r""",|\||-|—|:|：|．|\*|\[|\]|\?|\.|\(|\)|/|#|&|'|\"|、|－|（|）|“|”|―|‖|~|，|！|¡|。|‛|‚|­|；|;|？""", '', key)
    key = re.sub('^其中', '', key)
    key = re.sub('^加', '', key)
    key = re.sub('附注$', '', key)
    discard_word = [
                    '((一)|(二)|(三)|(四)|(五)|(六)|(七)|(八)|(九)|(十))',
                    '(⒈|⒉|⒊|⒋|⒌)',
                    '(㈡|㈠)',
                    '(⑴|⑵|⑶|⑷|⑸|⑹|⑺|⑻|⑼|⑽|⑾|⑿|⒀|⒁|⒂|⒃|⒄|⒅|⒆|⒇)'
                    ]
    key = re.sub(r'\d', '', key)
    rule = tools.linkStr(discard_word, '|')
    key = re.sub(rule, '', key)
    key = re.sub('（）', '', key)
    return key


def special_handling_value(value):
    key = re.sub('#\|#|\)|）', '', value)
    # 2019/1/10需求
    key = re.sub(r'\(|（', '-', key)
    # 2019/1/10需求
    key = re.sub('人民币|元', '', key)
    return key


def get_company_leader(guid):
    sql = "select assigned_to from g_fs_data_original WHERE guid = '{}'".format(guid)
    person_result = dbtools.query_opd_fdss(sql)
    if person_result:
        return person_result[0][0]
    else:
        return 'notAssigned'
def get_company_leader_test(guid):
    sql = "select assigned_to from g_fs_data_original WHERE guid = '{}'".format(guid)
    person_result = dbtools.query_opd_fdss_test(sql)
    if person_result:
        return person_result[0][0]
    else:
        return 'notAssigned'

def delete_bf_push(guid):
    get_id_sql = "SELECT id from g_fs_data_original WHERE guid='{}';".format(guid)
    original_guid = dbtools.query_opd_fdss(get_id_sql)
    dbtools.query_opd_fdss(get_id_sql)
    if original_guid:
        fs_id = original_guid[0][0]
        delete_detail = "DELETE from g_fs_data_original_detail WHERE fs_original_id='{}';".format(fs_id)
        delete_opdst = "DELETE FROM g_fs_data_original_detail_in_opd_st WHERE fs_original_id='{}';".format(fs_id)
        delete_check_result = "DELETE FROM g_fs_data_quality_management_check_result WHERE fs_data_original_id='{}';".format(fs_id)
        delete_original = "DELETE from g_fs_data_original WHERE guid='{}';".format(guid)

        # 推送前删除数据
        dbtools.query_opd_fdss(delete_detail)
        dbtools.query_opd_fdss(delete_opdst)
        dbtools.query_opd_fdss(delete_check_result)
        dbtools.query_opd_fdss(delete_original)
        print guid+'deleted'

def delete_bf_push_test(guid):
    get_id_sql = "SELECT id from g_fs_data_original WHERE guid='{}';".format(guid)
    original_guid = dbtools.query_opd_fdss_test(get_id_sql)
    dbtools.query_opd_fdss_test(get_id_sql)
    if original_guid:
        fs_id = original_guid[0][0]
        delete_detail = "DELETE from g_fs_data_original_detail WHERE fs_original_id='{}';".format(fs_id)
        delete_opdst = "DELETE FROM g_fs_data_original_detail_in_opd_st WHERE fs_original_id='{}';".format(fs_id)
        delete_check_result = "DELETE FROM g_fs_data_quality_management_check_result WHERE fs_data_original_id='{}';".format(fs_id)
        delete_original = "DELETE from g_fs_data_original WHERE guid='{}';".format(guid)

        # 推送前删除数据
        dbtools.query_opd_fdss_test(delete_detail)
        dbtools.query_opd_fdss_test(delete_opdst)
        dbtools.query_opd_fdss_test(delete_check_result)
        dbtools.query_opd_fdss_test(delete_original)
        print guid+'deleted'

def get_disclosure_date_result(report):
    disclosure_date_sql = "SELECT disclosure_date FROM `financial_statement_index` WHERE report_id = '{}'".format(
        report)
    disclosure_date_result = dbtools.query_common(disclosure_date_sql)
    disclosure_date_result = disclosure_date_result[0][0]
    return disclosure_date_result


def get_doc_local_path(report):
    doc_local_path_sql = "SELECT doc_local_path FROM `financial_statement_index` WHERE report_id = '{}'".format(report)
    doc_local_path_result = dbtools.query_common(doc_local_path_sql)
    doc_local_path = doc_local_path_result[0][0]
    return doc_local_path


def get_doc_source_url(report):
    doc_source_url_sql = "SELECT doc_source_url FROM `financial_statement_index` WHERE report_id = '{}'".format(report)
    doc_source_url_result = dbtools.query_common(doc_source_url_sql)
    doc_source_url = doc_source_url_result[0][0]
    return doc_source_url

def get_fs_id_result(guid):
    fs_id_sql = "SELECT id from g_fs_data_original where guid='{}'".format(guid)  # 新的id
    fs_id_result = dbtools.query_opd_fdss(fs_id_sql)
    fs_id_result = fs_id_result[0][0]
    return fs_id_result

def get_fs_id_result_test(guid):
    fs_id_sql = "SELECT id from g_fs_data_original where guid='{}'".format(guid)  # 新的id
    fs_id_result = dbtools.query_opd_fdss_test(fs_id_sql)
    fs_id_result = fs_id_result[0][0]
    return fs_id_result



if __name__ == '__main__':
    pass

