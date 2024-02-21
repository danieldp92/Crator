import logging
from datetime import datetime
import time
import os
import concurrent.futures

# Local import
import crawler
from utils.config import Configuration
from utils.seeds import get_seeds
from handler import TorHandler


def init_logger():
    log_directory = "../log"
    if not os.path.exists(log_directory) or not os.path.isdir(log_directory):
        os.mkdir(log_directory)

    today_tms = datetime.now().strftime("%Y%m%dT%H%M%S")
    logfile_path = os.path.join(log_directory, f"crator_{today_tms}.log")

    # Create a logger object
    logger = logging.getLogger("CRATOR")
    logger.setLevel(logging.DEBUG)

    # Create a file handler to write logs to a file
    file_handler = logging.FileHandler(logfile_path)
    file_handler.setLevel(logging.DEBUG)

    # Create a formatter to format the logs
    formatter = logging.Formatter("%(asctime)s:%(levelname)s:%(message)s")
    file_handler.setFormatter(formatter)

    # Add the file handler to the logger
    logger.addHandler(file_handler)


def print_info(pcrawler: crawler.Crawler):
    n_200_pages, n_300_pages, n_400_pages, n_500_pages, n_skip_page, links_found, n_requests = pcrawler.get_info()
    print(f"Seed: {crator.seed}")
    print(f"HTTP 2xx status code: {n_200_pages}")
    print(f"HTTP 3xx status code: {n_300_pages}")
    print(f"HTTP 4xx status code: {n_400_pages}")
    print(f"HTTP 5xx status code: {n_500_pages}")
    print(f"Link skipped: {n_skip_page}")
    print(f"Request sent: {n_requests}")
    print(f"Links found: {links_found}")

    n_pages = n_200_pages + n_300_pages + n_400_pages + n_500_pages
    if links_found > 0 and n_pages > 0:
        print(f"Actual percentage of coverage: {round((n_pages / links_found) * 100, 2)}%")
    else:
        print(f"Actual percentage of coverage: 0%")
    print("----------------------------")


if __name__ == '__main__':
    init_logger()
    logger = logging.getLogger("CRATOR")
    logger.info("CRATOR - START")

    config = Configuration()

    seeds = get_seeds()
    logger.info(f"Urls to analyze: {', '.join(seeds)}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(seeds)) as executor:
        torhandler = TorHandler()
        crators = []
        futures = []

        for seed in seeds:
            print(f"Thread for the seed -> {seed}")
            crator = crawler.Crawler(seed, torhandler)
            crators.append(crator)

            future = executor.submit(crator.start)
            futures.append(future)

        # while not all(future.done() for future in futures):
            # print("\nCrawling info\n")
            # for crator in crators:
            #     if crator.require_cookies() and crator.waiting_new_cookies():
            #         print("###### COOOKIE UPDATE REQUIRED!!! #####")
            #         print(f"{crator.seed} - Cookie list is empty. Insert new cookies.")
            #         user_input = input("Press any keys when you updates the cookies.")
            #         crator.unlock()
            #         print("----------------------------")
            #
            #     print_info(crator)
            #
            # time.sleep(60)

        # Wait for all tasks to complete
        concurrent.futures.wait(futures)

        print("Seeds downloaded. Final info\n")

        for crator in crators:
            print_info(crator)

        print("CRATOR - END")




