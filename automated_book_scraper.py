"""Provides the class for an automated book scraper """
from abc import ABC, abstractmethod
import time
from selenium import webdriver
from entities import Book
from book_attribute_scraper import BookAttributeScraper
from book_review_scraper import AutomatedBookReviewScraper
from raw_data_storage import RawDataStorage
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
            browser: str = 'chrome',
            banned_titles: list[str] = None) -> None:
        """_summary_

        Args:
            url (str): starting url for the book sraper
            book_attribute_scraper (BookAttributeScraper): scraper for a book
            automated_book_review_scraper (AutomatedBookReviewScraper): 
                    scraper for a book reviews
            raw_data_storage (RawDataStorage): object for saving raw data
            browser (str, optional): select the browser.
            banned_titles (list[str], optional): specify any banned phrases in
                    the title.
        """
        self._book_attribute_scraper = book_attribute_scraper
        self._automated_book_review_scraper = automated_book_review_scraper
        self._raw_data_storage = raw_data_storage

        if banned_titles is None:
            self._banned_titles = []

        # init Selenium 
        try:
            if browser == 'chrome':
                self._driver = webdriver.Chrome()
            elif browser == 'firefox':
                self._driver = webdriver.Firefox()
            else:
                raise NotImplementedError(
                    'Only Chrome and Firefox are supported.')
        except:
            print('Selenium driver error')

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
        saved_ulrs = self._get_saved_urls(num_reviews=num_reviews)

        if num_books > len(saved_ulrs):
            num_books_to_scrape = num_books - len(saved_ulrs)
            # scrape 1% extra to compesate for errors
            num_books_to_scrape = num_books_to_scrape + \
                    int(num_books_to_scrape * 0.01)
        else:
            num_books_to_scrape = 0

        urls_to_scrape = self._get_urls_to_scrape(
                num_books_to_scrape, saved_ulrs)

        for i, book_url in enumerate(urls_to_scrape):
            # driver need not point to the page
            # side-effect: webdriver points to the book page
            book_attribute = \
                self._book_attribute_scraper.scrape_book_attributes_from_page(
                        url=book_url, driver=self._driver)
            if book_attribute is None:
                continue
            saved_reviews = self._get_saved_reviews(book_attribute.isbn)
            # driver needs to point to the page
            book_reviews = self._automated_book_review_scraper.scrape_book_reviews(
                    num=num_reviews, driver=self._driver, skip_users=saved_reviews)
            scraped_book = Book(attributes=book_attribute, reviews=book_reviews)
            saved_isbns = self._get_saved_isbns()
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
        while len(url_list) < num_books:
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
        saved_urls = self._raw_data_storage.get_saved_book_urls(num_reviews)
        return saved_urls

    def _get_saved_reviews(self, isbn):
        """Retrieves the list of saved reviews for the given book (isbn)"""
        users = self._raw_data_storage.get_saved_review_users(isbn)
        return users

    @abstractmethod
    def _get_book_urls_from_page(self):
        pass

    @abstractmethod
    def _go_to_next_page_if_exists(self):
        pass



