import random
import logging
import sys
import time
from datetime import datetime
import hashlib
from waiting import wait
from waiting.exceptions import TimeoutExpired
import os
from collections import deque
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

# Local imports
from handler import TorHandler, CookieHandler
from monitor import CrawlerMonitor
from detector import captcha_detector, login_redirection
from downloader import Downloader
from saver import FileSaver
from utils.config import Configuration
import utils.fileutils as file_utils
from exceptions import InvalidURLException, HTTPStatusCodeError

MAX_RETRIES = 3
MAX_COOKING_WAITING_TIME = 36000     # 10 hours

logger = logging.getLogger("CRATOR")


class Crawler:
    """
    Crawler for tor onion links
    """
    def __init__(self, seed, tor_handler=None):
        """
        Initialize the class crawler
        :param seed: the url to crawl
        :param tor_handler: an instance of the TorHandler class, useful when the crawler is executed in a multithread
        environment and the tor requests must be shared among the threads (e.g., if a webpage contains
        a captcha, the handler requests a new ip, blocking all the connections until the new ip.
        """
        self.config = Configuration()
        self.max_link = self.config.max_links()
        self.max_crawl_time = self.config.max_time()
        self.max_depth = self.config.max_depth()
        self.wait_request = int(self.config.wait_request()) / 1000
        self.max_retries = 5
        self.retries_counter = 0
        self.max_retries_before_renew = 5

        self.seed = seed
        self.login_page = None
        self.retry_queue = {}

        self.tor_handler = tor_handler
        if not self.tor_handler:
            self.tor_handler = TorHandler()
        self.actual_ip = self.tor_handler.get_ip()

        self.downloader = Downloader(5, torhandler=self.tor_handler, waiting_time=self.wait_request)
        self.downloader.start()

        self.cookie_handler = None
        if self.config.has_cookies(seed):
            self.cookie_handler = CookieHandler(self.seed, self.tor_handler)

            self.bucket_cookies = None
            self.cookies = None
            self.cookie_wait = False

        # Config info
        data_dir = self.config.data_dir()

        # - Project directory
        today_tms = datetime.now().strftime("%Y%m%d")
        project_name = f"{self.config.project_name()}-{today_tms}"
        project_path = os.path.join(data_dir, project_name)

        if os.path.exists(project_path):
            error_msg = f"Error: The project folder '{project_name}' already exists."
            raise FileExistsError(error_msg)

        os.makedirs(project_path, exist_ok=True)

        # Pages folder
        self.page_path = os.path.join(project_path, "pages")
        os.makedirs(self.page_path)

        self.monitor = CrawlerMonitor(project_path)
        self.monitor.start_scheduling()

        self.filesaver = FileSaver(self.page_path)
        self.filesaver.start()

    def require_cookies(self):
        return self.config.requires_cookies(self.seed)

    def get_info(self):
        return self.monitor.get_info()

    def get_webpage_url(self, webpage):
        if not webpage:
            return None

        if len(webpage.history) > 0:
            return webpage.history[-1].url

        return webpage.url

    def extract_internal_links(self, web_page):
        """
        This function, using Beautifulsoup4, search for all the internal links (links of the same website)
        in a web page.
        :param web_page: the web_page content retrieved from a request (return value of request.get function).
        :return: set() of url found in the web_page
        """
        logger.info(f"{self.seed} - Internal link extraction")

        request_url = web_page.request.url
        logger.debug(f"{self.seed} - Internal links - Request URL -> {request_url}")
        domain = urlparse(request_url).netloc

        # Make soup
        soup = BeautifulSoup(web_page.content, "html.parser", from_encoding="iso-8859-1")

        urls = set()

        # Get all internal links
        for a_tag in soup.findAll("a"):
            href = a_tag.attrs.get("href")
            href = urljoin(request_url, href).strip("/")
            # logger.debug(f"{self.market.upper()} - Internal links - Extracting link {href}")

            if href == "" or href is None:
                # href empty tag
                continue

            if urlparse(href).netloc != domain:
                # external link
                continue

            urls.add(href)

        return list(urls)

    def enqueue_url(self, url):
        # TOR request
        cookie = None

        if self.require_cookies():
            # Try to acquire a new cookie
            cookie = self.cookie_handler.get_random_cookie(url, validity_check=False)

            # No cookies in yml file. Wait new cookies
            if not cookie:
                cookie = wait(lambda: self.cookie_handler.get_random_cookie(url, validity_check=False),
                              sleep_seconds=1, timeout_seconds=MAX_COOKING_WAITING_TIME, waiting_for="waiting for new cookies.")

        self.downloader.enqueue(url, cookie)

    def validate(self, web_page):
        """
        Check if the url content is valid, without captchas or without any anomalous redirection.
        If something is found, then the cookie used for that page is removed.
        :param web_page: the web page to validate
        :return: True, is the page contains no captchas or anomalous redirect, False otherwise.
        """

        if not self.config.has_cookies(self.seed):
            return True

        captcha = captcha_detector(web_page.url, web_page)
        login_redirect = True
        if self.login_page:
            login_redirection(web_page, self.login_page)

        if login_redirect or captcha:
            if captcha:
                logger.info(f"{self.seed} - Captcha FOUND in link {web_page.url}. Request new cookie.")
            else:
                logger.info(f"{self.seed} - Redirection to login page. Cookie expired. Request new cookie.")

            return True

        return False

    def start(self):
        """
        Method to execute the crawler.
        :return: no return value. All the web_pages will be saved in a dump folder.
        """
        # Track visited URLs to avoid duplicates
        visited = {}
        unvisited_links = set()
        try:
            if not self.seed:
                logger.error(f"No valid seed -> {self.seed}")
                raise InvalidURLException(f"No valid seed -> {self.seed}")

            if self.config.has_cookies(self.seed):
                # Assumption: all the markets with no valid cookies redirect to the same page with the same url
                logger.info(f"{self.seed} - Send a request without cookie to store the login redirect url")

                self.login_page = self.tor_handler.send_request(self.seed)
                self.cookie_handler.nocookiepage = self.login_page
                # logger.info(f"{self.market.upper()} - URL no cookie default redirect -> {self.loginpage.url}")

                # Get a valid cookie among the cookies stored in the market configuration file
                self.cookie_handler.cookies_validity_check(self.seed)

            # Create a queue for BFS
            self.enqueue_url(self.seed)
            node_index = 0

            # Crawling iter condition
            # 1. all the urls are crawled
            # 2. if the cookie expiration time has been reached
            # 3. the maximum allowed number of links, defined in the config.ini file, has been reached
            # 4. expiration time defined in the config.ini file
            cookie_timeout = False
            start_time = time.time()
            n_links_crawled = 0
            url_depth = {self.seed: 0}
            url_attempts = {}

            while (not self.downloader.is_empty() and n_links_crawled < self.max_link and not cookie_timeout and
                   time.time() - start_time < self.max_crawl_time):

                try:
                    url_futures = self.downloader.get_results()
                    logger.debug(f"{self.seed} - CRAWLER: futures len -> {len(url_futures)}")

                    # If no pages are available, wait for the thread to complete.
                    if not url_futures:
                        time.sleep(0.1)
                        continue

                    self.monitor.update_tor_requests(self.tor_handler.n_requests_sent)

                    for url, future in url_futures:
                        try:
                            web_page = future.result()
                        except Exception as e:
                            logger.error(f"{self.seed} - Error while processing a webpage. SKIP.")
                            logger.error(f"{self.seed} - Error msg: {str(e)}")
                            url = self.downloader.get_future_url(future)
                            self.monitor.add_info_unvisited_page(int(time.time()), url, self.actual_ip, "ERROR")
                            continue

                        if not web_page:
                            continue

                        # Check if the page is valid or not.
                        if not self.validate(web_page):
                            if url not in url_attempts or url_attempts[url] < MAX_RETRIES:
                                url_attempts[url] = 1
                                self.enqueue_url(url)
                                logger.debug(f"{self.seed} - Error while downloading the url -> {url}. RETRY.")
                            else:
                                logger.error(f"{self.seed} - Error while downloading the url -> {url}. SKIPPED.")
                                self.monitor.add_info_unvisited_page(int(time.time()), url, self.actual_ip, "ERROR")

                        # STATUS CODE CHECK
                        if web_page.status_code < 200 or web_page.status_code >= 300:
                            self.monitor.add_info_page(int(time.time()), url, self.actual_ip, web_page.status_code)
                            continue

                        try:
                            internal_urls = self.extract_internal_links(web_page)
                            logger.debug(f"{self.seed} - Internal links: {len(internal_urls)}.")
                        except Exception as e:
                            logger.error(f"{self.seed} - Internal link extraction failed..")
                            logger.error(f"{self.seed} - Error msg: {str(e)}")
                            continue

                        try:
                            logger.debug(f"{self.seed} - URL: {url}.")
                            depth = url_depth[url]
                            logger.debug(f"{self.seed} - DEPTH: {depth}.")
                            del url_depth[url]
                        except Exception as e:
                            logger.error(f"{self.seed} - URL DEPTH.")
                            logger.error(f"{self.seed} - Error msg: {str(e)}")
                            raise e

                        if url not in visited:
                            visited[url] = node_index
                            self.monitor.add_node(url, node_index, depth, str(node_index)+".html")
                            node_index += 1

                        self.monitor.add_info_page(int(time.time()), url, self.actual_ip, web_page.status_code)

                        # Enqueue new links and add edges
                        for link in internal_urls:
                            # Skip the link if the deep level is at least equal to the max deep level (configuration
                            # setting)
                            if depth + 1 > self.max_depth:
                                logger.info(f"{self.seed} - URL {link}: depth value greater than {self.max_depth}. IGNORED.")
                                unvisited_links.add(link)
                                self.monitor.add_info_unvisited_page(int(time.time()), link, self.actual_ip, "MAX DEPTH")
                            else:
                                if link not in visited and link not in unvisited_links:
                                    url_depth[link] = depth + 1

                                    # Save scheduled page
                                    self.monitor.add_scheduled_page(int(time.time()), link, self.actual_ip, depth + 1)

                                    self.enqueue_url(link)
                                    visited[link] = node_index
                                    self.monitor.add_node(link, node_index, depth + 1, str(node_index)+".html")
                                    node_index += 1

                                self.monitor.add_edge(visited[url], visited[link])

                        # Save the html page
                        self.filesaver.enqueue(web_page, visited[url])

                        n_links_crawled += 1
                except TimeoutExpired as te:
                    logger.error(f"{self.seed} - Cookie timeout expired.")
                    logger.error(f"{self.seed} - Error msg: {str(te)}")
                    cookie_timeout = True

            if self.downloader.is_empty():
                logger.info(f"{self.seed} - Crawler END - All links have been crawled.")
            elif len(visited) >= self.max_link:
                logger.info(f"{self.seed} - Crawler END - The max_link set in the config.ini has been reached.")
            elif cookie_timeout:
                logger.info(f"{self.seed} - Crawler END - Cookie expiration time.")
            else:
                logger.info(f"{self.seed} - Crawler END - The max_crawl_time set in the config.ini has been reached.")
        except Exception as e:
            logger.error(f"{self.seed} - {str(e)}.")

        self.downloader.stop()
        self.filesaver.stop()
        self.monitor.stop_program()
