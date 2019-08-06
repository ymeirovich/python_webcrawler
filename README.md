# python_webcrawler
My first python webcrawler built without a framework but uses BeautifulSoup.

<b>4 cli arguments</b>

originalUrl : (required) string - root url

depthLimit: (required) integer - desired depth 

startWithJson: (optional) boolean - if false, output json is always overwritten, if true will look for current 'outputToJson.json' file first and merge that with any new output. The json file is continually written to so that if the process is terminated any previous output will be skipped / pulled from cache.

delay: (optional) integer - minute of the hour to start the crawl. If, for example, 'delay=23' then if the current time is 13:21 the main process will sleep / loop every 30 seconds until the time is 13:23 before starting. This way the process can start at a later time.

&gt;&gt;&gt;python Main.py originUrl=http://quotes.toscrape.com depthLimit=2 startWithJson=true delay=23

<b>Dependencies</b>

BeautifulSoup<br/>
Request-Cache -  used to cache pages, can set the expiration time, stores in sqlite<br/>
urllib3<br/>

<b>Output</b>

outputToJson.json - main record storage
output.tsv - final url, deph,ratio records


Github repo:  https://github.com/ymeirovich/python_webcrawler


