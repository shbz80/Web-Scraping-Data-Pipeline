import unittest
from amazon_automated_book_scraper import AmazonAutomatedBookScraper
from amazon_book_attribute_scraper import AmazonBookAttributeScraper
from amazon_automated_book_review_scraper import AmazonAutomatedBookReviewScraper
from entities import Book

class TestAmazonAutomatedBookScraper(unittest.TestCase):
    def setUp(self) -> None:
        url = "https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1645782603&ref=sr_pg_1"
        abas = AmazonBookAttributeScraper()
        aabrs = AmazonAutomatedBookReviewScraper()
        self.aabs = AmazonAutomatedBookScraper(
                url=url,
                book_attribute_scraper=abas,
                automated_book_review_scraper=aabrs,
                browser='firefox')

    def test_get_urls_to_scrape_eq_10(self):
        urls = self.aabs._get_urls_to_scrape(num_books=10, saved_ulrs=[])
        self.assertIsInstance(urls, list)
        self.assertEqual(len(urls), 10)
        
    def test_get_urls_to_scrape_lt_10(self):
        urls = self.aabs._get_urls_to_scrape(num_books=5, saved_ulrs=[])
        self.assertIsInstance(urls, list)
        self.assertEqual(len(urls), 5)

    def test_get_urls_to_scrape_gt_10(self):
        urls = self.aabs._get_urls_to_scrape(num_books=25, saved_ulrs=[])
        self.assertIsInstance(urls, list)
        self.assertEqual(len(urls), 25)
        test_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/'
        self.assertTrue(test_url == urls[0])
        for url in urls:
            self.assertIsInstance(url, str)
            self.assertTrue(url.startswith("https://"))
            
    def test_get_urls_to_scrape_saved_list(self):
        saved_list = [
            'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/']
        urls = self.aabs._get_urls_to_scrape(num_books=25, saved_ulrs=saved_list)
        self.assertIsInstance(urls, list)
        self.assertEqual(len(urls), 25)
        for url in urls:
            self.assertIsInstance(url, str)
            self.assertTrue("http" in url)
            self.assertNotEqual(url, saved_list[0])

    def test_scrape_books_1(self):
        test_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/'
        test_user = 'Patrick F'
        books = self.aabs.scrape_books(num_books=3, num_reviews=3)
        self.assertIsInstance(books, list)
        self.assertEqual(len(books), 3)
        self.assertEqual(books[0].attributes.book_url, test_url)
        self.assertEqual(books[0].reviews[0].user, test_user)
        for book in books:
            self.assertIsInstance(book, Book)
            print(book.attributes.title)
            self.assertEqual(len(book.reviews), 3)

    def test_scrape_books_2(self):
        books = self.aabs.scrape_books(num_books=12, num_reviews=18)
        self.assertIsInstance(books, list)
        self.assertEqual(len(books), 12)
        for book in books:
            self.assertIsInstance(book, Book)
            self.assertEqual(len(book.reviews), 18)

    def test_scrape_books_3(self):
        test_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/'
        books = self.aabs.scrape_books(num_books=3, num_reviews=3)
        self.assertIsInstance(books, list)
        self.assertEqual(len(books), 2)
        self.assertNotEqual(books[0].attributes.book_url, test_url)
        for book in books:
            self.assertIsInstance(book, Book)
            print(book.attributes.title)
            self.assertEqual(len(book.reviews), 3)
