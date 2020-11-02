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
# If you are using BitSky Desktop Application, check https://docs.bitsky.ai/how-tos/how-to-get-bitsky-port-number-in-desktop-application
BITSKY_BASE_URL = environ.get('BITSKY_BASE_URL') or 'http://localhost:9099'
# You MUST change to correct Retailer Configuration Global ID
GLOBAL_ID = environ.get('GLOBAL_ID') or 'bf9f0118-8456-4f05-b6a6-bcf747acb5f8'
# path of crawled blogs
BLOGS_CSV_PATH = './static/blogs.csv'
# crawled blog fileds
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

# Implement Initial Tasks RESTFul API
# Doc - https://docs.bitsky.ai/api/retailer-restful-api#initial-tasks-optional
@app.route('/apis/tasks/trigger', methods=['GET'])
def trigger():
    return sendToBitSky([{
        # Target website URL
        'url': "http://exampleblog.bitsky.ai/",
        # Priority of this task. This is useful if your tasks need to be executed by order. `1` is highest priority
        'priority': 1,
        'retailer': {
            'globalId': GLOBAL_ID
        },
        # Additional metadata for this task, you should add it based your requirement. `script` is preserved, it only used for pass JavaScript Code String
        # In this example, I use `type` to distinguish different page - `bloglist` or `blog`. 
        # If it is `bloglist` then get all blog links and add new tasks to continues crawl those blogs, otherwise save blog to JSON
        # 
        # In this example, I let page to wait 5 second, this isn't necessary, only used for show you how to execute JavaScript Code. 
        # `script` is useful to crawl single page application or you need to interact with page. And only `Headless Producer` can execute tasks have script
        # `script` is the JavaScript Code you want to execute, you need to convert your function to string. Normally you can use `functionName.toString()`
        'metadata': {
            'type': "bloglist",
            # Check more detail https://docs.bitsky.ai/how-tos/how-to-execute-javascript-in-browser
            'script': '''
                async function customFunction() {
                    await $$page.waitFor(5 * 1000);
                }
            '''
        }
    }])

# Implement Receive Tasks RESTFul API
# Doc - https://docs.bitsky.ai/api/retailer-restful-api#receive-tasks
@app.route('/apis/tasks', methods=["POST"])
def parse():
    # https://flask.palletsprojects.com/en/1.1.x/api/#flask.Request.get_json
    returnTasks = request.get_json()
    tasks = []
    # crawled blogs
    crawledBlogs = []
    targetBaseURL = "http://exampleblog.bitsky.ai"
    for i in range(len(returnTasks)):
        # Schema of Task: https://raw.githubusercontent.com/bitskyai/bitsky-supplier/develop/src/schemas/task.json
        task = returnTasks[i]
        htmlString = task['dataset']['data']['content']
        type = task['metadata']['type']
        # You can find how to use Beautiful Soap from https://www.crummy.com/software/BeautifulSoup/bs4/doc/#
        # Beautiful Soup: A Python library for pulling data out of HTML and XML files
        soup = BeautifulSoup(htmlString, 'html.parser')
        if type == 'bloglist':
            # If task type is **bloglist**, then need to get blog link 
            # Get more detail from https://docs.bitsky.ai/tutorials/crawl-example-blog#crawl-each-blog-list-page-and-get-blogs-link
            blogUrls = soup.select("div.post-preview a")
            for j in range(len(blogUrls)):
                blog = blogUrls[j]
                blogURL = blog.get('href')
                # Get blog page link, don't forget to add Base URL
                blogURL = urljoin(targetBaseURL, blogURL)
                # Add Task to crawl blog page
                tasks.append({
                    'url': blogURL,
                    # Set `priority` to `2`, so we can first crawl all blog list page, then crawl all blogs
                    'priority': 2,
                    'retailer': {
                        'globalId': GLOBAL_ID
                    },
                    'metadata': {
                        # Add `type: "blog"` to indicate this task is for crawl blog
                        'type': "blog"
                    }
                })
            # Get next blog list page link. https://docs.bitsky.ai/tutorials/crawl-example-blog#crawl-each-blog-list-page-and-get-blogs-link
            nextURL = soup.select("ul.pager li.next a")
            if len(nextURL):
                nextURL = nextURL[0]
                nextURL = nextURL.get('href')
                nextURL = urljoin(targetBaseURL, nextURL)
                # If it has next blog list page, then create a Task to crawl Next Blog List page
                tasks.append({
                    'url': nextURL,
                    # blog list page is highest priority
                    'priority': 1,
                    'retailer': {
                        'globalId': GLOBAL_ID
                    },
                    'metadata': {
                        # indicate this task is for crawl blog list page
                        'type': "bloglist",
                        # Just to show you how to execute JavaScript in the browser
                        'script': '''
                            async function customFunction() {
                                await $$page.waitFor(5 * 1000);
                            }
                        '''
                    }
                })

        elif type == 'blog':
            # If it is blog page, then crawl data and save to blogs.csv
            crawledBlogs.append({
                'title': soup.select("div.post-heading h1")[0].get_text(),
                'author': soup.select("div.post-heading p.meta span.author")[0].get_text(),
                'date': soup.select("div.post-heading p.meta span.date")[0].get_text(),
                'content': soup.select("div.post-container div.post-content")[0].get_text(),
                'url': task['dataset']['url']
            })

        else:
            print('unknown type')

    # Send Tasks that need to be executed to BitSky
    if len(tasks):
        sendToBitSky(tasks)
    # Save crawled data to 
    if len(crawledBlogs):
        writeToBlogCSV(crawledBlogs)
    return 'successful'

# Implement health check RESTFul API
# Doc - https://docs.bitsky.ai/api/retailer-restful-api#health-check
@app.route('/health', methods=['GET'])
def health():
    return 'running'

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
