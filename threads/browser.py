"""
 * Developed by Hutz Media Ltd. <info@hutzmedia.com>
 * Copyright 2025-04-07
 * See README.md
"""

import threading
import time
import os
import json

from selenium.webdriver.remote.webdriver import WebDriver
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import logging
logger = logging.getLogger('yt-mark-watched')

script_dir = os.path.dirname(os.path.realpath(__file__)) + "/.."
hidden = os.environ.get("MW_HIDDEN", "true").lower() in ["true", "1", "yes"]

platform = os.environ.get("MW_PLATFORM", "desktop")

class BrowserThread:
    _running: bool = True
    _driver: WebDriver = None
    _driverStart: float = 0
    _driverMutex: threading.Lock = threading.Lock()
    _queue: list = []
    _queueMutex: threading.Lock = threading.Lock()
    
    def run(self) -> None:
        t = time.time()
        while (self._running):
            self._markWatched()
            if (time.time() - t > 300):
                # run garbage collection every 5 minutes
                t = time.time()
                self._gc()
            time.sleep(0.1) # 10hz
            
    def _gc(self) -> None:
        # garbage collect
        logger.debug("browser._gc()")
        t = time.time()
        with self._driverMutex:
            if (self._driver != None):
                if (t - self._driverStart > 10800):
                    logger.debug("Closing web driver")
                    # close webdriver every 3 hours
                    self._driver.close()
                    self._driverStart = t
                    self._driver = None
                
            
    def _addToWatched(self, url: str) -> bool:
        logger.info("adding url to list url=" + url)
        with (self._queueMutex):
            self._queue.append(url)
        return True
    
    def _reloadDriver(self) -> WebDriver:
        # clear driver
        logger.info("browser._reloadDriver()")
        with self._driverMutex:
            if (self._driver != None):
                self._driver.close()
            self._driver = None
        return self._getDriver()
    
    def _reloadCookies(self) -> bool:
        self._getDriver()
        with self._driverMutex:
            # clean cookies
            self._driver.delete_all_cookies()
            
            # reload cookies from file
            cookieFile = script_dir + "/data/cookies.txt"
            if (os.path.exists(cookieFile)):
                with open(cookieFile) as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    d = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                    }
                    self._driver.add_cookie(d)
        return True
            
    def _getDriver(self) -> WebDriver: 
        with self._driverMutex:
            # driver already loaded
            if (self._driver != None):
                return self._driver
            
            logger.debug(f"starting webdriver hidden={str(hidden)}, platform={platform}")
        
            # load firefox driver
            options = webdriver.FirefoxOptions()
            if (hidden):
                options.add_argument("--headless") # headless
            options.set_preference("media.volume_scale", "0.0") # mute
            
            if (platform == "mobile"):
                options.set_preference("general.useragent.override", "Mozilla/5.0 (iPhone; CPU iPhone OS 17_7_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) FxiOS/137.0 Mobile/15E148 Safari/605.1.15")
        
            self._driver = webdriver.Firefox(options)
            self._driver.install_addon(script_dir + "/extensions/ublock_origin-1.63.2.xpi")
            
            # load youtube so we can set cookies
            self._driver.get("https://www.youtube.com")
            
            # cookies
            cookieFile = script_dir + "/data/cookies.txt"
            if (os.path.exists(cookieFile)):
                with open(cookieFile) as f:
                    cookies = json.load(f)
                for cookie in cookies:
                    d = {
                        'name': cookie['name'],
                        'value': cookie['value'],
                    }
                    self._driver.add_cookie(d)
            self._driverStart = time.time()
        return self._driver
    
    def _driverStatus(self) -> str:
        status = 'UNKNOWN'
        with self._driverMutex:
            if (self._driver == None):
                status = 'STOPPED'
            else:
                status = f'RUNNING ({round(time.time() - self._driverStart)}s)'
        return status

    def _markWatched(self) -> None:
        # mark next item watched
        with (self._queueMutex):
            if len(self._queue) == 0:
                # no items on list
                return
            item = self._queue.pop(0)
            
        # prepare browser
        driver = self._getDriver()
            
        with (self._driverMutex):
            logger.info("marking as watched url=" + item)
            driver.get(item)  
            body = driver.find_element(By.XPATH, "//body")
            
            # wait for meta data to be loaded
            if (platform == "mobile"):
                waitClass = "yt-core-attributed-string"
            else:
                waitClass = "ytd-watch-metadata"
            
            try:    
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, waitClass))
                )
            except:
                logger.warning(f"{waitClass} class not found")
                
            if (platform == "mobile"):
                # mobile plays automatically
                time.sleep(3)
                
                # pause video
                element = driver.find_element(By.CLASS_NAME, "player-container")
                element.click() # click to unmute and present controls
                
                # click to pause
                element = driver.find_element(By.CLASS_NAME, "player-control-play-pause-icon")
                element.click()
                time.sleep(1)
            else:
                # send space bar to play
                body.send_keys(Keys.SPACE)
                time.sleep(3)
                
                # send space bar to pause
                body.send_keys(Keys.SPACE)
                time.sleep(1)
                
            logger.debug("done url=" + item)
        return

THREAD = BrowserThread()

def _runThread():
    THREAD.run()

def run() -> None:
    logger.debug('browser run()')
    t = threading.Thread(target=_runThread)
    t.start()
    
def reloadDriver() -> WebDriver:
    return THREAD._reloadDriver()

def reloadCookies() -> bool:
    return THREAD._reloadCookies()

def addToWatched(url: str) -> bool:
    return THREAD._addToWatched(url)

def driverStatus() -> str:
    return THREAD._driverStatus()

def close() -> None:
    logger.debug('browser close()')
    THREAD._running = False