import os
import shutil
from glob import glob
import unittest
from amazon_scraper import AmazonBookScraper


class TestBookRecords(unittest.TestCase):
    """Tests the method scrape_books() that acquires book records."""
    def setUp(self) -> None:
        # inits the scraper
        section_url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
        self.scraper = AmazonBookScraper(url=section_url)

    def test_book_records_type(self):
        # scrape some books
        records, reviews = self.scraper.scrape_books(5, save_data=False)
        # is the scraped record and reviews a list
        self.assertIsInstance(records, list)
        self.assertIsInstance(reviews, list)
        # are the they dicts
        for record in records:
            self.assertIsInstance(record, dict)
        for review in reviews:
            self.assertIsInstance(review, dict)
        
    
    def test_book_records_len(self):
        # scrape some books
        records, reviews = self.scraper.scrape_books(5, review_num=5,save_data=False)
        # is the number of records consistent with number of books specified 
        self.assertEqual(len(records), 5)
        self.assertEqual(len(reviews), 25)

    def test_file_saving(self):
        # if raw_data folder exists in tests folder delete and create again
        test_dir = os.getcwd() + '/tests/'
        if os.path.exists(test_dir + 'raw_data/'):
            shutil.rmtree(test_dir + 'raw_data/')
        os.makedirs(test_dir + 'raw_data/')

        # scrape some books
        records, invalids = self.scraper.scrape_books(
            5, review_num=5, save_loc=test_dir, save_data=True)
        
        # did the data save properly
        saved_dirs = glob(test_dir + 'raw_data/' + '*')
        self.assertEqual(len(saved_dirs), 5)
        for d in saved_dirs:
            self.assertEqual(len(glob(d +'/*.json')), 1)
            self.assertEqual(len(glob(d +'/*.img')), 1)
            self.assertEqual(len(glob(d +'/reviews/')), 1)
            self.assertEqual(len(glob(d +'/reviews/*')), 5)

    def tearDown(self) -> None:
        del self.scraper

if __name__ == '__main__':
    unittest.main()
