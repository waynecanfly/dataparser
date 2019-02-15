# -*- coding: UTF-8 -*-
import MySQLdb

from algorithm.common import configManage
import pandas as pd

def query_to_df_dps(sql):
    pdf_lib_ip = configManage.config['database']['pdfparser']['ip']
    pdf_lib_user = configManage.config['database']['pdfparser']['user']
    pdf_lib_password = configManage.config['database']['pdfparser']['password']
    pdf_lib_dbname = configManage.config['database']['pdfparser']['name']
    db = MySQLdb.connect(host=pdf_lib_ip, user=pdf_lib_user, passwd=pdf_lib_password, db=pdf_lib_dbname, port=3306,
                         charset='utf8')
    try:
        df = pd.read_sql(sql, db)
        return df
    except MySQLdb.IntegrityError:
        db.close()
        raise MySQLdb.IntegrityError
    except Exception:
        db.close()
        raise Exception

def query_pdfparse(sql):
    pdf_lib_ip = configManage.config['database']['pdfparser']['ip']
    pdf_lib_user = configManage.config['database']['pdfparser']['user']
    pdf_lib_password = configManage.config['database']['pdfparser']['password']
    pdf_lib_dbname = configManage.config['database']['pdfparser']['name']
    db = MySQLdb.connect(host = pdf_lib_ip, user = pdf_lib_user, passwd = pdf_lib_password, db = pdf_lib_dbname, port = 3306,charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        db.commit()
        db.close()
        return data
    except MySQLdb.IntegrityError:
        db.close()
        raise MySQLdb.IntegrityError
    except Exception:
        print '[SQL_ERROR]: ' + sql
        configManage.logger.error('[SQL_ERROR]: ' + sql)
        db.close()
        raise Exception

def query_opd_fdss(sql):
    common_ip = configManage.config['database']['opd_fdss']['ip']
    common_user = configManage.config['database']['opd_fdss']['user']
    common_password = configManage.config['database']['opd_fdss']['password']
    common_dbname = configManage.config['database']['opd_fdss']['name']
    db = MySQLdb.connect(host=common_ip, user=common_user, passwd=common_password, db=common_dbname, port=3306, charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        db.commit()
        db.close()
        return data
    except Exception:
        db.close()
        raise Exception

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
        db.commit()
        db.close()
        return data
    except Exception:
        db.close()
        raise Exception


def query_common(sql):
    common_ip = configManage.config['database']['common']['ip']
    common_user = configManage.config['database']['common']['user']
    common_password = configManage.config['database']['common']['password']
    common_dbname = configManage.config['database']['common']['name']

    db = MySQLdb.connect(host = common_ip, user = common_user, passwd = common_password, db = common_dbname, port = 3306,charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        db.commit()
        db.close()
        return data
    except Exception:
        db.close()
        raise Exception


def deleteDataByReportID(tablename, reportid):
    pdf_lib_ip = configManage.config['database']['pdfparser']['ip']
    pdf_lib_user = configManage.config['database']['pdfparser']['user']
    pdf_lib_password = configManage.config['database']['pdfparser']['password']
    pdf_lib_dbname = configManage.config['database']['pdfparser']['name']

    sql = "delete from {tablename} where reportid='{reportid}'"
    sql = sql.format(tablename=tablename, reportid=reportid)

    db = MySQLdb.connect(host=pdf_lib_ip, user=pdf_lib_user, passwd=pdf_lib_password, db=pdf_lib_dbname, port=3306, charset='utf8')
    try:
        cursor = db.cursor()
        result = cursor.execute(sql)
        data = cursor.fetchall()
        db.commit()
        db.close()
        return data
    except Exception:
        db.close()
        raise Exception


def query_pdfparse_overlap_by_reportid(sql,tablename, reportid):
    pdf_lib_ip = configManage.config['database']['pdfparser']['ip']
    pdf_lib_user = configManage.config['database']['pdfparser']['user']
    pdf_lib_password = configManage.config['database']['pdfparser']['password']
    pdf_lib_dbname = configManage.config['database']['pdfparser']['name']


    db = MySQLdb.connect(host = pdf_lib_ip, user = pdf_lib_user, passwd = pdf_lib_password, db = pdf_lib_dbname, port = 3306,charset='utf8')
    try:
        cursor = db.cursor()
        # delete first
        deletesql = "delete from {tablename} where reportid = '{reportid}'"
        deletesql = deletesql.format(tablename=tablename, reportid=reportid)
        cursor.execute(deletesql)

        # query
        result = cursor.execute(sql)
        data = cursor.fetchall()
        db.commit()
        db.close()
        return data
    except Exception:
        db.close()
        raise Exception
