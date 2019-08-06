
from Util import Util
from Writer import Writer
from Fetch import Fetch
import time
from datetime import datetime as dt

import csv, json, logging, os
import sys, traceback
from urllib.parse import urlparse

class Main:

    def __init__(self):
        self.originUrl = Util.getArg('originUrl')
        self.depthLimit = int(Util.getArg('depthLimit'))
        self.start_with_json = Util.getArg('startWithJson')
        self.delay = Util.getArg('delay')
        self.write = Writer()
        self.fetch = Fetch(self.originUrl, self.depthLimit, self.start_with_json)

    def start(self):
        self.write.logDebug('Main.start')
        if self.delay is not None:
            self.write.print('sleep 30')
            self.write.print('min: ' + str(dt.now().minute))
            time.sleep(30)
            if dt.now().minute == int(self.delay):
                self.write.print('starting...')
                self.fetch.start_crawl()
            else:
                self.start()
        else:
            self.write.print('starting...')
            self.fetch.start_crawl()


main = Main()
main.start()

"""
classes
    Writer
        Json writer - json file
        Csv writer
            - tab delimeter
            - convert json to tab
        LogWriter
    Reader
        Json reader
        import any previous json file
        cli arg to use prev json output
    Fetch
        _queue[]
        _depth --> cli arg
        processPage
            getAllLinks
            check mimetype - text/html
            add list of links to queue
        getAllLinks

    Util
        calcRatio
        removeDuplicateLInks
        trimDomainStr -- remove all but the domain
        trimLinkStr -- limit to filename length ?
        isMimeTypeValid
        isPageExpired
    Caching
    ? Timer
"""