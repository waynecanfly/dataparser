# -*- coding: UTF-8 -*-
class NoHeaderBeMatched(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class NoTableInPDFException(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class StatementNotFound(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class StatementNotAllFound(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message

class TableIncomplete(Exception):
    def __init__(self, message):
        Exception.__init__(self)
        self.message = message