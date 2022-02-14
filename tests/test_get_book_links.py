import unittest
from amazon_scraper import AmazonBookScraper


class TestGetBookLinks(unittest.TestCase):
    """Tests the method get_book_links() that acquires book url to scrape.
    """
    def setUp(self) -> None:
        # inits the scraper
        section_url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
        self.scraper = AmazonBookScraper(url=section_url)

    def test_link_list_type(self):
        # get some links
        link_list = self.scraper.get_book_links(2)
        # is the link container a list
        self.assertIsInstance(link_list, list)
    
    def test_link_list_len(self):
        # get some links
        link_list = self.scraper.get_book_links(10)
        # is the link list of the correct size
        self.assertEqual(len(link_list), 10)

    def test_link_validity(self):
        # get some links
        link_list = self.scraper.get_book_links(10)
        # are all links valid url (starts with https)
        for link in link_list:
            self.assertTrue(link.startswith('https'))

    def tearDown(self) -> None:
        del self.scraper


if __name__ == '__main__':
    unittest.main()
