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
        records, invalids = self.scraper.scrape_books(5, save_data=False)
        # is the scraped recrod set a list
        self.assertIsInstance(records, list)
        # are the records dicts
        for record in records:
            self.assertIsInstance(record, dict)
    
    def test_book_records_len(self):
        # scrape some books
        records, invalids = self.scraper.scrape_books(5, save_data=False)
        # is the number of records consistent with number of books specified 
        # and invalid books
        self.assertEqual(len(records) + invalids, 5)

    def test_file_saving(self):
        # if raw_data folder exists in tests folder delete and create again
        test_dir = os.getcwd() + '/tests/'
        if os.path.exists(test_dir + 'raw_data/'):
            shutil.rmtree(test_dir + 'raw_data/')
        os.makedirs(test_dir + 'raw_data/')

        # scrape some books
        records, invalids = self.scraper.scrape_books(
            5, save_loc=test_dir, save_data=True)
        
        # did the data save properly
        saved_dirs = glob(test_dir + 'raw_data/' + '*')
        self.assertEqual(len(saved_dirs) + invalids, 5)
        for d in saved_dirs:
            self.assertEqual(len(glob(d +'/*.json')), 1)
            self.assertEqual(len(glob(d +'/*.jpg')), 1)

    def tearDown(self) -> None:
        del self.scraper

if __name__ == '__main__':
    unittest.main()
