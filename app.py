# python built-in module: json - JSON encoder and decoder. https://docs.python.org/3/library/json.html
import json
# python built-in module: csv - CSV File Reading and Writing. https://docs.python.org/3/library/csv.html
import csv
# python build-in module: os.environ. Get environment variable
from os import environ
################################################################
# Third part libraries
# `flash`: The Python micro framework for building web applications
# https://flask.palletsprojects.com/en/1.1.x/
from flask import Flask, request
# `requests`: HTTP for Humans
# https://requests.readthedocs.io/en/master/
import requests
# `beautifulsoup4`: A Python library for pulling data out of HTML and XML files
# Python web scraping beautifual soup: https://www.scrapingbee.com/blog/python-web-scraping-beautiful-soup/
# https://www.crummy.com/software/BeautifulSoup/bs4/doc/
from bs4 import BeautifulSoup


app = Flask(__name__)

BITSKY_BASE_URL = environ.get('BITSKY_BASE_URL') or 'http://localhost:9099'
GLOBAL_ID = environ.get('GLOBAL_ID') or '0a88925d-418f-4fdf-8fe5-4176669f6938'
BLOGS_CSV_PATH = './static/blogs.csv'
FIELD_NAMES = ['title', 'author', 'date', 'content', 'url']


def sendToBitSky(tasks):
    # res = requests.post(f"{BITSKY_BASE_URL}/apis/tasks", data=json.dumps(tasks))
    res = requests.post(f"{BITSKY_BASE_URL}/apis/tasks", json=tasks)
    return json.dumps(res.json())


def writeToBlogCSV(blogs, blog_csv_path=BLOGS_CSV_PATH, fieldnames=FIELD_NAMES, header=False):
    with open(blog_csv_path, mode='a') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if header:
            writer.writeheader()    # add column names in the CSV file
        writer.writerows(blogs)


# init blogs.csv with header
writeToBlogCSV(blogs=[], header=True)


@app.route('/health', methods=['GET'])
def health():
    return 'running'


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
