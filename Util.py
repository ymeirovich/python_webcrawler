"""
Util
        calcRatio
        removeDuplicateLInks
        trimDomainStr -- remove all but the domain
        trimLinkStr -- limit to filename length ?
        isMimeTypeValid
        isPageExpired
"""
import sys, json, os
import requests
import requests_cache
from datetime import datetime
from Writer import Writer
from Reader import Reader
import os


class Util:

    def __init__(self):
        self.read = Reader()
        self.write = Writer()

    def calcRatio(self):
        pass

    def os_filename_length(self, func):
        length = 0

        def memoized_func(length=None, *args):
            if length is not 0:
                return length
            x = str(os.statvfs('/')).split('=')
            y = x[len(x) - 1]
            length = int(''.join(list(filter(str.isdigit, y))))
        return memoized_func

    def trimDomainStr(self, url):
        filename_maxlength = self.os_filename_length()
        url_length = len(url)
        return (url[:filename_maxlength]) if url_length > filename_maxlength else url

    @staticmethod
    def getArg(argstr):
        for arg in sys.argv:
            if argstr in arg:
                return arg.split("=")[1]


class Requests:
    # cache saved to sqlite db for persistence
    def __init__(self):
        requests_cache.install_cache(cache_name='web_cache', backend='sqlite', expire_after=600)
        self.write = Writer()

    def fetch(self, url):
        try:
            r = requests.get(url, verify=False)
            return r
        except Exception as e:
            self.write.logError(e)

    def disable_cache(self):
        try:
            requests_cache.disabled()
        except Exception as e:
            self.write.logError(e)

    def clear_cache(self):
        try:
            requests_cache.clear()
        except Exception as e:
            self.write.logError(e)

    def is_from_cache(self, r):
        try:
            c = r.from_cache
            self.write.print('From Cache: ' + str(c))
            return c
        except Exception as e:
            self.write.logError(e)


class Node:
    def __init__(self, _url, sourcenodes, depth=0, index=0):
        self.write = Writer()
        self.url = _url
        self.index = index
        self.sourceNodes = sourcenodes
        self.depth = depth

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__,
                          sort_keys=True, indent=4)

    @staticmethod
    def load_json_file():
        with open('webcrawler_data.json') as f:
            data = json.load(f)
        return data

    # @staticmethod
    # def from_json(data, cls):
    #     annotations: dict = cls.__annotations__ if hasattr(cls, '__annotations__') else None
    #     if issubclass(cls, List):
    #         list_type = cls.__args__[0]
    #         instance: list = list()
    #         for value in data:
    #             instance.append(Node.from_json(value, list_type))
    #         return instance
    #     elif issubclass(cls, Dict):
    #         key_type = cls.__args__[0]
    #         val_type = cls.__args__[1]
    #         instance: dict = dict()
    #         for key, value in data.items():
    #             instance.update(Node.from_json(key, key_type), Node.from_json(value, val_type))
    #         return instance
    #     else:
    #         instance: cls = cls()
    #         for name, value in data.items():
    #             field_type = annotations.get(name)
    #             if inspect.isclass(field_type) and isinstance(value, (dict, tuple, list, set, frozenset)):
    #                 setattr(instance, name, from_json(value, field_type))
    #             else:
    #                 setattr(instance, name, value)
    #         return instance

    def to_json_file(self, entry, file='webcrawler_data.json'):
        try:
            a = []
            if not os.path.isfile(file):
                a.append(entry)
                with open(file, mode='w') as f:
                    f.write(json.dumps(a, indent=2))
            else:
                with open(file) as feedsjson:
                    feeds = json.load(feedsjson)

                feeds.append(entry)
                with open(file, mode='w') as f:
                    f.write(json.dumps(feeds, indent=2))
        except json.decoder.JSONDecodeError as j:
            self.write.logError('JSONDecodeError: ' + str(j))
        except FileNotFoundError:
            self.write.logError(self.file_name + " not found. ")
        except Exception as e:
            self.write.logError(e)

        # def set_depth(self, x):
        #     self.depth = x
        #
        # def get_depth(self):
        #     return self.depth
        #
        # def del_depth(self):
        #     del self.depth
        #
        # depth = property(get_depth,set_depth,del_depth)
        # # url = self.url
        # # index = self.index
        # # sourcenodes = self.sourceNodes


class Links:
    def __init__(self, _url, _links, _depth):
        self.url = _url
        self.links = _links
        self.depth = _depth


class Pages:
    def __init__(self):
        self.write = Writer()
        self.pages = {}
        self.read = Reader()
        pass

    def new_page(self, page):
        self.pages[page] = []

    def get_page(self, page):
        return self.pages.get(page)

    def add_link(self, _page, link, depth, d=None):
        try:
            d = {
                "link": link,
                "depth": depth,
                # "date": datetime.timestamp(datetime.now())
            }
            page = self.get_page(_page)
            if page is not None:
                page.append(d)
            else:  # add new page empty object and recall the fx
                self.new_page(_page)
                self.add_link(_page, link, depth)
        except Exception as e:
            self.write.logError(e)

    def output_to_tsv(self):
        self.write.toTsv(self.pages)

    def output(self):
        return self.pages

    def output_to_json(self, links, _exist=False, depth=0):
        try:
            existing_json = []
            for l in links:
                found = self.pages.get(l.url)
                if found is not None and 'page_links' not in found[0]:
                    found.insert(0, {
                        "page_links": len(l.links)
                    })
                # else:
                #     for k in l.links:
                #         self.add_link(l.url, k, l.depth)
                #     found = self.pages.get(l.url)
                #     if found is not None:
                #         found.append({
                #             "page_links": len(l.links)
                #         })
            # only use existing json if defined in cli param
            if _exist:
                existing_json = self.get_existing_json()
                if existing_json is not None:
                    self.pages = self.merge_json(self.pages, existing_json)
            with open('outputToJson.json', mode='w') as f:
                f.write(json.dumps(self.pages, indent=2))
        except Exception as e:
            self.write.logError(e)

    def get_existing_json(self):
        return self.read.json_to_crawl("outputToJson.json")

    def merge_json(self, x, y):
        try:
            z = {**x, **y}
            return z
        except Exception as e:
            self.write.logError(e)


class Edge:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __eq__(self, other):
        return self.source == other.source and self.target == other.target

    def __hash__(self):
        return hash((self.source, self.target))


class Graph:
    def __init__(self, nodes=[], edges=set()):
        self.nodes = nodes
        self.edges = edges

    def addNode(self, node, nodeIndex):
        node.index = nodeIndex
        self.nodes.append(node)

    def addEdge(self, sourceNodeIdx, targetNodeIdx):
        edge = Edge(sourceNodeIdx, targetNodeIdx)
        self.edges.add(edge)
