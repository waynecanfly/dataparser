# -*- coding:utf-8 -*-

class Para():
    def __init__(self, countryid, companyid, reportid, statusid, country_name, company_name, fiscal_year,
                 season_type_code, history_status, data_mark, doc_path, doc_type, report_type, error_code='', sector_code='', sector_name=''):
        self.countryid = countryid
        self.companyid = companyid
        self.reportid = reportid
        self.statusid = statusid
        self.country_name = country_name
        self.company_name = company_name
        self.fiscal_year = fiscal_year
        self.season_type_code = season_type_code
        self.history_status = history_status
        self.data_mark = data_mark
        self.doc_path = doc_path
        self.doc_type = doc_type
        self.report_type = report_type
        self.error_code = error_code
        self.sector_code = sector_code
        self.sector_name = sector_name
