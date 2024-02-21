import unittest
from handler import TorHandler


class TorHandlerTest(unittest.TestCase):
    def test_send_request(self):
        seed = 'http://xv3dbyx4iv35g7z2uoz2yznroy56oe32t7eppw2l2xvuel7km2xemrad.onion/store/nojs/'

        tor_handler = TorHandler()
        web_page = tor_handler.send_request(seed)
        print(web_page.__dict__.keys())
        print(web_page.connection)


if __name__ == '__main__':
    unittest.main()