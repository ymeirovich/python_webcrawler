"""
Fetch
        _queue[]
        _depth --> cli arg
        processPage
            getAllLinks
            check mimetype - text/html
            add list of links to queue
        getAllLinks
"""
import sys
from urllib.parse import urlparse
import urllib3
import urllib.request
import urllib.error
from bs4 import BeautifulSoup
import requests
import mimetypes
from Writer import Writer
from Reader import Reader
from Util import Node, Graph, Requests, Pages, Links
import ssl
import urllib
import json
import time
import json


class Fetch:

    def __init__(self, origin_url, depth_limit, start_with_json):
        self.read = Reader()
        self.links = []
        self.pages = Pages()
        self.requests = Requests()
        self.write = Writer()
        self.url = origin_url
        self.depthLimit = depth_limit
        self.start_with_json = json.loads(start_with_json.lower())
        # self.start_with_json = True if self.json_path is not None else self.start_with_json = False
        self.visitedUrls = set()
        self.currentDepth = 0
        self.nodesToVisit = []
        self.graph = Graph()
        self.nodeIndex = 0
        self.nodeCount = 0
        self.nodeUrlMap = {}
        self.response_header = {}

    def start_crawl(self):
        self.write.print("start_crawl(): ")
        try:
            if self.url is None:
                raise Exception('The starting URL is not provided as an argument.')
            if self.depthLimit is None:
                raise Exception('Depth level is not provided as an argument')
            if self.start_with_json:
                # start from previous search
                self.write.print('start_with_json')
                self.crawl_with_json()
            else:
                # new search
                node = Node(self.url, None)
                self.crawl(node)
        except Exception as e:
            self.write.logError(e)

    def crawl(self, node):
        self.write.print("crawl(): " + node.url)
        try:
            visited = node.url in self.visitedUrls
            if not visited:
                self.graph.addNode(node, self.nodeIndex)
                self.nodeIndex += 1
                self.nodeCount += 1
                self.visitedUrls.add(node.url)
            if node.sourceNodes:  # If this is not the starting node
                sourceNode = node.sourceNodes.pop()
                if sourceNode.index is not None and node.index is not None:
                    self.graph.addEdge(sourceNode.index, node.index)  # Add an edge between sourceNode and node

            if not visited:

                self.pages.output_to_json(self.links, self.start_with_json) # incrementally output to json for recovery
                soup = self.generateSoup(node.url)
                links = self.findLinks(soup, node)
                links = {l for l in links}  # Remove duplicate links
                links_item = Links(node.url,links, node.depth)
                self.links.append(links_item)
                if links:
                    self.write.print("Depth: " + str(node.depth))
                    # if self.currentDepth >= self.depthLimit:  # If depth limit reached, getNextNode (up a level)
                    if node.depth >= self.depthLimit:  # If depth limit reached, getNextNode (up a level)
                        # self.currentDepth = 0  # Reset currentDepth
                        self.getNextNode()
                    else:  # Otherwise, keep going deeper
                        # self.currentDepth += 1
                        self.dfs(node, links, self.currentDepth)
                else:  # No links present
                    self.getNextNode()
            else:  # Avoid infinite loop
                self.getNextNode()
        except Exception as e:
            self.write.logError(e)

    def crawl_with_json(self):
        try:
            '''
            get the previous run json file
            loop through
                  "http://localhost:8080/a1.html": [
                    {
                      "link": "http://localhost:8080/a2a.html",
                      "depth": 2,
                      "date": 1564645059.166687
                    },
                    {
                      "page_links": 2
                    }
                  ],
                  
                  compare the total number of page links to the actual number of pages visited
                  if they are not equal then this page was not fully crawled
                  insert into the queue via getNextNode()
                  
                  crawls insert visited pages from top of the tree down
                  from a json file nodes are inserted in reverse
                  therefore, deeper nodes are crawled before higher level nodes
                  ensures nodes are not crawled again
            '''

            json_file = self.read.json_to_crawl('outputToJson.json')
            for j in json_file:
                # self.visitedUrls.add(j)
                for pl in json_file[j]:
                    # get the page_links obj and compare that
                    # number to the number of visited links in the json obj
                    page_links = pl.get('page_links')
                    link = pl.get('link')
                    if page_links is not None:
                        if page_links != len(json_file[j])-1:
                            self.add_new_node(json_file, j)
                    if link is not None:
                        if json_file.get(link) is None:
                            self.add_new_node(json_file, j)
            self.getNextNode()
        except Exception as e:
            self.write.logError(e)

    def add_new_node(self, json_file, j):
        parent_url = j
        depth = json_file[j][1]['depth'] - 1
        newNode = Node(parent_url, None, depth)
        self.nodesToVisit.append(newNode)

    # Convert URL into soup
    def generateSoup(self, url):
        try:
            '''
                self.requests.fetch(url) will retrieve from cache if not yet expired
                otherwise will make the call
            '''
            # self.write.print("generateSoup(): " + url)
            sourceCode = self.requests.fetch(url)  # requests.get(url)
            self.requests.is_from_cache(sourceCode)
            plainText = sourceCode.text
            soup = BeautifulSoup(plainText, "html.parser")
            return soup
        except Exception as e:
            self.write.logError(e)

    def dfs(self, currentNode, links, currentDepth):
        try:
            # self.write.print("dfs(): ")
            for link in links:
                if link not in self.visitedUrls:
                    # item = Item(link)
                    currentDepth = currentNode.depth + 1
                    newNode = Node(link, [currentNode], currentDepth)
                    newNode.to_json_file(newNode.toJSON())
                    self.pages.add_link(currentNode.url, link, currentDepth)
                    newNode.sourceNodes.append(currentNode)
                    self.nodesToVisit.append(newNode)
                elif link in self.nodeUrlMap:  # Repeat URL, get existing node
                    existingNode = self.nodeUrlMap[link]
                    existingNode.sourceNodes.append(currentNode)
                    self.nodesToVisit.append(existingNode)
            self.getNextNode()
        except Exception as e:
            self.write.logError(e)

    def getNextNode(self):
        self.write.print("getNextNode(): ")
        if len(self.nodesToVisit) is not 0:
            # We use the same data structure to store urlsToVisit for BFS and DFS,
            # and pop elements off the same way.  How the elements are added is
            # what's important.
            nextNode = self.nodesToVisit.pop()
            self.crawl(nextNode)
        else: # Crawl is over
            self.printGraph()

    # Parse soup to find links
    def findLinks(self, soup, node):
        self.write.print("findLinks()")
        try:
            links = soup.findAll('a')
            hrefs = []
            for link in links:
                if 'http' in link.get('href',''):
                    href = link.get('href', '')
                   # hrefs.append(href)
                    if self.check_mime_type(href, node):
                        hrefs.append(href)
            return hrefs
        except Exception as e:
            self.write.logError(e)

    def printGraph(self):
        self.pages.output_to_json(self.links, self.start_with_json)
        for node in self.graph.nodes:
            print("\nNode:")
            if node.url:
                print("Index: " + str(node.index))
                print("URL: " + node.url)
        # if self.graph.edges:
        #     print("\nEdges:")
        #     edgeCount = 0
        #     for e in self.graph.edges:
        #         print("Source: " + str(e.source) + " Target: " + str(e.target))
        # print("\nJSON:")
        # print(self.jsonSerialize())
        self.pages.output_to_tsv()
        # print(json.decoder(Node.load_json_file()))


    def check_mime_type(self, url, node):
        try:
            # use guess_type to for speed / efficiency, no need to call the site
            # returns a tuple
            if node.depth >= self.depthLimit:
                return False
            if mimetypes.guess_type(url)[0] == 'text/html':
                self.write.print(url)
                return True
            # handle [SSL: CERTIFICATE_VERIFY_FAILED]
            context = ssl._create_unverified_context()
            # 429 error comes from Reddit throttling the request
            self.write.print(url)
            with urllib.request.urlopen(url, context=context) as response:
                info = response.info()
                if info.get_content_type() == 'text/html':
                    return True
                else:
                    return False
        except urllib3.exceptions.MaxRetryError as maxretry_err:
            self.write.logError(maxretry_err)
            self.write.print('maxretry: sleeping for 30 seconds')
            time.sleep(30)
        except ssl.SSLError as ssl_err:
            self.write.logError(ssl_err)
        except urllib.error.HTTPError as err:
            if err.code == 404:
                self.write.print("HTTP 404 Not Found: " + url)
            elif err.code == 403:
                self.write.print("HTTP 403 Forbidden: " + url)
            else:
                self.write.print(err)
        except Exception as e:
            self.write.logError(e)

    def jsonSerialize(self):
        for n in self.graph.nodes:
            n.sourceNodes = []
        self.graph.edges = list(self.graph.edges)
        return json.dumps(self.graph, default=lambda o: o.__dict__)


"""

                    # output = Node(link, [currentNode])
                    # dict = {
                    #     "link": link,
                    #     "depth": currentDepth
                    # }
                    # output.to_json_file(dict, 'output.json')
                    
        visited = node.url in self.visitedUrls
        if not visited:
            self.graph.addNode(node, self.nodeIndex)
            self.nodeIndex += 1
            self.nodeCount += 1
            self.visitedUrls.add(node.url)
        if node.sourceNodes:  # If this is not the starting node
            sourceNode = node.sourceNodes.pop()
            if sourceNode.index is not None and node.index is not None:
                self.graph.addEdge(sourceNode.index, node.index)  # Add an edge between sourceNode and node
        if not visited:
            soup = self.generateSoup(node.url)
            hasKeyword = self.checkForKeyword(soup, node.url)
            if hasKeyword:
                node.keyword = True
            links = self.findLinks(soup)
            links = self.validLinks(links)
            links = {l for l in links}  # Remove duplicate links
            if links:
                if self.method == "BFS":
                    self.bfs(node, links)
                else:  # DFS
                    self.currentDepth += 1
                    if self.currentDepth >= self.depthLimit:  # If depth limit reached, getNextNode (up a level)
                        self.currentDepth = 0  # Reset currentDepth
                        self.getNextNode()
                    else:  # Otherwise, keep going deeper
                        self.dfs(node, links)
            else:  # No links present
                self.getNextNode()
        else:  # Avoid infinite loop
            self.getNextNode()
            
            
    def testRequest(self, url):
        requests.get(url)
    
    
    def isValidUrl(self, url):
        # self.write.print("isValidUrl(): ")
        extensionBlacklist = [".zip", ".dmg", ".msi", ".tar", ".exe", ".sisx", ".ico", ".jpg", ".jpeg", ".svg", ".gif", ".png"]
        for x in extensionBlacklist:
            if x in url:
                return False
        if "http" not in url: return False
        parsed_url = urlparse(url)
        if not bool(parsed_url.scheme): return False
        try:
            self.testRequest(url)
        except:
            return False
        return True
"""

# DFS
# sourceNodes = node.sourceNodes
# depth = 1 if isinstance(node.sourceNodes,list) else 0
# self.currentDepth = self.countDepth(sourceNodes, depth)
# c = self.flatten(node)
# self.countSourceNodes(node)
# list(self.fun(node))
# self.currentDepth = c if type(c) == int else c.count(node.sourceNodes)
# sum(x.count(sourceNodes) for x in node.sourceNodes) # self.countSourceNodes(node)

# def fun(self, d):
#     if hasattr(d, 'sourceNodes'):
#         yield d['sourceNodes']
#     for k in d:
#         if isinstance(d[k], list):
#             for i in d[k]:
#                 for j in self.fun(i):
#                     yield j
#
# def countDepth(self, sourceNodes, depth=0):
#     try:
#         if sourceNodes.sourceNodes is None:
#             depth += 1
#         if isinstance(sourceNodes.sourceNodes, (list,)):
#             # if hasattr(sourceNodes[0], 'sourceNodes') and sourceNodes[0].sourceNodes is None:
#             #     self.currentDepth += 1
#             #     return
#             depth += 1
#             self.countDepth(sourceNodes.sourceNodes[0], depth)
#
#         return depth
#     except Exception as e:
#         self.write.logError(e)
#
# def flatten(self, seq, container=None):
#     try:
#         if container is None:
#             container = []
#         if seq.sourceNodes is None:
#             self.currentDepth += 1
#             return
#
#         for s in seq:
#             try:
#                 iter(s)  # check if it's iterable
#             except TypeError:
#                 container.append(s)
#             else:
#                 self.flatten(s, container)
#         return container
#     except Exception as e:
#         self.write.logError(e)

# def countSourceNodes(self, node, _depth=0, sourceNodes = "null"):
#     try:
#         self.currentDepth += 1
#         if node.sourceNodes is None:
#             return
#         elif hasattr(sourceNodes,'sourceNodes') and sourceNodes.sourceNodes is None:
#             return
#         else: # inner loops
#             # if sourceNodes == 'null':
#             #     self.countSourceNodes(node, self.currentDepth, node.sourceNodes[0])
#             sourceNodes = sourceNodes[0] if hasattr(sourceNodes,'sourceNodes') else node.sourceNodes[0]
#             self.countSourceNodes(node, self.currentDepth, sourceNodes)
#                 # return self.currentDepth if sourceNodes.sourceNodes is None else self.countSourceNodes(node, self.currentDepth, sourceNodes.sourceNodes[0])
#     except Exception as e:
#         self.write.logError(e)
