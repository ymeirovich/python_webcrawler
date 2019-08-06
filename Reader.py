"""
Reader
        Json reader
        import any previous json file
        cli arg to use prev json output
"""
import json
from Writer import Writer


class Reader:

    def __init__(self):
        self.write = Writer()

    def getJson(self, file):
        pass

    def json_to_crawl(self, file):
        try:
            with open(file) as json_file:
                data = json.load(json_file)
                return data
        except Exception as e:
            self.write.logError(e)
