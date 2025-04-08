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
from flask import request, jsonify

app = Flask("yt-mark-watched")
cors = CORS(app) # enable cross-origin on all requests

@app.route('/')
def index():
    
    return f"<p>yt-mark-watched API</p><p>WebDriver is currently {browser.driverStatus()}"

@app.post('/api/videos/mark-watched')
def api_add():
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
def api_cookies_update():
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