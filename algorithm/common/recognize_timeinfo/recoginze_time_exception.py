# -*- coding: UTF-8 -*-
class TimeRecoginzeException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message
