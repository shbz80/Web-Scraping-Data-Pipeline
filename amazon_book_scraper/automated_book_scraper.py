"""Provides the class for an automated book scraper """
from abc import ABC, abstractmethod
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from entities import Book
from book_attribute_scraper import BookAttributeScraper
from book_review_scraper import AutomatedBookReviewScraper
from raw_data_storage import RawDataStorage
from rds_data_storage import RDSDataStorage
from utils import PAGE_SLEEP_TIME

class AutomatedBookScraper(ABC):
    """Automates the book scraping process. Ensures that the total number
    of required books will be scraped after considering what is already saved.
    So this can be rerun multiple times with the same command until the 
    required number of books are scraped. The main method is scrape_books().
    """
    def __init__(
            self, url: str, 
            book_attribute_scraper: BookAttributeScraper,
            automated_book_review_scraper: AutomatedBookReviewScraper,
            raw_data_storage: RawDataStorage,
            rds_data_storage: RDSDataStorage = None,
            browser: str = 'chrome',
            mode: str = 'normal') -> None:
        """
        Args:
            url (str): starting url for the book sraper
            book_attribute_scraper (BookAttributeScraper): scraper for a book
            automated_book_review_scraper (AutomatedBookReviewScraper): 
                    scraper for a book reviews
            raw_data_storage (RawDataStorage): object for saving raw data
            rds_data_storage (RDSDataStorage, optional): RDS interface object
            browser (str, optional): select the browser.
            mode (str, optional): normal or headless mode
        """
        if not isinstance(book_attribute_scraper, BookAttributeScraper):
            raise TypeError('Invalid type')
        if not isinstance(automated_book_review_scraper, AutomatedBookReviewScraper):
            raise TypeError('Invalid type')
        if not isinstance(raw_data_storage, RawDataStorage):
            raise TypeError('Invalid type')
        if rds_data_storage and not isinstance(rds_data_storage, RDSDataStorage):
            raise TypeError('Invalid type')

        self._book_attribute_scraper = book_attribute_scraper
        self._automated_book_review_scraper = automated_book_review_scraper
        self._raw_data_storage = raw_data_storage
        self._rds_data_storage = rds_data_storage

        # init Selenium 
        try:
            if browser == 'chrome':
                chrome_options = ChromeOptions()
                if mode == 'headless':
                    chrome_options.add_argument("--headless")
                chrome_options.add_argument('--no-sandbox')
                chrome_options.add_argument('--disable-dev-shm-usage')
                self._driver = webdriver.Chrome(options=chrome_options)
                # self._driver.implicitly_wait(10)
            elif browser == 'firefox':
                firfox_options = FirefoxOptions()
                if mode == 'headless':
                    firfox_options.add_argument("--headless")
                firfox_options.add_argument('--no-sandbox')
                firfox_options.add_argument('--disable-dev-shm-usage')
                self._driver = webdriver.Firefox(options=firfox_options)
                # self._driver.implicitly_wait(10)
            else:
                raise NotImplementedError(
                    'Only Chrome and Firefox are supported.')
        except Exception as e:
            print('Selenium driver error: ', e)

        # get to the url
        try:
            self._driver.get(url)
        except:
            print('Invalid url')
        time.sleep(PAGE_SLEEP_TIME)

    def scrape_books(self, num_books: int, num_reviews: int = 10) -> list[Book]:
        """The main method for scraping books. It can be rerun with the same
        num_books multiple times. Each time it scrapes the remaining books.
        This applies to number of reviews to already scraped books also.

        Args:
            num_books (int): number of books to scrape
            num_reviews (int, optional): number of reviews to scrape

        Returns:
            list[Book]: _description_
        """
        scraped_books = []
        # get all the scraped book urls that satisfies the current
        # requirements on num_review
        saved_ulrs = self._get_saved_urls(num_reviews=num_reviews)

        # get the number of books to scrape
        if num_books > len(saved_ulrs):
            num_books_to_scrape = num_books - len(saved_ulrs)
            # scrape 5% extra to compesate for errors
            num_books_to_scrape = num_books_to_scrape + \
                    int(num_books_to_scrape * 0.05)
        else:
            num_books_to_scrape = 0

        # get all saved book isbn numbers even if it does not match the
        # current num_review requirement
        saved_isbns = self._get_saved_isbns()

        # get all the urls that needs to be scraped that includes the one that
        # have already been scraped but do not satisfy the current num_review
        # requirement.
        urls_to_scrape = self._get_urls_to_scrape(
                num_books_to_scrape, saved_ulrs)

        # scrape all new book/reviews
        for i, book_url in enumerate(urls_to_scrape):
            # get the book attribute for the url
            # driver need not point to the page
            # side-effect: webdriver points to the book page
            book_attribute = \
                self._book_attribute_scraper.scrape_book_attributes_from_page(
                        url=book_url, driver=self._driver)
            # skip this book if it is invalid
            if book_attribute is None:
                continue
            # get any saved reviews for this book
            saved_reviews = self._get_saved_reviews(book_attribute.isbn)
            # get the book review for this book
            # driver needs to point to the page
            book_reviews = self._automated_book_review_scraper.scrape_book_reviews(
                    book_attribute.isbn, num=num_reviews, driver=self._driver,
                    skip_users=saved_reviews)
            # prepare the book object
            scraped_book = Book(attributes=book_attribute, reviews=book_reviews)
            # save the book in the chosen raw data storage (local or S3 bucket)
            self._raw_data_storage.save_book(scraped_book, saved_isbns)
            # save the book in the RDS system if required
            if self._rds_data_storage:
                self._rds_data_storage.save_book(scraped_book, saved_isbns)
            # save the image in the raw data storage
            image_url = scraped_book.attributes.image_url
            book_isbn = scraped_book.attributes.isbn
            self._raw_data_storage.save_book_image(image_url, book_isbn)
            scraped_books.append(scraped_book)
            print(f"{len(urls_to_scrape)- i - 1} remaining books")

        return scraped_books

    def _get_urls_to_scrape(self, num_books, saved_ulrs):
        # get book urls form the first page
        url_list = self._get_book_urls_from_page()
        url_list = self._remove_saved_urls(url_list, saved_ulrs)
        # navigate pages sequentially and get book urls
        while len(url_list) < num_books and self._go_to_next_page_if_exists():
            urls_curr_page = self._get_book_urls_from_page()
            urls_curr_page = self._remove_saved_urls(
                urls_curr_page, saved_ulrs)
            url_list.extend(urls_curr_page)
            
        # return only a maximum of num_books urls
        if len(url_list) > num_books:
            return url_list[:num_books]
        else:
            return url_list

    @staticmethod
    def _remove_saved_urls(urls, saved_ulrs):
        return [item for item in urls if item not in saved_ulrs]

    def _get_saved_urls(self, num_reviews):
        """Retireve the list of scraped urls from storage that does not 
        already satisfy the num_reviews requirement"""
        if self._rds_data_storage:
            saved_urls = self._rds_data_storage.get_saved_book_urls(num_reviews)
        else:
            saved_urls = self._raw_data_storage.get_saved_book_urls(num_reviews)
        return saved_urls

    def _get_saved_reviews(self, isbn):
        """Retrieves the list of saved reviews for the given book (isbn)"""
        if self._rds_data_storage:
            users = self._rds_data_storage.get_saved_review_users(isbn)
        else:
            users = self._raw_data_storage.get_saved_review_users(isbn)
        return users

    def _get_saved_isbns(self):
        """Retrieves the list of saved book isbn number"""
        if self._rds_data_storage:
            isbns = self._rds_data_storage.get_saved_book_isbns()
        else:
            isbns = self._raw_data_storage.get_saved_book_isbns()
        return isbns

    @abstractmethod
    def _get_book_urls_from_page(self):
        pass

    @abstractmethod
    def _go_to_next_page_if_exists(self):
        pass



