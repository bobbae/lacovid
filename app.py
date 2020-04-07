from bot.lacovidbot import Lacovidbot
from flask import (Flask,render_template,request,Response,jsonify)
from scrapy.crawler import CrawlerRunner
import logging
import crochet
import json
from logging.handlers import RotatingFileHandler

crochet.setup()

app = Flask(__name__)

crawl_runner = CrawlerRunner()

lacovidlist= []
scrape_in_progress=False
scrape_complete=False
logging.basicConfig(level=logging.DEBUG)

empty_data={"data": [{"city": "not ready", "cases":0,"rate":0}]}

handler = RotatingFileHandler('lacovid.log',maxBytes=10000,backupCount=1)
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.info('starting')


@app.route('/')
def myindex():
    global lacovidlist
    app.logger.info("myindex")
    return render_template("index.html",data=json.dumps(empty_data), flask_token="la covid info")
    
@app.route('/table')
def rendertable():
    data={ "data": lacovidlist}
    return render_template("index.html", data=json.dumps(data),flask_token="la covid info")

@app.route('/crawl')
def crawl_for_covidinfo():
    global scrape_in_progress
    global scrape_complete

    if not scrape_in_progress:
        scrape_in_progress=True
        global lacovidlist
        scrape_with_crochet(lacovidlist)
        app.logger.info("scraping")
        return 'SCRAPING'
    elif scrape_complete:
        app.logger.info("scrape complete")
        return 'SCRAPE_COMPLETE'
    app.logger.info("scrape in progress")
    return 'SCRAPE_IN_PROGRESS'

@app.route('/results')
def results():
    global scrape_complete
    global lacovidlist
    if scrape_complete:
        return json.dumps({ "data": lacovidlist})
    if scrape_in_progress:
        app.logger.info("work in progress")
        return 'Work in progress'
    return 'Run crawler first'

@app.route('/get_results')
def get_results():
    global scrape_complete
    global lacovidlist
    global empty_data
    if scrape_complete:
        data={ "data": lacovidlist}
        return jsonify(data)
    return empty_data

@crochet.run_in_reactor
def scrape_with_crochet(_list):
    app.logger.info("start crawler")
    eventual = crawl_runner.crawl(Lacovidbot, alist = _list, alogger = app.logger)
    eventual.addCallback(finished_scrape)

def finished_scrape(null):
    global scrape_complete
    scrape_complete=True
    app.logger.info("scrape complete")

@app.route('/message', methods = ['POST'])
def message_post():
    if "Content-Type" in request.headers:
        pass
    else:
        return "No content type"
    if request.headers['Content-Type'] == 'text/plain':
        msg = request.data
        return "Text message: " + msg
    if request.headers['Content-Type'] == 'application/json':
        msg = request.json
        return "JSON message: " + json.dumps(msg)
    if request.headers['Content-Type'] == 'application/octet-stream':
        f = open('./binarydata.bin', 'wb')
        f.write(request.data)
        f.close()
        return 'Binary message written'
    return '415 unsupported media type'

@app.route('/start_crawling', methods=['POST'])
def start_crawling():
    crawl_for_covidinfo()
    resp = Response('OK',status=200, mimetype='application/json')
    return resp

if __name__=='__main__':
    app.run('0.0.0.0', 5000)
