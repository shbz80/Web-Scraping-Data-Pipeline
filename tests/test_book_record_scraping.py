import unittest
from datetime import datetime
from amazon_scraper import AmazonBookScraper

class TestBookScraping(unittest.TestCase):
    """Tests the method scrape_book_data_from_link() that scrapes a single
    book item.
    """
    def setUp(self) -> None:
        # inits the scraper
        section_url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
        scraper = AmazonBookScraper(url=section_url)
        # test book: "The Midnight Library: A Novel"
        book_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/ref=sr_1_1?qid=1644789523&s=books&sr=1-1'
        self.record = scraper.scrape_book_data_from_link(book_url)

    def test_book_record_type(self):
        self.assertIsInstance(self.record, dict)

    def test_book_record_title(self):
        # is the title attribute present
        self.assertIn('title', self.record)
        title = self.record['title']
        # is the title a string
        self.assertIsInstance(title, str)

    def test_book_record_author(self):
        # is the author attribute present
        self.assertIn('author(s)', self.record)
        author = self.record['author(s)']
        # is the author attribute a string
        self.assertIsInstance(author, str)

    def test_book_record_isbn(self):
        # is the isbn attribute present
        self.assertIn('isbn', self.record)
        isbn = self.record['isbn']
        # is the isbn attribute a string
        self.assertIsInstance(isbn, str)
        # does isbn starts with ISBN
        self.assert_(isbn.startswith('ISBN'))

    def test_book_record_date(self):
        # is the date attribute present
        self.assertIn('date', self.record)
        date_publish = self.record['date']
        # is the date attribute a string
        self.assertIsInstance(date_publish, str)
        # is the date valid
        try:
            date_time = datetime.strptime(date_publish, '%B %d %Y')
        except ValueError:
            self.fail('Invalid date data')

    def test_book_record_page(self):
        # is the page attribute present
        self.assertIn('pages', self.record)
        page = self.record['pages']
        # is the page attribute an int
        self.assertIsInstance(page, int)
        # is the page number greater than 0
        self.assertGreater(page, 0)

    def test_book_record_bestseller_rank(self):
        # is the bestseller_rank attribute present
        self.assertIn('best_seller_rank', self.record)
        bestseller_rank = self.record['best_seller_rank']
        # is the bestseller_rank attribute an int
        self.assertIsInstance(bestseller_rank, int)
        # is the bestseller_rank number greater than 0
        self.assertGreater(bestseller_rank, 0)

    def test_book_record_review_rating(self):
        # is the review_rating attribute present
        self.assertIn('review_rating', self.record)
        review_rating = self.record['review_rating']
        # is the review_rating attribute a float
        self.assertIsInstance(review_rating, float)
        # is the review_rating number greater than 1.0
        self.assertGreaterEqual(review_rating, 1.0)
        # is the review_rating number lesser than 5.0
        self.assertLessEqual(review_rating, 5.0)

    def test_book_record_review_count(self):
        # is the review_count attribute present
        self.assertIn('review_count', self.record)
        review_count = self.record['review_count']
        # is the review_count attribute an int
        self.assertIsInstance(review_count, int)
        # is the review_count number greater than 0
        self.assertGreaterEqual(review_count, 0)
        
    def test_book_record_image_link(self):
        # is the image_link attribute present
        self.assertIn('image_link', self.record)
        image_link = self.record['image_link']
        # is the image_link attribute a str
        self.assertIsInstance(image_link, str)
        # does it starts with https
        self.assert_(image_link.startswith('https'))

    def test_book_record_description(self):
        # is the description attribute present
        self.assertIn('description', self.record)
        description = self.record['description']
        # is the description attribute a str
        self.assertIsInstance(description, str)

    def test_book_record_uuid(self):
        # is the uuid attribute present
        self.assertIn('uuid', self.record)
        uuid = self.record['uuid']
        # is the uuid attribute a str
        self.assertIsInstance(uuid, str)
        # is the uuid 36 chars
        self.assertEqual(len(uuid), 36)

    def tearDown(self) -> None:
        del self.record

if __name__ == '__main__':
    unittest.main()




