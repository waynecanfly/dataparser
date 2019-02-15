# -*- coding:utf-8 -*-
import datetime
import json
import logging
import os
import threading
import re


lock = threading.Lock()
config = None
algorithmMap = {}
logger = None

comment_re = re.compile(
    '(^)?[^\S\n]*/(?:\*(.*?)\*/[^\S\n]*|/[^\n]*)($)?',
    re.DOTALL | re.MULTILINE
)

def initConfig(isTestConfig=False):
    if '/' in __file__:
        projectPath = __file__.split("algorithm/common")[0]
    else:
        projectPath = __file__.split("algorithm\\common")[0]

    global config, algorithmMap, logger


    # 配置初始化
    if isTestConfig:
        fopen = open(projectPath + 'config/config_test.json')

        try:
            config = json.load(fopen)
            timeMark = datetime.datetime.now().strftime('%Y%m%d%H_%f')
            # timeMark = '2018080218'
            config['timeMark'] = timeMark
            for tablename in config['location'].keys():
                if tablename not in ['pdf_source', 'pdf_line']:
                    location = config['location'][tablename]
                    joinPoint = location.rfind('/')
                    config['location'][tablename] = location[0:joinPoint] + '/' + timeMark + location[joinPoint:]
        finally:
            fopen.close()
    else:
        fopen = open(projectPath + 'config/config.json')
        try:
            config = json.load(fopen)
        finally:
            fopen.close()

    # 算法配置加载
    algorithmMap = {}
    with open(projectPath + 'config/algorithm.json') as alfopen:
        content = ''.join(alfopen.readlines())
        ## Looking for comments
        match = comment_re.search(content)
        while match:
            # single line comment
            content = content[:match.start()] + content[match.end():]
            match = comment_re.search(content)
        # Return json file
        algBox = json.loads(content)
        #配置算法优先级
        algBox.sort(key=lambda x: x['priority'], reverse=True)
        # 算法合法性校验【后续完善】

        # 封装到algorithmMap
        for a in algBox:
            if a['algorithmtype'] not in algorithmMap:
                algorithmMap[a['algorithmtype']] = [a]
            else:
                algorithmMap[a['algorithmtype']].append(a)

    # log 初始化。【还可以完善得更复杂】
    if logger is None:
        logger = logging.getLogger(__name__)
        logger.setLevel(level=logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s: %(message)s')
        if not os.path.exists("./log"):
            os.mkdir("./log")
        handler = logging.FileHandler("./log/log.txt")
        handler.setLevel(logging.INFO)
        handler.setFormatter(formatter)

        console = logging.StreamHandler()
        console.setLevel(logging.INFO)

        logger.addHandler(handler)
        # logger.addHandler(console)






