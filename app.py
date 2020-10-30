import json
# Third part libraries
from flask import Flask, request
import requests
from bs4 import BeautifulSoup


app = Flask(__name__)

BITSKY_BASE_UR = 'http://localhost:9099'
GLOBAL_ID = '0a88925d-418f-4fdf-8fe5-4176669f6938'

storeData = []


def sendToBitSky(tasks):
    # res = requests.post(f"{BITSKY_BASE_UR}/apis/tasks", data=json.dumps(tasks))
    res = requests.post(f"{BITSKY_BASE_UR}/apis/tasks", json=tasks)
    return json.dumps(res.json())


@app.route('/health', methods=['GET'])
def health():
    return 'running'


@app.route('/apis/tasks', methods=["POST"])
def parse():
    returnTasks = request.get_json()
    tasks = []
    targetBaseURL = "http://exampleblog.bitsky.ai"
    for i in range(len(returnTasks)):
        task = returnTasks[i]
        htmlString = task['dataset']['data']['content']
        type = task['metadata']['type']
        soup = BeautifulSoup(htmlString, 'html.parser')
        if type == 'bloglist':
            print('bloglist')
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
            storeData.append({
                'title': soup.select("div.post-heading h1")[0].get_text(),
                'author': soup.select("div.post-heading p.meta span.author")[0].get_text(),
                'date': soup.select("div.post-heading p.meta span.date")[0].get_text(),
                'content': soup.select("div.post-container div.post-content")[0].get_text(),
                'url': task['dataset']['url']
            })

        else:
            print('unknown type')

    sendToBitSky(tasks)
    print(storeData)
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
