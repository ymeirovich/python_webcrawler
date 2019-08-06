"""
    Json writer - json file
    Csv writer
        - tab delimeter
        - convert json to tab
    LogWriter
"""

import csv, json, logging, os
import sys, traceback
from urllib.parse import urlparse


class Writer:

    def toTsv(self, _pages):
        print('exporting to output.tsv')
        _link_ratios = {}
        _link_list = []
        _link_list_single = []

        def extract_url(_url):
            data = urlparse(_url)
            return data.netloc

        def calculate_ratios(link, parent_url):
            print('calculating ratios')
            '''
            loop to each subpage
            extract url from link property
            check if _link_ratios has the url ratio already calculated,
            if so
                return value
            else
                add url to list1
                return list2 that removes duplicates
                loop list2
                    for each el list1.count(el)
                    ratio = count / total page_links
                    add el to _link_ratios dict { url: ratio }
            add ratio key / val to the subpage
            '''
            _ratio = 0
            try:
                domain = extract_url(link)
                pg_obj = _pages[parent_url]
                page_links_total = pg_obj[0]['page_links']
                i = 1
                obj = pg_obj[i]
                while i < len(pg_obj):
                    _link_list.append(pg_obj[i]['link'])
                    i += 1
                num_links = _link_list.count(link)
                ratio = round(num_links / page_links_total, 1)
                return ratio
            except Exception as e:
                print(e)

        def truncate_str(url):
            x = str(os.statvfs('/')).split('=')
            y = x[len(x) - 1]
            filename_maxlength = int(''.join(list(filter(str.isdigit, y))))
            url_length = len(url)
            return (url[:filename_maxlength]) if url_length > filename_maxlength else url

        def remove_page_links():
            try:
                js = []
                for pg in _pages:
                    for p in _pages[pg]:
                        if p.get('page_links') is None:
                            ratio = calculate_ratios(p['link'], pg)
                            p['ratio'] = ratio
                            p['link'] = truncate_str(p['link'])
                            js.append(p)
                return js
            except Exception as e:
                print(e)

        try:
            pages = remove_page_links()
            j = json.loads(pages.__str__().replace("'", '"'))
            with open('output.tsv', 'w') as output_file:
                dw = csv.DictWriter(output_file, j[0].keys(), delimiter='\t')
                dw.writeheader()
                dw.writerows(j)
        except Exception as e:
            print(e)

    def logError(self, error):
        logging.error(error)
        traceback.print_exc(file=sys.stdout)

    def log(self, msg):
        logging.info(msg)

    def logDebug(self, msg):
        logging.debug(msg)

    def print(self,msg):
        print(msg)
