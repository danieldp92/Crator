import csv
import os
import logging
import time
import threading

logger = logging.getLogger("CRATOR")

SCHEDULE_TIME = 60   # 1 minute


class CrawlerMonitor:
    def __init__(self, project_path=None):
        self.info_pages = []
        self.previous_info_page_length = 0
        self.scheduled_pages = []
        self.previous_scheduled_pages_length = 0
        self.info_unvisited_page = []
        self.previous_info_unvisited_page_length = 0
        self.nodes = []
        self.previous_nodes_length = 0
        self.edges = []
        self.previous_edges_length = 0

        self.tor_requests = 0

        if project_path:
            if not os.path.exists(project_path) or not os.path.isdir(project_path):
                raise FileNotFoundError(f"The project path {project_path} does not exist.")

            self.stop_flag = False

            # Init file and folders
            monitor_path = os.path.join(project_path, "monitor")
            os.makedirs(monitor_path, exist_ok=True)

            self.crawled_file_path = os.path.join(monitor_path, "crawledpages.csv")
            self.__init_header(self.crawled_file_path, ["timestamp", "url", "ip_client", "status_code"])

            self.scheduled_file_path = os.path.join(monitor_path, "scheduled.csv")
            self.__init_header(self.scheduled_file_path, ["timestamp", "url", "depth"])

            self.unvisited_pages_file_path = os.path.join(monitor_path, "unvisitedlinks.csv")
            self.__init_header(self.unvisited_pages_file_path, ["timestamp", "url", "reason"])

            graph_path = os.path.join(project_path, "graph")
            os.makedirs(graph_path, exist_ok=True)

            self.nodes_file_path = os.path.join(graph_path, "nodes.csv")
            self.__init_header(self.nodes_file_path, ["url", "index", "depth_level", "filename"])
            self.edges_file_path = os.path.join(graph_path, "edges.csv")
            self.__init_header(self.edges_file_path, ["node", "node"])

    def __init_header(self, file_path, attribute_list):
        with open(file_path, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(attribute_list)

    def __save_list_to_csv(self, file_path, element_list):
        try:
            with open(file_path, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for element in element_list:
                    writer.writerow(element)
        except Exception as e:
            logger.error(f"MONITOR - Error while saving {file_path}.")
            logger.error(f"Error msg: {str(e)}.")

    def add_info_page(self, timestamp, url, ip, status_code):
        self.info_pages.append((str(timestamp), url, str(ip), str(status_code)))

    def add_scheduled_page(self, timestamp, url, ip, depth):
        self.scheduled_pages.append((str(timestamp), url, str(ip), str(depth)))

    def add_info_unvisited_page(self, timestamp, url, ip, reason):
        self.info_unvisited_page.append((str(timestamp), url, str(ip), reason))

    def add_node(self, url, index, depth, filename):
        self.nodes.append((url, str(index), str(depth), filename))

    def add_edge(self, node1, node2):
        self.edges.append((str(node1), str(node2)))

    def add_edges(self, parent, children):
        for child in children:
            self.add_edge(parent, child)

    def update_tor_requests(self, n_requests):
        self.tor_requests = n_requests

    def get_info(self):
        n_200_pages = 0
        n_300_pages = 0
        n_400_pages = 0
        n_500_pages = 0
        for page in self.info_pages:
            if 200 <= int(page[3]) < 300:
                n_200_pages += 1
            elif 300 <= int(page[3]) < 400:
                n_300_pages += 1
            elif 400 <= int(page[3]) < 500:
                n_400_pages += 1
            else:
                n_500_pages += 1

        return n_200_pages, n_300_pages, n_400_pages, n_500_pages, len(self.info_unvisited_page), len(self.nodes), \
            self.tor_requests

    def save_data_to_csv(self):
        if len(self.info_pages) > self.previous_info_page_length:
            self.__save_list_to_csv(self.crawled_file_path, self.info_pages)
            self.previous_info_page_length = len(self.info_pages)
            logger.debug("MONITOR - Crawled pages file successfully updated.")
        else:
            logger.debug("MONITOR - No changes detected in the crawled pages file. Ignoring.")

        if len(self.scheduled_pages) > self.previous_scheduled_pages_length:
            self.__save_list_to_csv(self.scheduled_file_path, self.scheduled_pages)
            self.previous_scheduled_pages_length = len(self.scheduled_pages)
            logger.debug("MONITOR - Scheduled pages file successfully updated.")
        else:
            logger.debug("MONITOR - No changes detected in the scheduled pages file. Ignoring.")

        if len(self.info_unvisited_page) > self.previous_info_unvisited_page_length:
            self.__save_list_to_csv(self.unvisited_pages_file_path, self.info_unvisited_page)
            self.previous_info_unvisited_page_length = len(self.info_unvisited_page)
            logger.debug("MONITOR - Unvisited pages file successfully updated.")
        else:
            logger.debug("MONITOR - No changes detected in the unvisited links file. Ignoring.")

        if len(self.nodes) > self.previous_nodes_length:
            self.__save_list_to_csv(self.nodes_file_path, self.nodes)
            self.previous_nodes_length = len(self.nodes)
            logger.debug("MONITOR - Nodes file successfully updated.")
        else:
            logger.debug("MONITOR - No changes detected in the nodes file. Ignoring.")

        if len(self.edges) > self.previous_edges_length:
            self.__save_list_to_csv(self.edges_file_path, self.edges)
            self.previous_edges_length = len(self.edges)
            logger.debug("MONITOR - Edges file successfully updated.")
        else:
            logger.debug("MONITOR - No changes detected in the edges file. Ignoring.")

    def schedule_loop(self):
        if not os.path.exists(self.crawled_file_path):
            raise FileNotFoundError("crawledpages.csv deos not exist. Please provide a valid directory path.")

        if not os.path.exists(self.scheduled_file_path):
            raise FileNotFoundError("scheduled.csv deos not exist. Please provide a valid directory path.")

        if not os.path.exists(self.unvisited_pages_file_path):
            raise FileNotFoundError("unvisitedlinks.csv deos not exist. Please provide a valid directory path.")

        if not os.path.exists(self.nodes_file_path):
            raise FileNotFoundError("nodes.csv deos not exist. Please provide a valid directory path.")

        if not os.path.exists(self.edges_file_path):
            raise FileNotFoundError("edges.csv deos not exist. Please provide a valid directory path.")

        while not self.stop_flag:
            self.save_data_to_csv()
            time.sleep(SCHEDULE_TIME)

    def start_scheduling(self):
        threading.Thread(target=self.schedule_loop, daemon=True).start()

    def stop_program(self):
        self.stop_flag = True

        # Final save
        self.save_data_to_csv()