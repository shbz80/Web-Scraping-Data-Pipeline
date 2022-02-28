import unittest
from amazon_book_review_scraper import AmazonBookReviewScraper
from entities import Review


class TestAmazonBookReviewScraper(unittest.TestCase):
    def setUp(self) -> None:
        self.abrs = AmazonBookReviewScraper()
        self.book_url = "https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/product-reviews/0525559477/ref=cm_cr_dp_d_show_all_btm?ie=UTF8&reviewerType=all_reviews"

    def test_scrape_reviews_from_curr_page(self):
        reviews = self.abrs.scrape_reviews_from_curr_page(url=self.book_url)
        self.assertEqual(reviews[0].user, 'Patrick F')
        print(reviews[0])
        self.assertEquals(len(reviews), 10)
        for review in reviews:
            self.assertIsInstance(review,Review)
            self.assertIsInstance(review.user, str)
            self.assertIsInstance(review.text, str)
            self.assertIsInstance(review.rating, int)
            self.assertGreaterEqual(review.rating, 0)
            self.assertLessEqual(review.rating, 5)

    def test_scrape_reviews_from_curr_page_with_skip(self):
        reviews = self.abrs.scrape_reviews_from_curr_page(
            url=self.book_url, skip_users=['Patrick F'])
        self.assertEquals(len(reviews), 9)
        for review in reviews:
            if review.user == 'Patrick F':
                self.fail

    

