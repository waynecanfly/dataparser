# -*- coding:utf-8 -*-
import csv
import re
import sys

from algorithm.common import tools, configManage, dbtools
from algorithm.common_tools_pdf import header_match_tools
from containers.block import Block
from containers.line import Line


def output(table_box, p_reportid, p_country, p_company, isTest):
    basePath  = configManage.config['location']['pdf_table_new']
    if not isTest:
        savepath = basePath + "/p_country={p_country}/p_company={p_company}/"
        savepath = savepath.format(p_country=p_country, p_company=p_company)
    else:
        savepath = "./test_result"

    tools.makeDirs(savepath)

    with file(savepath + '/' + p_reportid + '.csv', 'wb') as outputFile:
        writer = csv.writer(outputFile)
        for table in table_box:
            for line in table.output_value_box:
                # print str(tools.linkStr(line, ',')).encode('utf-8')
                writer.writerow(line)


def outputMarkSource(p_country, p_company, p_reportid, tablebox):

    valuebox = []
    recognizedInfoBox = []
    for table in tablebox:
        # 标记数据
        for unit in table.tableunitbox:
            value = """("{countryid}", "{companyid}", "{reportid}", "{tabletype}",{pagenum},"{textblock}",{lineindex},{columnindex})"""
            value = value.format(countryid=p_country, companyid=p_company, reportid=p_reportid, tabletype=table.tabletype, pagenum=table.pageNum,
                           textblock=re.sub("\"", '', unit.text + ' ' + unit.extraText), lineindex=unit.lineIndex, columnindex=unit.columnIndex)
            valuebox.append(value)
        # 已识别信息
        for info in table.baseInfoRecoginzedLib:
            infoStr = """("{countryid}", "{companyid}", "{reportid}", "{tabletype}", "{original_text}","{currency}","{measureunit}",{match_type})"""
            infoStr = infoStr.format(countryid=p_country, companyid=p_company, reportid=p_reportid,tabletype=table.tabletype,
                                     original_text=info[0],
                                     currency=info[1],
                                     measureunit=info[2],
                                     match_type=info[3])
            recognizedInfoBox.append(infoStr)



    values = tools.linkStr(valuebox, ',')
    markDataSql ="insert into opd_pdf_info_mark(countryid,companyid,reportid,tabletype,pagenum,textblock,lineindex,columnindex) values {values}"
    markDataSql =  markDataSql.format(values=values)
    dbtools.query_pdfparse_overlap_by_reportid(markDataSql, 'opd_pdf_info_mark', p_reportid)

    if recognizedInfoBox:
        recognizedInfos = tools.linkStr(recognizedInfoBox, ',')
        infoSql = "insert into opd_pdf_identified_info(countryid,companyid,reportid,tabletype,original_text,currency,measureunit, match_type) values {values}"
        infoSql = infoSql.format(values=recognizedInfos)
        dbtools.query_pdfparse_overlap_by_reportid(infoSql, 'opd_pdf_identified_info', p_reportid)

# discard
def outputTableTocsv(table_box, p_country, p_company, p_reportid):
    savepath = "C:/workspace/pdf_table_csv/{p_country}/{p_company}/{p_reportid}"
    savepath = savepath.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)
    tools.makeDirs(savepath)

    for tIndex, t in enumerate(table_box):
        output = file(savepath + '/' + t.tableid + re.sub('\/', '|', re.sub(',', '|', t.title[0].text)) + '.csv', 'w+')

        for b in t.title + t.unkonw:
            titleStr = '{text}\n'
            titleStr = titleStr.format(text=re.sub(',', '|', b.text))
            output.write(titleStr)


        for l in t.header + t.body:
            line_text = ''
            index = 0
            for i, b in enumerate(l.blockbox):
                while 1:
                    if index == b.columnIndex or index > 20:
                        break
                    else:
                        line_text = line_text + ','
                        index = index + 1
                line_text = line_text + re.sub(',', '|', b.text) + ','
            output.write(line_text + '\n')
        output.close()

def output_valid_page_box(valid_page_box, p_country, p_company, p_reportid):
    savepath_line = "/home/lee/workspace/pdfcsv3/pdf_manual_before/{p_country}/{p_company}/{p_reportid}"
    savepath_line = savepath_line.format(p_country=p_country, p_company=p_company, p_reportid=p_reportid)
    tools.makeDirs(savepath_line)

    for page in valid_page_box:
        output_block = file(savepath_line + '/' + str(page.pageNum+1) + '.csv', 'w+')
        for l in page.linebox:
            for b in l.blockbox:
                bStr = '{pageNum},{text},{x0},{y0},{x1},{y1},{direction},{fontsize},{lineIndex},{type},{top_gap},{bottom_gap},{left_gap},{right_gap},{step},\n'
                bStr = bStr.format(pageNum=b.pageNum, text=re.sub(',','#|#',b.text), x0=b.x0, y0=b.y0, x1=b.x1, y1=b.y1,
                                   direction=b.direction,
                                   top_gap=b.top_gap, bottom_gap=b.bottom_gap, left_gap=b.left_gap,
                                   right_gap=b.right_gap,
                                   step = 0,
                                   fontsize=b.fontsize, type=b.type, lineIndex=b.lineIndex)
                output_block.write(bStr)
        output_block.close()

def pagefilter(page, LINE_BLOCK_NUM_THRESHOLD=2):
    if page.pageNum == 88:
        pass
    linebox = page.linebox
    counter = 0
    begin = -1
    end = -1
    for l in linebox:
        if len(l.blockbox) >= LINE_BLOCK_NUM_THRESHOLD:
            if begin == -1:
                begin = l.lineIndex
            elif ishasDigit(l.blockbox):
                counter = counter + 1
                end = l.lineIndex
    if begin == -1 or end == -1 or counter < 1:
        return False
    else:
        return True

def pagefilter2(page):
    if len(page.linebox)>0:
        return True
    else:
        return False


def ishasDigit(blockbox):
    legaltimes = 0
    for b in blockbox:
        if b.type in ['digit', 'placeholder', 'NumOrder', 'currency']:
            legaltimes = legaltimes + 1
    return legaltimes >= 1


def getPatterns():
    ps_box = []
    headers = dbtools.query_pdfparse("select distinct orig_text, identity from opd_structure_pattern")
    for h in headers:
        text = header_match_tools.getMatchText(h[0].encode('utf-8'))
        identity = h[1]
        ps_box.append({'text':text, 'identity': identity})
    return ps_box


def getSourceData(datapath):
    blockBox = []
    with open(datapath, 'rb') as f:
        content = csv.reader(f)
        for data in content:
            b = Block(data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7],data[8],
                              data[9], data[10], data[11], data[12], data[13], data[14])

            # if b.pageNum == 15:
            #     print b.text

            blockBox.append(b)

    return blockBox


def lineConverge(blockBox):
    linebox_total = []
    total_lineindex = 0
    curLine = Line(blockBox[0], total_lineindex)

    for i in range(1, len(blockBox)):
        b = blockBox[i]
        if curLine.add(b) == 'reject':
            linebox_total.append(curLine)
            total_lineindex += 1
            curLine = Line(b, total_lineindex)
    linebox_total.append(curLine)
    return linebox_total


def filterPage(pagebox):
    valid_page_box = [page for page in pagebox if pagefilter2(page)]
    if len(valid_page_box) == 0:
        raise Exception('NoTableException')
    else:
        return valid_page_box

def filterIllegalTable(table_box):
    valid_table_box = [table for table in table_box if len(table.body) > 0 and table.title and table.table_type in ['BS', 'IS', 'CF']]
    if len(valid_table_box) == 0:
        raise Exception('statement can not found overall, found quantity: 0')
    else:
        return valid_table_box

def genPageReferline(linebox):
    referline = {}
    for i,b in enumerate(linebox[0].blockbox):
        referline[(i+1)*80000000] = [b.x0, b.x1]

    for line in linebox:
        for block in line.blockbox:
            rIndexbox = sorted(referline.keys())
            for i, rIndex in enumerate(rIndexbox):
                range = referline[rIndex]
                if block.x1 <= range[0]:
                    newIndex = (0 + rIndex)/2 if i == 0 else (rIndexbox[i-1] + rIndex)/2
                    referline[newIndex] = [block.x0, block.x1]
                    break
                elif not (block.x1<=range[0] or block.x0>=range[1]):
                    newx0 = block.x0 if block.x0>range[0] else range[0]
                    newx1 = block.x1 if block.x1<range[1] else range[1]
                    referline[rIndex] = [newx0, newx1]
                    break
                elif block.x0>range[1] and i+1 == len(rIndexbox):
                    newIndex = rIndex + 80000000
                    referline[newIndex] = [block.x0, block.x1]
                    break

    newRferline = {}
    indexs = sorted(referline.keys())
    for i, index in enumerate(indexs):
        newRferline[i] = referline[index]
    return newRferline

def genPageColumnIndex(page):
    # gen referline
    referline = genPageReferline(page.linebox)
    referIndex = sorted(referline.keys())

    # gen column index
    for line in page.linebox:
        for block in line.blockbox:
            isMatch = False
            for rIndex in referIndex:
                range = referline[rIndex]
                if not (block.x1<range[0] or block.x0>range[1]):
                    isMatch = True
                    block.columnIndex = rIndex
                    break
            if not isMatch:
                pass


def outputIdentifiedTableInfo(p_country, p_company, p_reportid, table):
    value = """("{countryid}", "{companyid}", "{reportid}", "{tabletype}", {tablepage})"""
    value = value.format(countryid=p_country, companyid=p_company, reportid=p_reportid, tabletype=table.table_type,tablepage=table.pageNum)
    sql = "insert into opd_pdf_identified_table(countryid,companyid,reportid,tabletype,tablepage) values" + value
    dbtools.query_pdfparse(sql)

def outputMarkTableToMysql(p_country, p_company, p_reportid, table):
    valuebox = []
    markvalue = """("{p_country}", "{p_company}", "{p_reportid}", {pagenum}, "{textblock}", {lineindex}, {columnindex}, "{x0}", "{y0}", "{x1}", "{y1}", {fontsize}, {istitle}, "{tabletype}", {isheader}, "{headertype}")"""
    markvalue = markvalue.format(p_country=p_country,
                         p_company=p_company,
                         p_reportid=p_reportid,
                         pagenum=table.page.pageNum,
                         textblock=table.table_type + ' Found',
                         lineindex=0,
                         columnindex=0,
                         x0=0,
                         y0=0,
                         x1=0,
                         y1=0,
                         fontsize=0,
                         istitle=0,
                         tabletype='',
                         isheader=0,
                         headertype=0
                         )
    valuebox.append(markvalue)
    headerIndex = sorted(table.index_header_map.keys())
    for i,index in enumerate(headerIndex):
        header = table.index_header_map[index]
        value = """("{p_country}", "{p_company}", "{p_reportid}", {pagenum}, "{textblock}", {lineindex}, {columnindex}, "{x0}", "{y0}", "{x1}", "{y1}", {fontsize}, {istitle}, "{tabletype}", {isheader}, "{headertype}")"""
        value = value.format(p_country=p_country,
                                     p_company=p_company,
                                     p_reportid=p_reportid,
                                     pagenum=table.page.pageNum,
                                     textblock=header.text + '\n' + header.extraInfo,
                                     lineindex=1,
                                     columnindex=i,
                                     x0=0,
                                     y0=0,
                                     x1=0,
                                     y1=0,
                                     fontsize=0,
                                     istitle=0,
                                     tabletype='',
                                     isheader=0,
                                     headertype=0
                                     )
        valuebox.append(value)
    valueStr = tools.linkStr(valuebox, ',')
    sql = 'insert into opd_pdf_structure_mark(countryid,companyid,reportid,pagenum,textblock,lineindex,columnindex,x0,y0,x1,y1,fontsize,istitle,tabletype,isheader,headertype) values ' + valueStr
    dbtools.query_pdfparse(sql)

def outputPageToMysql(p_country, p_company, p_reportid, page):
    valuebox = []
    for line in page.linebox:
        for block in line.blockbox:
            text = re.sub('\n', ' ', block.text)
            text = re.sub('\"', '\'', text)
            text = text.replace('\\', '')
            try:
                columnindex = block.columnIndex
            except:
                try:
                    columnindex = block.columnIndexs[0]
                except:
                    columnindex = 0

            value = """("{p_country}", "{p_company}", "{p_reportid}", {pagenum}, "{textblock}", {lineindex}, {columnindex}, "{x0}", "{y0}", "{x1}", "{y1}", {fontsize}, {istitle}, "{tabletype}", {isheader}, "{headertype}")"""
            value = value.format(p_country=p_country,
                                 p_company=p_company,
                                 p_reportid=p_reportid,
                                 pagenum=block.pageNum,
                                 textblock=text,
                                 lineindex=block.lineIndex,
                                 columnindex=columnindex,
                                 x0=block.x0,
                                 y0=block.y0,
                                 x1=block.x1,
                                 y1=block.y1,
                                 fontsize=block.fontsize,
                                 istitle=0,
                                 tabletype='',
                                 isheader=0,
                                 headertype=0
                                 )
            valuebox.append(value)
    valueStr = tools.linkStr(valuebox, ',')
    sql = 'insert into opd_pdf_structure_mark(countryid,companyid,reportid,pagenum,textblock,lineindex,columnindex,x0,y0,x1,y1,fontsize,istitle,tabletype,isheader,headertype) values ' + valueStr
    dbtools.query_pdfparse(sql)



def outputTableStructureMarkSource(p_country, p_company, p_reportid, valid_page_box, valid_table_box):
    pagenum_table_map = {}
    for table in valid_table_box:
        if table.page.pageNum in pagenum_table_map:
            pagenum_table_map[table.page.pageNum].append(table)
        else:
            pagenum_table_map[table.page.pageNum] = [table]

    valid_page_box_3 = [page for page in valid_page_box if pagefilter(page, 3)]
    valid_page_box = valid_page_box_3 if valid_page_box_3 else valid_page_box

    # delete data
    dbtools.deleteDataByReportID('opd_pdf_structure_mark', p_reportid)


    for page in valid_page_box:
        # judge if is in valid_table_box
        if page.pageNum==88:
            pass

        if page.pageNum in pagenum_table_map and len(pagenum_table_map[page.pageNum]) == 1:
            table = pagenum_table_map[page.pageNum][0]
            outputMarkTableToMysql(p_country, p_company, p_reportid, table)
            outputIdentifiedTableInfo(p_country, p_company, p_reportid, table)
        else:
            genPageColumnIndex(page)
            # out put page to mysql
            outputPageToMysql(p_country, p_company, p_reportid, page)

def headerIsTheSame(table, lasttable):
    for index in table.index_header_map:
        header = table.index_header_map[index]
        if header.identity != '':
            isFound = False
            curHeaderText = re.sub('\s', '',header.text).lower()
            for lastIndex in lasttable.index_header_map:
                lastheader =  lasttable.index_header_map[lastIndex]
                compareHeaderText =  re.sub('\s', '',lastheader.text).lower()
                if curHeaderText == compareHeaderText:
                    isFound = True
                    break
            if not isFound:
                return False
    return True



def backfillTitle(table_box):
    # 回填规则，无titlte的表查看同一页或者上一页中是否有合法有效的表，有的话对比一下两者的header是否一样，如果header是一样的，那就对title进行回填
    pagenum_table_map = {}
    for table in table_box:
        if table.page.pageNum in pagenum_table_map:
            pagenum_table_map[table.page.pageNum].append(table)
        else:
            pagenum_table_map[table.page.pageNum] = [table]

    pageNums = sorted(pagenum_table_map.keys())

    for i, pageNum in enumerate(pageNums):
        pagetables = pagenum_table_map[pageNum]
        for k, table in enumerate(pagetables):
            if not table.title:  # 无title
                if len(pagetables) > 1 and k != 0: # 同一页中有多个表，且该表不是排在第一
                    if pagetables[0].title and pagetables[0].table_type in ['BS', 'IS', 'CF'] and headerIsTheSame(table,pagetables[0]): # 取第一个有title并且是目标表的表
                        table.title =  pagetables[0].title
                        table.table_type =  pagetables[0].table_type
                elif i != 0 and (pageNum-pageNums[i-1])==1: # 往上一页找
                    lastPageFirstTable = pagenum_table_map[pageNums[i-1]][0]  #取上一页第一个并且是目标表的title作为title
                    if  lastPageFirstTable.title and lastPageFirstTable.table_type in ['BS', 'IS', 'CF'] and headerIsTheSame(table,lastPageFirstTable):
                        table.title =  lastPageFirstTable.title
                        table.table_type =  lastPageFirstTable.table_type

def getJudgePureText(table):
    t_text = ''
    for t_line in table.title:
        for t_block in t_line.blockbox:
            # if t_block.identity == 'title':
            t_text = t_text + t_block.text

    return re.sub('\s', '', t_text)


# def judgeIfHadFoundAllAimTable(valid_table_box):
#     # 备忘： 后续可能需要加上时间跨度的判断，如果某个表有某个时间跨度，那么所有类型的报表是否都有这个时间跨度的表？
#     consolidatedKeyWord = ['consolidated','合并']
#     standaloneKeyWord = ['standalone','母公司']
#
#     for table in valid_table_box:
#         pureTitle = getJudgePureText(table)
#         for standWord in standaloneKeyWord:
#             if standWord in pureTitle:
#                 table.isConsolidated = 0
#                 break
#         for conWord in consolidatedKeyWord:
#             if conWord in pureTitle:
#                 table.isConsolidated = 1
#                 break
#
#
#     consolidatedBox = set()
#     standaloneBox = set()
#     unknowBox = set()
#     # 分类
#     for table in valid_table_box:
#         if table.isConsolidated == 1:
#             consolidatedBox.add(table.table_type)
#         elif table.isConsolidated == -1:
#             unknowBox.add(table.table_type)
#         elif table.isConsolidated == 0:
#             standaloneBox.add(table.table_type)
#     #  判断
#     if len(consolidatedBox) == 3:
#         return True
#     elif len(consolidatedBox) == 0 and len(unknowBox) == 3:
#         return False  # 表示表找全了，但是没有独立报表和母公司报表之分
#     else:
#         if len(consolidatedBox) == 0 and len(unknowBox) == 0:
#             raise StatementNotFound('No report be found')
#         else:
#             raise StatementNotAllFound('Not all report be found')







def isInNoTitleHeader(noTitleTableHeaderRange, pageNum, lineIndex):
    headerRanges = noTitleTableHeaderRange.get(pageNum, False)
    if headerRanges:
        return lineIndex >= headerRanges[0] and lineIndex <= headerRanges[1]
    else:
        return False

def structureMarkIsFull():
    MARK_CAPACITY = 60 # 待标记的数量最多只能有60个
    checksql = 'select count(*) from {table} where statusid = 33'
    checksql = checksql.format(table=configManage.config['table']['status'])
    result = dbtools.query_pdfparse(checksql)
    return int(result[0][0]) >= MARK_CAPACITY

def same_kind_table_filter(tablebox):
    # 现阶段判断标准还过于粗糙，最起码要加上科目上的判断， 后续需要重构
    # 距离超过6页，则认为该表与其它表不是一个集团
    group_distance_thr = 6
    # tabletype_map = {}  # 暂时用不上
    tableGroup = []
    for table in tablebox:
        if len(tableGroup) == 0:
            tableGroup.append([table])
        elif abs(table.pageNum - tableGroup[-1][-1].pageNum) < group_distance_thr:
            tableGroup[-1].append(table)
        else:
            tableGroup.append([table])

    # 如果某一个table组中包含了所有目标报表的话，丢弃其它组的报表
    aimset = {'BS', 'IS', 'CF'}
    for i, group in enumerate(tableGroup):
        tableTypeSet = set()
        for t in group:
            tableTypeSet.add(t.table_type)
        if aimset.issubset(tableTypeSet):
            return group
    return tablebox



def getPageMap(pagebox):
    pagemap = {}
    for p in pagebox:
        pagemap[p.pageNum] = p
    return pagemap


def getCompanyName(companyid):
    sql = "select name_origin from company where code='%s';"
    sql = sql % (companyid)
    result = dbtools.query_common(sql)
    company_name = result[0][0] if len(result) > 0 else ''
    return company_name


def data_counter():

    header = '公司ID,公司名,上市日期,2007,2008,,,,2009,,,,2010,,,,2011,,,,2012,,,,2013,,,,2014,,,,2015,,,,2016,,,,2017,,,,2018,,,,\n,,,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,Q1,HF,Q3,FY,\n'
    #
    # for i in range(0, 11):
    #     header = header + 'Q1,HF,Q3,FY,'
    #     init += 1

    # 0 无报表
    # -1 未下载
    # -2 处理中
    # 1 处理完成
    # 2 处理完成且已经推送到fdss
    # 3 处理完成，fdss标记成功
    # 4 处理完成，fdss标记失败

    value_box = []
    re_box = []
    lost_box = []
    lost_box_new = []

    statu_map = {}
    checksql = "select companyid, fiscal_year, season_type_code, statusid from opd_pdf_status where countryid='CHN' and statusid not in (32)"
    checkresult = dbtools.query_pdfparse(checksql)
    for cr in checkresult:
        key = cr[0] + '_' + cr[1] + '_' + cr[2]
        if key not in statu_map:
            statu_map[key] = [cr[3]]
        else:
            statu_map[key].append(cr[3])

    # sql = "select code, name_origin, ipo_date, security_code, exchange_market_code from company where country_code_listed='CHN' and code not in ('CHN10002', 'CHN10187', 'CHN10012', 'CHN10031', 'CHN10037', 'CHN12161', 'CHN12595', 'CHN10434', 'CHN10193', 'CHN12477', 'CHN12514', 'CHN10163', 'CHN10150', 'CHN10087', 'CHN12049', 'CHN12772', 'CHN10262', 'CHN10276', 'CHN10001', 'CHN10282', 'CHN12521', 'CHN10778', 'CHN10230', 'CHN12024', 'CHN10130', 'CHN12473', 'CHN12181', 'CHN10132', 'CHN10194', 'CHN12325', 'CHN12442', 'CHN12138', 'CHN10025', 'CHN10279', 'CHN10103', 'CHN10005', 'CHN10115', 'CHN10113', 'CHN10407', 'CHN12048', 'CHN10350', 'CHN12224', 'CHN12833', 'CHN12401', 'CHN10027', 'CHN10044', 'CHN10010', 'CHN10242', 'CHN12037', 'CHN10598', 'CHN12086', 'CHN12580', 'CHN13319', 'CHN12041', 'CHN10154', 'CHN12493', 'CHN10673', 'CHN10218', 'CHN12025', 'CHN10158', 'CHN10749', 'CHN12713', 'CHN12575', 'CHN12062', 'CHN12806', 'CHN10035', 'CHN10202', 'CHN12206', 'CHN10077', 'CHN12844', 'CHN10400', 'CHN12644', 'CHN12677', 'CHN12421', 'CHN12155', 'CHN12540', 'CHN10226', 'CHN10374', 'CHN12479', 'CHN10307', 'CHN12520', 'CHN12317', 'CHN10197', 'CHN12919', 'CHN12045', 'CHN12505', 'CHN12831', 'CHN12804', 'CHN12272', 'CHN12670', 'CHN12152', 'CHN12365', 'CHN12311', 'CHN12072', 'CHN12562', 'CHN12504', 'CHN12395', 'CHN10382', 'CHN12863', 'CHN12492', 'CHN10318', 'CHN12615', 'CHN12100', 'CHN12210', 'CHN12015', 'CHN12306', 'CHN12591', 'CHN12018', 'CHN10542', 'CHN10301', 'CHN12631', 'CHN12584', 'CHN12270', 'CHN12057', 'CHN10206', 'CHN10036', 'CHN12856', 'CHN12527', 'CHN10362', 'CHN12194', 'CHN12787', 'CHN12246', 'CHN10286', 'CHN12910', 'CHN12852', 'CHN12186', 'CHN10039', 'CHN12651', 'CHN10612', 'CHN12552', 'CHN12507', 'CHN12657', 'CHN10267', 'CHN12267', 'CHN12541', 'CHN10227', 'CHN10135', 'CHN10481', 'CHN10246', 'CHN12525', 'CHN12568', 'CHN12205', 'CHN12509', 'CHN12559', 'CHN13331', 'CHN10709', 'CHN12135', 'CHN12434', 'CHN12285', 'CHN12925', 'CHN13324', 'CHN10611', 'CHN12142', 'CHN10769', 'CHN13317', 'CHN12139', 'CHN12060', 'CHN10447', 'CHN10607', 'CHN10449', 'CHN12880', 'CHN12764', 'CHN12841', 'CHN12828', 'CHN12871', 'CHN10964', 'CHN12888', 'CHN12848', 'CHN12904', 'CHN12835', 'CHN11133', 'CHN11136', 'CHN10071', 'CHN11196', 'CHN12815', 'CHN12730', 'CHN12811', 'CHN10465', 'CHN12801', 'CHN12724', 'CHN12924', 'CHN12727', 'CHN12798', 'CHN11252', 'CHN13058', 'CHN12723', 'CHN11261', 'CHN11291', 'CHN12726', 'CHN12840', 'CHN12823', 'CHN12896', 'CHN12894', 'CHN13460', 'CHN13351', 'CHN13388', 'CHN13286', 'CHN13300', 'CHN13345') order by ipo_date"
    sql = "select code, name_origin, ipo_date, security_code, exchange_market_code from company where country_code_listed='CHN' order by ipo_date"


    sector_map = {}
    sc_sql = "select distinct code, sector_code from g_company where country_code_origin = 'CHN'"
    result = dbtools.query_pdfparse(sc_sql)
    for r in result:
        sector_map[r[0]] = r[1]


    result = dbtools.query_common(sql)
    init = 2007
    for r in result:
        company_code = r[0]
        company_name = r[1]
        security_code = r[3]
        exchange_market_code = r[4]
        this_company = '{},{},{},'.format(r[0], r[1], r[2])
        try:
            ipo_year = int(str(r[2]).split('-')[0])
            ipo_month = int(str(r[2]).split('-')[1])
        except:
            ipo_year = 1949
            ipo_month = 1
        for i in range(0, 12):
            year = init + i
            if year < ipo_year:
                if year == 2007:
                    this_company = this_company + '0,'
                else:
                    this_company = this_company + '0,0,0,0,'
                continue
            this_year = ''
            for season in ['Q1', 'Q2', 'Q3', 'FY']:
                if year == 2007 and season != 'FY':
                    continue
                checkKey = str(r[0]) + '_' + str(year) + '_' + str(season)
                checkValue = statu_map.get(checkKey, None)
                    # 公司表中存在状态表中不存在
                if checkValue is None:
                    if year==2018 and season == 'FY':
                        this_year = this_year + '0,'
                    elif ipo_year < year or (season == 'Q1' and ipo_month < 3) or (season == 'Q2' and ipo_month < 6) or (season == 'Q3' and ipo_month < 9) or (season == 'FY'):
                        this_year = this_year + '-1,'
                        lost_box.append([company_code, security_code, exchange_market_code, year, season])
                    else:
                        this_year = this_year + '0,'
                    continue
                elif 200 in checkValue:
                    this_year = this_year + '3,'
                elif -110 in checkValue or 110 in checkValue or 50 in checkValue:
                    this_year = this_year + '1,'
                elif -60 in checkValue:
                    this_year = this_year + '4,'
                elif 5 in checkValue:
                    this_year = this_year + '5,'
                else:
                    lost_box_new.append([company_code, company_name.encode('gbk'), sector_map.get(company_code, ''), year, season])
                    this_year = this_year + '-2,'
                if len(checkValue) > 1:
                    re_box.append(str(r[0]) + ',' + str(year) + ',' + str(season) + ',' + str(len(checkValue)))
            this_company = this_company + this_year
            print this_year + ' ' + str(year)
        value_box.append(this_company)
        # print this_company

    # str_loss = '\n'.join([tools.linkStr(x, ',') for x in lost_box])

    # 输出到文件
    save_data('./CHN.csv', header + '\n'.join(value_box))
    save_data('./CHN_re.csv', '\n'.join(re_box))
    save_data('./CHN_lost.csv', '\n'.join([tools.linkStr(x, ',') for x in lost_box]))


    with file('./lost_box_new.csv', 'w+') as outputFile:
        writer = csv.writer(outputFile)
        for l in lost_box_new:
            # print str(tools.linkStr(l, ',')).encode('utf-8')
            writer.writerow(l)

    sys.exit()

def save_data(savepath, data):
    try:
        # tools.makeDirs(savepath)

        output = file(savepath, 'w+')

        output.write(data.encode('gbk'))

        output.close()
    except:
        print 'error'
