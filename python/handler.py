import time
import requests
import threading
import logging
import random
from fake_useragent import UserAgent
from stem.control import Controller
from stem import Signal
from urllib.parse import urlparse

# Local imports
from utils.config import Configuration
import detector
from exceptions import InvalidCookieException, HTTPStatusCodeError

logger = logging.getLogger("CRATOR")
MAX_CONNECTION_ATTEMPT = 3
NEW_REQUEST_DELAY = 2


class TorHandler:
    def __init__(self):
        config = Configuration()
        http_proxy = config.http_proxy()
        self.proxy = {"http": http_proxy, "https": http_proxy}
        self.lock = threading.Lock()

        self.n_requests_sent = 0

    def get_random_useragent(self):
        ua = UserAgent()
        return ua.random

    def send_request(self, url, cookie=None):
        if self.lock.locked():
            logger.debug("TOR HANDLER - Waiting for a new ip.")
        while self.lock.locked():
            time.sleep(1)

        # attempt = 0
        # web_page = None
        # status_code = 200

        logger.debug(f"TOR HANDLER - Downloading URL: {url}")

        header = {'User-Agent': self.get_random_useragent()}
        if cookie:
            header["Cookie"] = cookie

        web_page = requests.get(url, headers=header, proxies=self.proxy)
        status_code = web_page.status_code
        logger.debug(f"TOR HANDLER - STATUS CODE: {status_code}")
        self.n_requests_sent += 1

        # while not web_page and attempt < MAX_CONNECTION_ATTEMPT:
        #
        #
        #     # Check if the request has been succeeded
        #     if not(200 <= status_code < 300):
        #         logger.debug(f"TOR HANDLER - Status code {status_code}. New request attempt in {NEW_REQUEST_DELAY}s")
        #         status_code = web_page.status_code
        #         web_page = None
        #         attempt += 1
        #         time.sleep(NEW_REQUEST_DELAY)

        # if attempt >= MAX_CONNECTION_ATTEMPT:
        #     raise HTTPStatusCodeError(status_code)

        return web_page

    def is_url_reachable(self, url, cookie=None):
        """
        Check if a url is reachable
        :param url: the url to analyze. It can be with or without scheme
        :param cookie: a valid cookie session
        :return: true if a url is reachable, false otherwise.
        """
        # Check schema: if no schema ahs been found, set an http schema
        logger.debug(f"TOR HANDLER - URL CHECK: {url}")

        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            url = "http://" + url

        try:
            self.send_request(url, cookie=cookie)
            logger.debug(f"TOR HANDLER - URL CHECK: TRUE")
            return True
        except ConnectionError:
            pass

        logger.debug(f"TOR HANDLER - URL CHECK: FALSE")
        return False

    def renew_connection(self):
        with self.lock:
            logger.debug("TOR HANDLER - New ip generation...")
            header = {'User-Agent': self.get_random_useragent()}
            ip = requests.get('https://ident.me', proxies=self.proxy, headers=header).text
            logger.debug(f"TOR HANDLER - Actual IP: {ip}")
            # print(f"TOR HANDLER - Actual IP: {ip}")

            # Send a request to tor asking for a new ip
            with Controller.from_port(port=9051) as controller:
                controller.authenticate(password='N0nn0')
                controller.signal(Signal.NEWNYM)

            # Check if the ip has been changed
            new_ip = self.get_ip()
            while new_ip == ip:
                time.sleep(1)
                new_ip = self.get_ip()

            logger.debug(f"TOR HANDLER - New IP: {new_ip}")
            # print(f"TOR HANDLER - New IP: {new_ip}")

    def get_ip(self):
        header = {'User-Agent': self.get_random_useragent()}
        return requests.get('https://ident.me', proxies=self.proxy, headers=header).text


class CookieHandler:
    def __init__(self, seed, torhandler):
        self.config = Configuration()

        self.seed = seed
        self.tor_handler = torhandler
        self.nocookiepage = None

        self.bucket_cookies = None
        self.cookies = None

    @property
    def nocookiepage(self):
        return self._nocookiepage

    @nocookiepage.setter
    def nocookiepage(self, page):
        self._nocookiepage = page

    def is_valid(self, url, cookie):
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            url = "http://" + url

        try:
            web_page = self.tor_handler.send_request(url, cookie)
            if self.nocookiepage and detector.login_redirection(web_page, self.nocookiepage):
                logger.info(f"{self.seed} COOKIE HANDLER - Validity CHECK: False -> Login redirection")
                return False
            if detector.captcha_detector(url, web_page):
                logger.info(f"{self.seed} COOKIE HANDLER - Validity CHECK: False -> Captcha")
                return False
        except Exception as e:
            logger.error(f"{self.seed} COOKIE HANDLER - Error msg: {str(e)}")
            return False

        return True

    def cookies_validity_check(self, url):
        logger.info(f"{self.seed} COOKIE HANDLER - Cookies validity check ")
        if not self.cookies or self.config.is_updated():
            try:
                self.cookies = self.config.cookies(self.seed)
                # self.cookies = market_config.get_cookies(self.market)
            except:
                error_msg = "No cookies found in the market config file"
                logger.error(f"{self.seed} COOKIE HANDLER - {error_msg}")
                raise FileNotFoundError(error_msg)

        if not self.cookies:
            error_msg = "Empty list in the market config file. Please update it with at least one valid cookie."
            logger.error(f"{self.seed} COOKIE HANDLER - {error_msg}")
            raise InvalidCookieException(error_msg)

        for cookie in self.cookies:
            logger.info(f"{self.seed} - Cookie validity check")
            logger.info(f"{self.seed} - Cookie: {cookie}")

            if not self.is_valid(url, cookie):
                logger.info(f"{self.seed} - INVALID COOKIE")
                self.remove_cookie(cookie)
            else:
                logger.info(f"{self.seed} - VALID COOKIE")

    def get_random_cookie(self, url, validity_check=True):
        # Check if there are cookies in the cookie list. If not, read them from the market config file.
        if not self.cookies or self.config.is_updated():
            try:
                self.cookies = self.config.cookies(self.seed)
                # self.cookies = market_config.get_cookies(self.market)
                if not self.cookies:
                    # raise InvalidCookieException("Empty list in the market config file. "
                    #                              "Please update it with at least one valid cookie.")
                    return None
            except:
                raise FileNotFoundError("No cookies found in the market config file")

        # Bucket cookies list is empty because all the cookies have already been chosen.
        # Replenish the bucket with the cookies saved in the market config file
        if not self.bucket_cookies:
            self.bucket_cookies = self.cookies.copy()

        logger.debug(f"{self.seed} COOKIE HANDLER - RANDOM COOKIE -> COOKIE LIST")
        [logger.debug(f"{self.seed} - {ck}") for ck in self.cookies]
        logger.debug(f"{self.seed} COOKIE HANDLER - RANDOM COOKIE -> BUCKET COOKIE LIST")
        [logger.debug(f"{self.seed} - {ck}") for ck in self.bucket_cookies]

        if not validity_check:
            random_index = random.randint(0, len(self.bucket_cookies) - 1)  # generate a random index
            return self.bucket_cookies.pop(random_index)  # remove the element at the random index

        # Cookie validity check
        while self.bucket_cookies:
            random_index = random.randint(0, len(self.bucket_cookies) - 1)  # generate a random index
            random_cookie = self.bucket_cookies.pop(random_index)  # remove the element at the random index

            logger.debug(f"{self.seed} COOKIE HANDLER - RANDOM COOKIE -> BUCKET COOKIE LIST (UPDATE)")
            [logger.debug(f"{self.seed} - {ck}") for ck in self.bucket_cookies]

            if self.is_valid(url, random_cookie):
                return random_cookie
            else:
                # Remove the invalid cookie from the list and in the market config file
                self.remove_cookie(random_cookie)

            if not self.bucket_cookies:
                self.bucket_cookies = self.cookies.copy()

        return None

    def remove_cookie(self, cookie):
        """
        Remove the cookie from the list and in the market config file
        """
        try:
            logger.debug(f"{self.seed} - REMOVE COOKIE")
            logger.debug(f"{self.seed} - COOKIE LIST")
            [logger.debug(f"{self.seed} - BEFORE: {cookie}") for cookie in self.cookies]
            self.cookies.remove(cookie)
            [logger.debug(f"{self.seed} - AFTER: {cookie}") for cookie in self.cookies]

            self.config.remove_cookie(self.seed, cookie)
            # market_config.remove_cookie(self.market, cookie)
        except ValueError as ve:
            logger.error(f"{self.seed} - COOKIE TO REMOVE NOT FOUND.")
            logger.error(f"{self.seed} - Error msg: {str(ve)}.")


if __name__ == '__main__':
    handler = TorHandler()
    handler.renew_connection()
