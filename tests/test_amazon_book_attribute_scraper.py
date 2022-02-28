import unittest
from amazon_book_attribute_scraper import AmazonBookAttributeScraper
from entities import BookAttribute


class TestAmazonBookAttributeScraper(unittest.TestCase):
    def setUp(self) -> None:
        self.abas = AmazonBookAttributeScraper()
        self.book_url = "https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/"

    def test_scrape_book_attributes_from_page(self):
        book_attributes = self.abas.scrape_book_attributes_from_page(self.book_url)
        self.assertIsInstance(book_attributes, BookAttribute)
        self.assertIsInstance(book_attributes.title, str)
        self.assertIsInstance(book_attributes.isbn, str)
        self.assertIsInstance(book_attributes.uuid, str)
        self.assertIsInstance(book_attributes.author, str)
        self.assertIsInstance(book_attributes.description, str)
        self.assertIsInstance(book_attributes.date, str)
        self.assertIsInstance(book_attributes.pages, int)
        self.assertGreater(book_attributes.pages, 0)
        self.assertIsInstance(book_attributes.price, float)
        self.assertGreater(book_attributes.price, 0)
        self.assertIsInstance(book_attributes.best_seller_rank, int)
        self.assertGreater(book_attributes.best_seller_rank, 0)
        self.assertIsInstance(book_attributes.review_count, int)
        self.assertGreater(book_attributes.review_count, 0)
        self.assertIsInstance(book_attributes.image_url, str)
        self.assertIsInstance(book_attributes.book_url, str)
