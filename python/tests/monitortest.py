import unittest
import os
import csv
from monitor import CrawlerMonitor


test_data_path = "test_data"


class MonitorTest(unittest.TestCase):
    # def test_update_crawled_pages(self):
    #     crawled_pages_path = os.path.join(data_path, "default/monitor/crawlerPages.csv")
    #     url_queue_path = os.path.join(data_path, "default/monitor/urlQueue.csv")
    #
    #     timestamp = 12243432432
    #     url = "http://sdsuhfgdsuihfiudshf.onion"
    #     ip_client = "192.453.67.43"
    #     status_code = 200
    #
    #     monitor = CrawlerMonitor(crawled_file=crawled_pages_path, queue_file=url_queue_path)
    #     monitor.update_crawled_pages(timestamp=timestamp, url=url, ip_client=ip_client, status_code=status_code)

    def test_get_info(self):
        info_pages_path = os.path.join(test_data_path, "crawledpages.csv")
        unvisited_links_path = os.path.join(test_data_path, "unvisitedlinks.csv")
        nodes_path = os.path.join(test_data_path, "nodes.csv")

        expected_results = {
            "https_200": 3914,
            "https_300": 0,
            "https_400": 8,
            "https_500": 0,
            "unvisited_links": 26,
            "tot_links": 5072
        }

        info_pages = []
        with open(info_pages_path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                info_pages.append(tuple(row))

        unvisited_pages = []
        with open(unvisited_links_path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                unvisited_pages.append(tuple(row))

        nodes = []
        with open(nodes_path, 'r') as file:
            reader = csv.reader(file)
            for row in reader:
                nodes.append(tuple(row))

        monitor = CrawlerMonitor()
        monitor.info_pages = info_pages
        monitor.info_unvisited_page = unvisited_pages
        monitor.nodes = nodes

        n_200_pages, n_300_pages, n_400_pages, n_500_pages, n_skip_page, links_found, n_requests = monitor.get_info()

        results = {
            "https_200": n_200_pages,
            "https_300": n_300_pages,
            "https_400": n_400_pages,
            "https_500": n_500_pages,
            "unvisited_links": n_skip_page,
            "tot_links": links_found
        }

        self.assertEqual(results, expected_results)


if __name__ == '__main__':
    unittest.main()