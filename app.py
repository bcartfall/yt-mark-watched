import logging, sys, time, os, json
from logging.handlers import RotatingFileHandler

from threads import browser

#import undetected_chromedriver as uc

# setup logger
script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = script_dir + '/data'
if not os.path.exists(data_dir):
    os.makedirs(data_dir)

logger = logging.getLogger('yt-mark-watched')
handler = RotatingFileHandler(data_dir + '/mark-watched.log', maxBytes=10 * 1024 * 1024, backupCount=8)
formatter = logging.Formatter('%(asctime)s,%(msecs)03d %(levelname)-8s %(message)s [%(filename)s:%(lineno)d]')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

stdout_handler = logging.StreamHandler(stream=sys.stdout)
stdout_handler.setFormatter(formatter)
logger.addHandler(stdout_handler)

from waitress import serve
from flask import Flask
from flask_cors import CORS
from flask import request, jsonify, render_template, Response

app = Flask("yt-mark-watched")
cors = CORS(app) # enable cross-origin on all requests

@app.route('/')
def index() -> Response:
    webDriverStatus = browser.driverStatus()
    return render_template('index.html', webDriverStatus=webDriverStatus)

@app.post('/api/videos/mark-watched')
def api_add() -> Response:
    content = request.get_json(silent=True)
    url = content['url']
    logger.debug(f'/api/videos/mark-watched url={url}')
    if (browser.addToWatched(url)):
        return jsonify(
            message="URL added.",
            url=url,
        )
    return "Error adding url", 500

@app.post('/api/cookies/update')
def api_cookies_update() -> Response:
    cookies = request.data
    logger.debug(f'/api/cookies/update cookies_len={len(cookies)}')
    
    # save cookies to file
    with open(script_dir + '/data/cookies.txt', 'w') as file:
        file.write(cookies.decode('utf-8'))
    
    # update cookies in driver
    browser.reloadCookies()
    
    return jsonify(
        message='Cookies updated.',
    )
    
@app.get('/api/logs')
def api_logs() -> Response:
    
    l = request.args.get('l', '')
    n = int(request.args.get('n', '20'))

    with open(script_dir + '/data/mark-watched.log', 'r') as f:
        logs = tail(f, lines=n)
        if (l != ''):
            # remove anything older than last (l)
            nLogs = []
            for line in logs:
                s = line.split(" ")
                if (s[0] + ' ' + s[1] > l):
                    nLogs.append(line)
            logs = nLogs
    return jsonify(
        logs=logs
    )

def tail(f, lines=1, _buffer=4098) -> list:
    """Tail a file and get X lines from the end"""
    # place holder for the lines found
    lines_found = []

    # block counter will be multiplied by buffer
    # to get the block size from the end
    block_counter = -1

    # loop until we find X lines
    while len(lines_found) < lines:
        try:
            f.seek(block_counter * _buffer, os.SEEK_END)
        except IOError:  # either file is too small, or too many lines requested
            f.seek(0)
            lines_found = f.readlines()
            break

        lines_found = f.readlines()

        # decrement the block counter to get the
        # next X bytes
        block_counter -= 1

    return lines_found[-lines:]

if __name__ == "__main__":
    try:
        # start threads
        browser.run()
        
        host = os.environ.get('APP_HOST', '0.0.0.0')
        port = int(os.environ.get('APP_PORT', '5002'))
        logger.info(f"Running yt-mark-watched server http://{host}:{str(port)}")
        
        serve(app, host=host, port=port)
        #app.run(host=host, port=port, debug=False, use_reloader=False)
    finally:
        logger.info("Stopping server.")
        browser.close()        