# python built-in module: json - JSON encoder and decoder. https://docs.python.org/3/library/json.html
import json
# python built-in module: csv - CSV File Reading and Writing. https://docs.python.org/3/library/csv.html
import csv
# python build-in module: os.environ. Get environment variable
from os import environ
# Construct a full (“absolute”) URL by combining a “base URL” (base) with another URL (url)
# https://docs.python.org/3/library/urllib.parse.html#module-urllib.parse
from urllib.parse import urljoin
################################################################
# Third part libraries
# `flash`: The Python micro framework for building web applications
# https://flask.palletsprojects.com/en/1.1.x/
from flask import Flask, request, render_template
# `requests`: HTTP for Humans
# https://requests.readthedocs.io/en/master/
import requests
# `beautifulsoup4`: A Python library for pulling data out of HTML and XML files
# Python web scraping beautifual soup: https://www.scrapingbee.com/blog/python-web-scraping-beautiful-soup/
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from bs4 import BeautifulSoup


app = Flask(__name__)

# You MUST change to correct BitSKy Base URL
BITSKY_BASE_URL = environ.get('BITSKY_BASE_URL') or 'http://localhost:9099'
# You MUST change to correct Retailer Configuration Global ID
GLOBAL_ID = environ.get('GLOBAL_ID') or '0a88925d-418f-4fdf-8fe5-4176669f6938'
BLOGS_CSV_PATH = './static/blogs.csv'
FIELD_NAMES = ['title', 'author', 'date', 'content', 'url']


#========================================================================
# You can read https://docs.bitsky.ai/tutorials/crawl-example-blog to get detail understand what is the requirement of this example
#========================================================================

# Add Tasks to BitSky
# Doc - https://docs.bitsky.ai/api/bitsky-restful-api
def sendToBitSky(tasks):
    bitsky_url = urljoin(BITSKY_BASE_URL, '/apis/tasks')
    res = requests.post(bitsky_url, json=tasks)
    return json.dumps(res.json())

# Write crawled blog to disk as csv format
def writeToBlogCSV(blogs, blog_csv_path=BLOGS_CSV_PATH, fieldnames=FIELD_NAMES, header=False):
    with open(blog_csv_path, mode='a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if header:
            writer.writeheader()    # add column names in the CSV file
        writer.writerows(blogs)


# init blogs.csv with header
writeToBlogCSV(blogs=[], header=True)

# Implement health check RESTFul API
# Doc - https://docs.bitsky.ai/api/retailer-restful-api#health-check
@app.route('/health', methods=['GET'])
def health():
    return 'running'

# Implement Receive Tasks RESTFul API
# Doc - https://docs.bitsky.ai/api/retailer-restful-api#receive-tasks
@app.route('/apis/tasks', methods=["POST"])
def parse():
    returnTasks = request.get_json()
    tasks = []
    # crawled blogs
    crawledBlogs = []
    targetBaseURL = "http://exampleblog.bitsky.ai"
    for i in range(len(returnTasks)):
        task = returnTasks[i]
        htmlString = task['dataset']['data']['content']
        type = task['metadata']['type']
        soup = BeautifulSoup(htmlString, 'html.parser')
        if type == 'bloglist':
            blogUrls = soup.select("div.post-preview a")
            for j in range(len(blogUrls)):
                blog = blogUrls[j]
                blogURL = blog.get('href')
                blogURL = f'{targetBaseURL}{blogURL}'
                tasks.append({
                    'url': blogURL,
                    'priority': 2,
                    'retailer': {
                        'globalId': GLOBAL_ID
                    },
                    'metadata': {
                        'type': "blog"
                    }
                })
            nextURL = soup.select("ul.pager li.next a")
            if len(nextURL):
                nextURL = nextURL[0]
                nextURL = nextURL.get('href')
                nextURL = f'{targetBaseURL}{nextURL}'
                tasks.append({
                    'url': nextURL,
                    'priority': 1,
                    'retailer': {
                        'globalId': GLOBAL_ID
                    },
                    'metadata': {
                        'type': "bloglist",
                        'script': '''
                            async function customFunction() {
                                await $$page.waitFor(5 * 1000);
                            }
                        '''
                    }
                })

        elif type == 'blog':
            crawledBlogs.append({
                'title': soup.select("div.post-heading h1")[0].get_text(),
                'author': soup.select("div.post-heading p.meta span.author")[0].get_text(),
                'date': soup.select("div.post-heading p.meta span.date")[0].get_text(),
                'content': soup.select("div.post-container div.post-content")[0].get_text(),
                'url': task['dataset']['url']
            })

        else:
            print('unknown type')

    sendToBitSky(tasks)
    writeToBlogCSV(crawledBlogs)
    return 'successful'

# Implement Initial Tasks RESTFul API
# Doc - https://docs.bitsky.ai/api/retailer-restful-api#initial-tasks-optional
@app.route('/apis/tasks/trigger', methods=['GET'])
def trigger():
    return sendToBitSky([{
        'url': "http://exampleblog.bitsky.ai/",
        'priority': 1,
        'retailer': {
            'globalId': GLOBAL_ID
        },
        'metadata': {
            'type': "bloglist",
            'script': '''
                async function customFunction() {
                    await $$page.waitFor(5 * 1000);
                }
            '''
        }
    }])

# Implement a index page, help user to know trigger function and crawled data
@app.route('/', methods=['GET'])
def index():
    indexData = {
        'title': "Retailer Service",
        'description': 'A retailer server to crawl data from website',
        'triggerURL': "/apis/tasks/trigger",
        'crawledData': '/static/blogs.csv',
        'githubURL': "https://github.com/bitskyai",
        'homeURL': "https://www.bitsky.ai",
        'docURL': "https://docs.bitsky.ai",
        'copyright': "© 2020 BitSky.ai"
    }
    return render_template("index.html", indexData=indexData)
