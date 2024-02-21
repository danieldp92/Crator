import threading
import time
import os
import hashlib
from collections import deque
from concurrent.futures import ThreadPoolExecutor

# Local imports
import utils.fileutils as file_utils


class FileSaver:
    def __init__(self, save_path, n_threads=1):
        self.n_threads = n_threads
        self.save_path = save_path

        self.queue = deque()
        self.lock = threading.Lock()
        self.running = True

    def enqueue(self, web_page, index_node):
        self.queue.append((web_page, index_node))

    def stop(self):
        self.running = False

    def start(self):
        threading.Thread(target=self.save, daemon=True).start()

    def save(self):
        with ThreadPoolExecutor(max_workers=self.n_threads) as executor:
            while self.running:
                if not self.queue:
                    time.sleep(0.1)
                    continue

                with self.lock:
                    while self.queue:
                        web_page, index_node = self.queue.popleft()
                        file_name = str(index_node) + ".html"
                        dir = os.path.join(self.save_path, file_name)

                        executor.submit(file_utils.save_file, web_page.text, dir)
                        time.sleep(0.1)
