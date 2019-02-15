# -*- coding: UTF-8 -*-
import datetime
import logging
import re
import traceback
import sys
sys.path.extend(['/home/code_lli/dataparser/'])

from algorithm.common import tools
from algorithm.financial_statement_html import fs_html_tools, fs_html_check
from algorithm.financial_statement_html.fs_html_info_recognize import recognize_info


def process(para, istest=False):
    begin_time = datetime.datetime.now()
    logging.basicConfig(filename="./log/fs_html.log", level=logging.DEBUG, format='[%(asctime)s] %(message)s')
    logging.info('[BEGIN] ' + para.reportid + ' ' + begin_time.strftime('%Y-%m-%d %H:%M:%S'))

    p_country, p_company, p_reportid = para.countryid, para.companyid, para.reportid
    try:
        # 获取原始文件数据
        source_df = fs_html_tools.get_source_data(p_country, p_company, p_reportid)

        # 通过table标签，获取table_box
        table_box = fs_html_tools.get_table_box(source_df)

        # 通过标题库生成财报对象
        statement_box = fs_html_tools.get_statement_box(source_df, table_box, para)

        # 信息识别： 货币、数量单位、时间(年份、季度)、合并与否
        recognize_info(p_reportid, statement_box)

        # 检查
        fs_html_check.process(p_reportid, statement_box)

        # 获取所有表格数据，生成待输出数据
        all_table_data = fs_html_tools.get_all_table_data(statement_box, para)

        # 输出文件
        fs_html_tools.output_data(all_table_data, para, istest)

        if istest:
            return statement_box

        logging.info('[-END-] ' + para.reportid + ' [COST] ' + str(datetime.datetime.now() - begin_time))

    except Exception as e:
        logging.info('[EXCPT] ' + para.reportid + ' [COST] ' + str(datetime.datetime.now() - begin_time))
        if not istest:
            excepttext = traceback.format_exc()
            print p_reportid + '\n' + excepttext
            excepttext = re.sub('\n', ' ', excepttext)
            excepttext = re.sub('\"', '\'', excepttext)
            tools.updatePDFStatus(p_country, p_company, p_reportid, -30, excepttext, e.message)
        else:
            return str(e.message)


if __name__ == '__main__':
    from algorithm.common import configManage, dbtools
    from algorithm.common.para import Para
    reload(sys)
    sys.setdefaultencoding('utf-8')
    configManage.initConfig()
    # sam100
    reportids = ['USA1624847104851', 'USA1329276094250', 'USA1356873897243', 'USA1419120073021', 'USA1468699962956', 'USA1120328884161', 'USA1214669679552', 'USA1152328436536', 'USA1236717017183', 'USA1786701521226', 'USA1696630692470', 'USA1172629469208', 'USA1773807747867', 'USA1382597730911', 'USA1019961300766', 'USA1356866862263', 'USA1551064961626', 'USA1220079799625', 'USA1381330200388', 'USA1444905662887', 'USA1937980795944', 'USA1464693472418', 'USA1577103603174', 'USA1842891393884', 'USA1782973233930', 'USA1539788207442', 'USA1386176968538', 'USA1772842386575', 'USA1597731020747', 'USA1242878780327', 'USA1783779453750', 'USA1526301009050', 'USA1491691809673', 'USA1420910958870', 'USA1381365301228', 'USA1733831205806', 'USA1022574904340', 'USA1780097047713', 'USA1631665749486', 'USA1079240268941', 'USA1943612071842', 'USA1180948868375', 'USA1476215965681', 'USA1237705237261', 'USA1780055696124', 'USA1672839083647', 'USA1223365724781', 'USA1491662951677', 'USA1306107728184', 'USA1819010130027', 'USA1811561790934', 'USA1768101540816', 'USA1631172228001', 'USA1832908552235', 'USA1763309112007', 'USA1079255478113', 'USA1227075136287', 'USA1531141592237', 'USA1743315072816', 'USA1059293325740', 'USA1159393499306', 'USA1745758002574', 'USA1775680758221', 'USA1315482756742', 'USA1491699657960', 'USA1123886971527', 'USA1754628405104', 'USA1817948163127', 'USA1786356466920', 'USA1264907686832', 'USA1427390066870', 'USA1381381253373', 'USA1456554331317', 'USA1123953707428', 'USA1434694874943', 'USA1345535569788', 'USA1212793262711', 'USA1088498830504', 'USA1011221281882', 'USA1006844411035', 'USA1276167303974', 'USA1188274420588', 'USA1153662418175', 'USA1708349869182', 'USA1283461080361', 'USA1019959528827', 'USA1059356033901', 'USA1795980877468', 'USA1400469045855', 'USA1400406223934', 'USA1772710113138', 'USA1551034882832', 'USA1569703570912', 'USA1570018202564', 'USA1746781658478', 'USA1804374369813', 'USA1001055921077', 'USA1501607414600', 'USA1488722289770', 'USA1053731425825']
    reportids = ['USA1081095011702']
    # coms20
    company_list = ['USA10471', 'USA10503', 'USA10530', 'USA10622', 'USA10661', 'USA11161', 'USA11238', 'USA11417', 'USA11536', 'USA11726', 'USA12453', 'USA12563', 'USA12793', 'USA12994', 'USA13455', 'USA13568', 'USA14646', 'USA15016', 'USA17447', 'USA17727']
    # ids
    sql = """select countryid,companyid,reportid,statusid,country_name,company_name,fiscal_year,season_type_code,history_status,data_mark,doc_path,doc_type,report_type,error_code from %s where report_type=1 and countryid in ('USA') and doc_type='html' and reportid in %s""" % (configManage.config['table']['status'], "('" + "','".join(reportids) + "')")
    # coms
    # sql = """select countryid,companyid,reportid,statusid,country_name,company_name,fiscal_year,season_type_code,history_status,data_mark,doc_path,doc_type,report_type,error_code from %s where report_type=1 and countryid in ('USA') and doc_type='html' and companyid < 'USA12000' ORDER BY companyid""" % (configManage.config['table']['status'])
    result = dbtools.query_pdfparse(sql)
    paras = []
    # offline
    # paras.append(Para(reportids[0][0:3], reportids[0][0:8], reportids[0], [3], [4], [5], [6], [7], [8], [9], [10], [11], [12]))
    for r in result:
        paras.append(Para(r[0], r[1], r[2], r[3], r[4], r[5], r[6], r[7], r[8], r[9], r[10], r[11], r[12]))
    for key, para in enumerate(paras):
        print para.reportid
        process(para)
        # if key == 0:
        #     break
