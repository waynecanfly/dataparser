# -*- coding: UTF-8 -*-

import datetime
import gc
import os
import sys
import time
import traceback

from apscheduler.schedulers.background import BackgroundScheduler

import mainFunc
from algorithm.common import configManage, dbtools, tools
from algorithm.common_tools_pdf import subject_match_tools

THREAD_NUM = 10

def loadPeriodJob():
    scheduler = BackgroundScheduler()
    scheduler._logger = configManage.logger

    als = configManage.algorithmMap.get('time_driven', None)
    if als is None:
        return
    for al in als:
        method = mainFunc.getMethod(al)
        timePara = mainFunc.getTimePara(al['period'])
        scheduler.add_job(func=method, trigger = 'cron',
                          year=timePara['year'],
                          month=timePara['month'],
                          day=timePara['day'],
                          day_of_week=timePara['day_of_week'],
                          hour=timePara['hour'],
                          minute=timePara['minute'],
                          second=timePara['second'])
    # jobs = scheduler.get_jobs()

    scheduler.start()


def monitor():
    # counter
    alreadyProcessNum = 0
    roundtimes = 1

    while 1:
        try:
            # 清一次cache，从数据处理逻辑中，我们不需要对同一个文件进行多次的读写【后续可做成时间驱动型任务】
            os.system('echo 1 > /proc/sys/vm/drop_caches')
            gc.disable()

            # capturen pattern
            # isHaveNew = capture_pattern.process() 【后续可做成时间驱动型任务】
            #
            # # 重跑表提取库缺失状态
            # if isHaveNew:
            #     pass
            #     mainFunc.captureTableRerun() 【周期执行？数据驱动？数据驱动的话任务优先级问题】

            # 上传处理完成的pdf到hdfs. 加个限制。有三万个再上传。【后续可做成时间驱动型任务】
            alreadyProcessNum += THREAD_NUM
            # merge_files.process('product') if alreadyProcessNum > 30000 else 0
            # 当前优先级
            curAlgroP = -1
            # 当前优先级是否有执行
            isExeCurAlgroP = False
            # ==== monitor 正式流程
            for al in configManage.algorithmMap['data_driven']:
                # 获取算法入口
                method = mainFunc.getMethod(al)

                # 获取待处理数据
                paraBox = mainFunc.getProcessFileInfo(al)

                # 判断是否需要休眠【休眠放到for循环外面，while循环里面】
                if len(paraBox) == 0:
                    continue

                if curAlgroP == al['priority']:
                    isExeCurAlgroP = True
                    # 分发处理
                    mainFunc.exeAlgorithm(al, method, paraBox, roundtimes, THREAD_NUM)

                else:
                    if isExeCurAlgroP == True:
                        break
                    else:
                        curAlgroP = al['priority']
                        isExeCurAlgroP = True
                        # 分发处理
                        mainFunc.exeAlgorithm(al, method, paraBox, roundtimes, THREAD_NUM)

                roundtimes = roundtimes + 1

            # 判断是否需要休眠【休眠放到for循环外面，while循环里面】
            if not isExeCurAlgroP:
                configManage.logger.info('sleep[NO_DATA] ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                print 'sleep[NO_DATA] ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                time.sleep(150)
                continue

            gc.enable()
            gc.collect()
        except Exception as e:
            excepttext = traceback.format_exc()
            print excepttext
            configManage.logger.error(excepttext)
            print 'sleep[Error] ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            configManage.logger.error('sleep[Error] ' + datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            time.sleep(600)


def temp():
    sql = 'select distinct original_subject from  subject_statistics'
    result = dbtools.query_pdfparse(sql)
    box = set()
    for s in result:
        text = s[0]
        matchtext = subject_match_tools.getPureSbuectText(text)
        box.add(matchtext)

    str = tools.linkStr(list(box).sort(), '\n')

    f = file('./subjects_from_db.txt', 'w+')
    f.write(str)

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 初始化配置
    configManage.initConfig(False)

    # 系统初始化
    # mainFunc.projectInit()

    # # 注册时间驱动型任务【此处写一个周期任务，周期algrithm.json及reload工程实现热加载】
    # loadPeriodJob()

    # 启动监控，触发数据驱动型任务d
    monitor()