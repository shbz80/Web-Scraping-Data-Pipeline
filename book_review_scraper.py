"""Provides classes for review scraping."""
from abc import ABC, abstractmethod
import time
from selenium import webdriver
from entities import Review
from utils import PAGE_SLEEP_TIME

class BookReviewScraper(ABC):
    """Abstract class for scraping reviews on a single page."""

    @abstractmethod
    def scrape_reviews_from_curr_page(
            self, driver: webdriver = None, url: str = None,
            skip_users: list[str] = None) -> list[Review]:
        pass


class AutomatedBookReviewScraper(BookReviewScraper):
    """Abstract class for automating scraping a required number
    of reviews from a book.
    """
    def scrape_book_reviews(
            self, num: int = 10, driver: webdriver = None,
            url: str = None, skip_users: list[str] = None) -> list[Review]:
        """Scrapes up to num reviews from users not in the list skip_users.

        Args:
            num (int, optional): number of reviews to scrape.
            driver (webdriver, optional): webdriver ponting to the book page
            url (str, optional): the book url
            skip_users (list[str], optional): list of user reviews to skip

        Returns:
            list[Review]: list of scraped reviews
        """
        if not driver and not url:
            raise ValueError('Requires either the webdriver or the url.')

        if not driver and url:
            driver = webdriver.Firefox()
            driver.get(url)
            time.sleep(PAGE_SLEEP_TIME)

        self._get_to_first_review_page(driver)
        reviews = []
        # scrape at least num reviews
        while len(reviews) < num:
            reviews.extend(
                self.scrape_reviews_from_curr_page(
                    driver=driver, skip_users=skip_users))
            # got to next review page, break if no next page
            if not self._go_to_next_review_page_if_available(driver):
                break
        review_count = len(reviews)
        # remove excess reviews and return
        return reviews[:num if num < review_count else review_count]

    @staticmethod
    @abstractmethod
    def _get_to_first_review_page(driver: webdriver) -> None:
        pass
    
    @staticmethod
    @abstractmethod
    def _go_to_next_review_page_if_available(driver: webdriver) -> None:
        pass
