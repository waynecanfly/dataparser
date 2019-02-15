# -*- coding:utf-8 -*-
import re
import sys

from algorithm.common_tools_pdf import header_match_tools
from capture_table_exceptions import NoTableInPDFException, StatementNotFound, StatementNotAllFound
from algorithm.common import tools, configManage, dbtools
from containers.block import Block
from containers.line import Line
from containers.page import Page
from containers.pattern import Pattern


def outputTables(table_box, p_country, p_company, p_reportid, isConsolidated = True):
    basePath  = configManage.config['location']['pdf_table'] if isConsolidated else configManage.config['location']['pdf_table_alone']

    savepath = basePath + "/p_country={p_country}/p_company={p_company}/"
    savepath = savepath.format(p_country=p_country, p_company=p_company)

    tools.makeDirs(savepath)

    output = file(savepath + '/' + p_reportid + '.csv', 'w+')

    for tIndex, t in enumerate(table_box):
        tableid = tIndex
        tablePage = t.pageNum
        columnIndexs = sorted(t.index_header_map.keys())
        index_column_map = tools.tupleToMap(zip(columnIndexs, range(0, len(columnIndexs))))

        lineIndexMiners = t.body[0].lineIndex - 2


        tableoutputstr = ''

        # global info
        globalinfo_text = ''
        for l in t.title:
            for b in l.blockbox:
                globalinfo_text = globalinfo_text + ' ' + b.text

        globalStr = '{tableid},{tabletype},{pageNum},{isConsolidated},{text},{texttype},{extraText},{x0},{y0},{x1},{y1},{size},,{lineIndex},{columnIndex},{identity},{tablepart},\n'
        globalStr = globalStr.format(tableid=tableid, tabletype=t.table_type,
                                   pageNum=tablePage,
                                   text=re.sub(',', '#|#', globalinfo_text),
                                   x0=0, y0=0, x1=0, y1=0,
                                   size=0,
                                   identity='',
                                   texttype='text-phrase',
                                   lineIndex=0,
                                   isConsolidated = t.isConsolidated,
                                   extraText='',
                                   tablepart='GLOBALINFO',
                                   columnIndex=0)
        output.write(globalStr)
        tableoutputstr += globalStr



        #header
        header_indes = sorted(t.index_header_map.keys())
        for index in header_indes:
            header = t.index_header_map[index]
            headerStr = '{tableid},{tabletype},{pageNum},{isConsolidated},{text},{texttype},{extraText},{x0},{y0},{x1},{y1},{size},,{lineIndex},{columnIndex},{identity},{tablepart},\n'
            headerStr = headerStr.format(tableid=tableid, tabletype = t.table_type,
                                       pageNum=tablePage,
                                       text=re.sub(',','#|#',header.text),
                                       extraText=re.sub(',','#|#',header.extraInfo),
                                       x0=header.x0, y0=header.y0, x1=header.x1, y1=header.y1,
                                       size=0,
                                       texttype='text-phrase',
                                       isConsolidated=t.isConsolidated,
                                       lineIndex=1,
                                       identity=header.identity,
                                       tablepart='HEADER',
                                       columnIndex=index_column_map.get(header.columnIndex))
            output.write(headerStr)
            tableoutputstr += headerStr

        #body
        bodyLineIndex = 2
        for l in t.body:
            for b in l.blockbox:
                bodyStr = '{tableid},{tabletype},{pageNum},{isConsolidated},{text},{texttype},{extraText},{x0},{y0},{x1},{y1},{size},{font},{lineIndex},{columnIndex},{identity},{tablepart},\n'
                bodyStr = bodyStr.format(tableid=tableid, tabletype = t.table_type,
                                           pageNum=b.pageNum,
                                           text=re.sub(',','#|#',b.text),
                                           x0=b.x0, y0=b.y0, x1=b.x1, y1=b.y1,
                                           size=b.fontsize,
                                           lineIndex=bodyLineIndex,
                                           identity= t.index_header_map.get(b.columnIndex, b).identity,
                                           texttype=b.type,
                                           isConsolidated=t.isConsolidated,
                                           tablepart='BODY',
                                           font=b.font,
                                           extraText='',
                                           columnIndex=index_column_map.get(b.columnIndex, 99))
                output.write(bodyStr)
                tableoutputstr += bodyStr
            bodyLineIndex = bodyLineIndex + 1

        # body buffer
        for l in t.body_buffer:
            for b in l.blockbox:
                bodyBuffStr = '{tableid},{tabletype},{pageNum},{isConsolidated},{text},{texttype},{extraText},{x0},{y0},{x1},{y1},{size},{font},{lineIndex},{columnIndex},{identity},{tablepart},\n'
                bodyBuffStr = bodyBuffStr.format(tableid=tableid, tabletype=t.table_type,
                                         pageNum=b.pageNum,
                                         text=re.sub(',', '#|#', b.text),
                                         x0=b.x0, y0=b.y0, x1=b.x1, y1=b.y1,
                                         size=b.fontsize,
                                         lineIndex=bodyLineIndex,
                                         identity=t.index_header_map.get(b.columnIndex, b).identity,
                                         texttype=b.type,
                                         isConsolidated=t.isConsolidated,
                                         tablepart='BODYBUFFER',
                                         font=b.font,
                                         extraText='',
                                         columnIndex=index_column_map.get(b.columnIndex, 99))
                output.write(bodyBuffStr)
                tableoutputstr += bodyBuffStr
            bodyLineIndex = bodyLineIndex + 1
    output.close()


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
    lineNumType = set()
    for h in headers:
        id = 'temp'
        lineNum = 99
        text = header_match_tools.getMatchText(h[0])
        text = h[0]
        identity = h[1]
        ps_box.append(Pattern(id, lineNum, text, identity))
        lineNumType.add(lineNum)
    lineNumType = list(lineNumType)
    return {
        'ps': ps_box,
        'lines':  [5,4,3,2,1]
    }


def getSourceData(datapath):
    blockBox = []
    fopen = open(datapath)
    try:
        while 1:
            line = fopen.readline()
            if not line:
                break
            data = line.split(',')
            if len(data) != 16:
                continue
            blockBox.append(
                Block(data[0], re.sub('(#\|#)', ',', data[1]), data[2], data[3], data[4], data[5], data[6], data[7],data[8],
                      data[9], data[10], data[11], data[12], data[13], data[14]))
    finally:
        fopen.close()
    return blockBox


def lineConverge(blockBox):
    linebox_total = []
    curLine = Line(blockBox[0])

    for i in range(1, len(blockBox)):
        b = blockBox[i]
        if curLine.add(b) == 'reject':
            linebox_total.append(curLine)
            curLine = Line(b)
    linebox_total.append(curLine)
    return linebox_total

def pageConverge(linebox_total):
    pagebox = []
    curPage = Page(linebox_total[0])
    for i in range(1, len(linebox_total)):
        l = linebox_total[i]
        if curPage.add(l) == 'reject':
            pagebox.append(curPage)
            curPage = Page(l)
    pagebox.append(curPage)
    return pagebox

def filterPage(pagebox):
    valid_page_box = [page for page in pagebox if pagefilter2(page)]
    if len(valid_page_box) == 0:
        raise NoTableInPDFException('NoTableException')
    else:
        return valid_page_box

def filterIllegalTable(table_box):
    valid_table_box = [table for table in table_box if len(table.body) > 0 and table.title and table.table_type in ['BS', 'IS', 'CF']]
    if len(valid_table_box) == 0:
        raise StatementNotFound('statement can not found overall, found quantity: 0')
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


def judgeIfHadFoundAllAimTable(valid_table_box):
    # 备忘： 后续可能需要加上时间跨度的判断，如果某个表有某个时间跨度，那么所有类型的报表是否都有这个时间跨度的表？
    consolidatedKeyWord = ['consolidated','合并']
    standaloneKeyWord = ['standalone','母公司']

    for table in valid_table_box:
        pureTitle = getJudgePureText(table)
        for standWord in standaloneKeyWord:
            if standWord in pureTitle:
                table.isConsolidated = 0
                break
        for conWord in consolidatedKeyWord:
            if conWord in pureTitle:
                table.isConsolidated = 1
                break


    consolidatedBox = set()
    standaloneBox = set()
    unknowBox = set()
    # 分类
    for table in valid_table_box:
        if table.isConsolidated == 1:
            consolidatedBox.add(table.table_type)
        elif table.isConsolidated == -1:
            unknowBox.add(table.table_type)
        elif table.isConsolidated == 0:
            standaloneBox.add(table.table_type)
    #  判断
    if len(consolidatedBox) == 3:
        return True
    elif len(consolidatedBox) == 0 and len(unknowBox) == 3:
        return False  # 表示表找全了，但是没有独立报表和母公司报表之分
    else:
        if len(consolidatedBox) == 0 and len(unknowBox) == 0:
            raise StatementNotFound('No report be found')
        else:
            raise StatementNotAllFound('Not all report be found')

def takeOutPageUselessBlock(pagebox):
    REPEAT_THR = 3
    pageTop3AndLast3LineMap = {0:[], 1:[], 2:[], -1:[], -2:[], -3:[]}
    for page in pagebox:
        try:
            pageTop3AndLast3LineMap[0].append(page.linebox[0]) if page.linebox[0].y0 > 500 else ''
            pageTop3AndLast3LineMap[1].append(page.linebox[1]) if page.linebox[1].y0 > 500 else ''
            pageTop3AndLast3LineMap[2].append(page.linebox[2]) if page.linebox[2].y0 > 500 else ''
            pageTop3AndLast3LineMap[-1].append(page.linebox[-1]) if page.linebox[-1].y0 < 500 else ''
            pageTop3AndLast3LineMap[-2].append(page.linebox[-2]) if page.linebox[-2].y0 < 500 else ''
            pageTop3AndLast3LineMap[-3].append(page.linebox[-3]) if page.linebox[-3].y0 < 500 else ''
        except Exception:
            pass

    pageLineTakeOutMap = {}
    for lineNum in pageTop3AndLast3LineMap.keys():
        lines = pageTop3AndLast3LineMap[lineNum]
        pageLineTakeOutMap[lineNum] = []
        classifyMap = {}
        # classify
        for l in lines:
            try:
                withoutdigitText = re.sub('\s', '', re.sub('\d+', '*', l.text)).encode('utf-8')
            except:
                withoutdigitText = l.text
            if withoutdigitText not in classifyMap:
                classifyMap[withoutdigitText] = [l]
            else:
                classifyMap[withoutdigitText].append(l)
        for linesPerKind in classifyMap.values():
            kindAmonut = len(linesPerKind)
            # if (kindAmonut > 5) or (kindAmonut / pageAmonut >= 0.4 and kindAmonut>2):
            if kindAmonut > REPEAT_THR:
                for l in linesPerKind:
                    pageLineTakeOutMap[lineNum].append(l.pageNum)

    for page in pagebox:
        pageNum = page.pageNum

        if pageNum in pageLineTakeOutMap[2] and pageNum in pageLineTakeOutMap[1] and pageNum in pageLineTakeOutMap[0]:
            del page.linebox[2]

        if pageNum in pageLineTakeOutMap[1] and pageNum in pageLineTakeOutMap[0]:
            del page.linebox[1]

        if pageNum in pageLineTakeOutMap[0]:
            del page.linebox[0]


        if pageNum in pageLineTakeOutMap[-3] and pageNum in pageLineTakeOutMap[-2] and pageNum in pageLineTakeOutMap[-1]:
            del page.linebox[-3]
        if pageNum in pageLineTakeOutMap[-2] and pageNum in pageLineTakeOutMap[-1]:
            del page.linebox[-2]
        if pageNum in pageLineTakeOutMap[-1]:
            del page.linebox[-1]

def isInNoTitleHeader(noTitleTableHeaderRange, pageNum, lineIndex):
    headerRanges = noTitleTableHeaderRange.get(pageNum, False)
    if headerRanges:
        return lineIndex >= headerRanges[0] and lineIndex <= headerRanges[1]
    else:
        return False


def fittingNonFinishTable(tablebox, pagebox):

    #
    notaimTableHeaderRange =  {}
    aimTableBox = []
    for t in tablebox:
        if t.isOnlyHaveHeader and t.table_type == 'unknow':
            notaimTableHeaderRange[t.pageNum] = t.headerRange
        else:
            aimTableBox.append(t)

    pageNumPageMap = {}
    for page in pagebox:
        pageNumPageMap[page.pageNum] = page

    for i, table in enumerate(aimTableBox):
        nextTablePageNum = sys.maxint if i+1 >= len(aimTableBox) else aimTableBox[i+1].pageNum
        nextTableHeaderLineMinIndex = sys.maxint if i+1 >= len(aimTableBox) else aimTableBox[i+1].headerRange[0]

        nextPageNum = table.pageNum + 1

        while not table.bodyFoundFinish and nextPageNum <= nextTablePageNum: # 第二个条件防止影响别的表的columnindex
            nextPage = pageNumPageMap.get(nextPageNum, None)
            if nextPage:
                for line in nextPage.linebox:
                    if nextTablePageNum == nextPageNum and line.lineIndex >= nextTableHeaderLineMinIndex:
                        table.setTableFinish()
                        break
                    # 判断该行是否处于无title表的表头中。这个是要解决跨页表有表头的问题.
                    isHeader = isInNoTitleHeader(notaimTableHeaderRange, line.pageNum, line.lineIndex)
                    if (not isHeader) or (isHeader and len(table.body)==0): #
                        result = table.add(line)
                        if result == 'reject':
                            break
            else:
                table.setTableFinish()
            nextPageNum = nextPageNum + 1
    return aimTableBox

def structureMarkIsFull():
    MARK_CAPACITY = 60 # 待标记的数量最多只能有60个
    checksql = 'select count(*) from {table} where statusid = 33'
    checksql = checksql.format(table=configManage.config['table']['status'])
    result = dbtools.query_pdfparse(checksql)
    return int(result[0][0]) >= MARK_CAPACITY

def kindredTableTypeFilter(tablebox):
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

        # if table.table_type not in tabletype_map.keys():
        #     tabletype_map[table.table_type] = [table]
        # else:
        #     tabletype_map[table.table_type].append(table)

    # 如果某一个table组中包含了所有目标报表的话，丢弃其它组的报表
    aimset = {'BS', 'IS', 'CF'}
    for i, group in enumerate(tableGroup):
        tableTypeSet = set()
        for t in group:
            if t.table_type == 'OCI':
                p = 'IS'
            else:
                p = t.table_type
            tableTypeSet.add(p)
        if aimset.issubset(tableTypeSet):
            return group
    return tablebox

# body 中的一个block只能对应一个header，当一个block对应多个header时，取重叠率最高那个
def fitting_columnindex(tablebox):
    for t in tablebox:
        # 非线表不需要修正
        if t.linetableid is not None:
            for l in t.body:
                for b in l.blockbox:
                    overlapMap = {}
                    for k in t.index_header_map.keys():
                        h = t.index_header_map[k]
                        overlapMap[k] = tools.overlapRate([b.x0, b.x1], [h.x0, h.x1])
                    maxKey = max(overlapMap, key=overlapMap.get)
                    b.columnIndex = maxKey

def getPageMap(pagebox):
    pagemap = {}
    for p in pagebox:
        pagemap[p.pageNum] = p
    return pagemap