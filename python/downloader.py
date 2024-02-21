import concurrent.futures
import os
import logging
import time
import threading
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from handler import TorHandler


logger = logging.getLogger("CRATOR")


class Downloader:
    def __init__(self, n_threads, torhandler, waiting_time=1.5):
        self.queue = deque()
        self.n_threads = n_threads
        self.waiting_time = waiting_time

        if torhandler and not isinstance(torhandler, TorHandler):
            raise TypeError("Invalid type for torhandler parameter. It must be a TorHandler class.")

        self.torhandler = torhandler
        self.running = True
        self.lock = threading.Lock()
        self.results = []
        self.futures = []

        self.future_url_map = {}

    def is_empty(self):
        # logger.debug(f"DOWNLOADER: Empty -> {not self.queue and not self.results}")
        return not self.queue and not self.futures

    def enqueue(self, url, cookie):
        self.queue.append((url, cookie))

    def has_results(self):
        if self.get_results():
            return True

        return False

    def get_future_url(self, future):
        if id(future) not in self.future_url_map:
            return None

        return self.future_url_map[id(future)]

    def get_results(self):
        # logger.debug(f"DOWNLOADER: Results: queue before -> {len(self.queue)}")
        completed_futures = [future for future in concurrent.futures.as_completed(self.futures)]

        # Update self.futures to remove completed futures
        self.futures = [future for future in self.futures if future not in completed_futures]

        completed_futures = [(self.future_url_map.pop(id(future)), future) for future in completed_futures]

        return completed_futures

        # return [future.result() for future in completed_futures]
        #
        #
        # future_completed = []
        # for future in concurrent.futures.as_completed(self.futures):
        #     future_completed.append(future)
        #
        # for future in future_completed:
        #     self.futures.remove(future)
        #
        # return [future.result() for future in future_completed]

    def start(self):
        threading.Thread(target=self.download, daemon=True).start()

    def download(self):
        with ThreadPoolExecutor(max_workers=self.n_threads) as executor:
            while self.running:
                if not self.queue:
                    time.sleep(0.1)
                    continue

                with self.lock:
                    while self.queue:
                        url, cookie = self.queue.popleft()

                        future = executor.submit(self.torhandler.send_request, url, cookie)
                        self.futures.append(future)
                        self.future_url_map[id(future)] = url

                        time.sleep(self.waiting_time)

    def stop(self):
        self.running = False