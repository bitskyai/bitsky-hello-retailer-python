# Hello Retailer Service
Use [python](https://www.python.org/) to implement [Crawl Example Blog](https://docs.bitsky.ai/tutorials/crawl-example-blog).

## How to start
1. Make sure you installed Python(>=3.8)
2. Install python packages. You can use [pipenv install](https://pipenv.pypa.io/en/latest/) or [pip install requirements.txt](https://packaging.python.org/tutorials/installing-packages/#id17)
3. Change `BITSKY_BASE_URL` and `GLOBAL_ID` inside `app.py`
4. `gunicorn app:app` to start server, by default, it will start [http://localhost:8000](http://localhost:8000)

If you don't know how to use BitSky, please check [BitSky Quick Start](https://docs.bitsky.ai/). 


## Heroku

You can simply deploy this app to Heroku by click this button:
[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/bitskyai/bitsky-hello-retailer-python/tree/main)