import unittest
from utils.config import Configuration


# Function to test
def add_numbers(x, y):
    return x + y


# Test class
class TestConfiguration(unittest.TestCase):

    def test_has_cookies_with_no_seeds(self):
        config = Configuration()
        self.assertTrue(config.has_cookies())

    def test_has_cookies(self):
        config = Configuration()
        seed = "http://royalrnpvfbodtt5altnnzano6hquvn2d5qy55oofc2zyqciogcevrad.onion/"
        self.assertTrue(config.has_cookies(seed))

    def test_has_no_cookies(self):
        config = Configuration()
        seed = "http://xv3dbyx4iv35g7z2uoz2yznroy56oe32t7eppw2l2xvuel7km2xemrad.onion/store/nojs/"
        self.assertFalse(config.has_cookies(seed))

    # def test_get_cookies_1(self):
    #     config = Configuration()
    #     seed = "http://royalrnpvfbodtt5altnnzano6hquvn2d5qy55oofc2zyqciogcevrad.onion/"
    #
    #     response_expected = ['royal_market_session=eyJpdiI6InhKZXM2ZG02ZTBnMyt3b0I5M0Zvamc9PSIsInZhbHVlIjoiNXZJTHJSQWJy'
    #                          'UUFQZ1k0TXQ1aUdQd2xjLzBzVmt2VForRGtRN0xzM21aMHd2amppdnlPUFd3R3BMeWVuYTBzcTc3VXFTQ2tmeDJVK'
    #                          '00yQkd4aU10OG5NM0RXQkdmenFId1d3TUpRb3d6TndNZEgwZ0UzNCtURnFRVVR0ZmJOMHgiLCJtYWMiOiI0ZWVmOD'
    #                          'hhNTZlNzAzZTE2MmM0ZDY0MTc0M2U3Y2MxMzAwZjczZTA2MzA5NDQ0NDM1MTA0ZGE0MGVhODk2MzEzIn0%3D; XSR'
    #                          'F-TOKEN=eyJpdiI6IldHNmxBQUNlYkFyM3ltOVc0Ym1SZlE9PSIsInZhbHVlIjoiSzBPM1QwZmVDYnlFWWdRTy9yc'
    #                          'lNwTWY2cHJsczZnMHVGWm9RNjN3MUNUWkVFYitYcmx4UGhEU05JNnRYUXBGR3hiTlRKeU92ZGVIazZ3cXdPTUpsK3'
    #                          'NRUm9YT3oxN0ZhdnY4V1pXRUwxcEpMdVNEaUJRV2xLWW1wZXZ1ZW9meHoiLCJtYWMiOiJkOTVlODQ3OGExMDYwN2Q'
    #                          '4MGY5MjgyOTgxMmEyYzI3N2NlODIxYmZiMzc2YTE4NzgyZTM5Yjg0ZTA0YjgyZWMyIn0%3D']
    #
    #     self.assertIsInstance(config.cookies(seed), list)
    #     self.assertEqual(config.cookies(seed), response_expected)

    def test_get_cookies_2(self):
        config = Configuration()
        seed = "http://xv3dbyx4iv35g7z2uoz2yznroy56oe32t7eppw2l2xvuel7km2xemrad.onion/store/nojs/"

        response_expected = None

        self.assertEqual(config.cookies(seed), response_expected)

    def test_add_cookie(self):
        seed = 'http://royalrnpvfbodtt5altnnzano6hquvn2d5qy55oofc2zyqciogcevrad.onion/'
        cookie_to_add = 'royal_market_session=eyJpdiI6InhKZXM2ZG02ZTBnMyt3b0I5M0Zvamc9PSIsInZhbHVlIjoiNXZJTHJSQWJyUUFQZ' \
                        '1k0TXQ1aUdQd2xjLzBzVmt2VForRGtRN0xzM21aMHd2amppdnlPUFd3R3BMeWVuYTBzcTc3VXFTQ2tmeDJVK00yQkd4aU1' \
                        '0OG5NM0RXQkdmenFId1d3TUpRb3d6TndNZEgwZ0UzNCtURnFRVVR0ZmJOMHgiLCJtYWMiOiI0ZWVmODhhNTZlNzAzZTE2M' \
                        'mM0ZDY0MTc0M2U3Y2MxMzAwZjczZTA2MzA5NDQ0NDM1MTA0ZGE0MGVhODk2MzEzIn0%3D; XSRF-TOKEN=eyJpdiI6IldH' \
                        'NmxBQUNlYkFyM3ltOVc0Ym1SZlE9PSIsInZhbHVlIjoiSzBPM1QwZmVDYnlFWWdRTy9yclNwTWY2cHJsczZnMHVGWm9RNj' \
                        'N3MUNUWkVFYitYcmx4UGhEU05JNnRYUXBGR3hiTlRKeU92ZGVIazZ3cXdPTUpsK3NRUm9YT3oxN0ZhdnY4V1pXRUwxcEpM' \
                        'dVNEaUJRV2xLWW1wZXZ1ZW9meHoiLCJtYWMiOiJkOTVlODQ3OGExMDYwN2Q4MGY5MjgyOTgxMmEyYzI3N2NlODIxYmZiMz' \
                        'c2YTE4NzgyZTM5Yjg0ZTA0YjgyZWMyIn0%3D'

        config = Configuration()
        config.add_cookie(seed, cookie_to_add)


    def test_remove_cookie(self):
        seed = 'http://royalrnpvfbodtt5altnnzano6hquvn2d5qy55oofc2zyqciogcevrad.onion/'
        cookie_to_remove = 'royal_market_session=eyJpdiI6InhKZXM2ZG02ZTBnMyt3b0I5M0Zvamc9PSIsInZhbHVlIjoiNXZJTHJSQWJyUU' \
                           'FQZ1k0TXQ1aUdQd2xjLzBzVmt2VForRGtRN0xzM21aMHd2amppdnlPUFd3R3BMeWVuYTBzcTc3VXFTQ2tmeDJVK00yQ' \
                           'kd4aU10OG5NM0RXQkdmenFId1d3TUpRb3d6TndNZEgwZ0UzNCtURnFRVVR0ZmJOMHgiLCJtYWMiOiI0ZWVmODhhNTZl' \
                           'NzAzZTE2MmM0ZDY0MTc0M2U3Y2MxMzAwZjczZTA2MzA5NDQ0NDM1MTA0ZGE0MGVhODk2MzEzIn0%3D; XSRF-TOKEN=' \
                           'eyJpdiI6IldHNmxBQUNlYkFyM3ltOVc0Ym1SZlE9PSIsInZhbHVlIjoiSzBPM1QwZmVDYnlFWWdRTy9yclNwTWY2cHJ' \
                           'sczZnMHVGWm9RNjN3MUNUWkVFYitYcmx4UGhEU05JNnRYUXBGR3hiTlRKeU92ZGVIazZ3cXdPTUpsK3NRUm9YT3oxN0' \
                           'ZhdnY4V1pXRUwxcEpMdVNEaUJRV2xLWW1wZXZ1ZW9meHoiLCJtYWMiOiJkOTVlODQ3OGExMDYwN2Q4MGY5MjgyOTgxM' \
                           'mEyYzI3N2NlODIxYmZiMzc2YTE4NzgyZTM5Yjg0ZTA0YjgyZWMyIn0%3D'

        config = Configuration()
        config.remove_cookie(seed, cookie_to_remove)

if __name__ == '__main__':
    unittest.main()