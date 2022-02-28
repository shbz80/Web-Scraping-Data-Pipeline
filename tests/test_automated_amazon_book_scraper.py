import unittest
from amazon_automated_book_review_scraper import AmazonAutomatedBookReviewScraper
from entities import Review

class TestAmazonAutomatedBookReviewScraper(unittest.TestCase):
    def setUp(self) -> None:
        self.aabrs = AmazonAutomatedBookReviewScraper()
        self.book_url = "https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/"

    def test_scrape_book_reviews_lt_10(self):
        reviews = self.aabrs.scrape_book_reviews(num=5, url=self.book_url)
        self.assertEqual(reviews[0].user, 'Patrick F')
        self.assertEquals(len(reviews), 5)
        for review in reviews:
            self.assertIsInstance(review, Review)
            self.assertIsInstance(review.user, str)
            self.assertIsInstance(review.text, str)
            self.assertIsInstance(review.rating, int)
            self.assertGreaterEqual(review.rating, 0)
            self.assertLessEqual(review.rating, 5)

    def test_scrape_book_reviews_eq_10(self):
        reviews = self.aabrs.scrape_book_reviews(url=self.book_url)
        self.assertEqual(reviews[0].user, 'Patrick F')
        self.assertEquals(len(reviews), 10)
        for review in reviews:
            self.assertIsInstance(review, Review)
            self.assertIsInstance(review.user, str)
            self.assertIsInstance(review.text, str)
            self.assertIsInstance(review.rating, int)
            self.assertGreaterEqual(review.rating, 0)
            self.assertLessEqual(review.rating, 5)

    def test_scrape_book_reviews_gt_10(self):
        reviews = self.aabrs.scrape_book_reviews(num=50, url=self.book_url)
        self.assertEqual(reviews[0].user, 'Patrick F')
        self.assertEquals(len(reviews), 50)
        for review in reviews:
            self.assertIsInstance(review, Review)
            self.assertIsInstance(review.user, str)
            self.assertIsInstance(review.text, str)
            self.assertIsInstance(review.rating, int)
            self.assertGreaterEqual(review.rating, 0)
            self.assertLessEqual(review.rating, 5)

    def test_scrape_book_reviews_with_skip(self):
        reviews = self.aabrs.scrape_book_reviews(num=19, 
            url=self.book_url, skip_users=['Patrick F'])
        self.assertEquals(len(reviews), 19)
        for review in reviews:
            if review.user == 'Patrick F':
                self.fail
