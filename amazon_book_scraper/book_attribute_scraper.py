"""Provides the class for scraping book attributes."""
from abc import ABC, abstractmethod
from typing import Optional
import time
import uuid
from selenium import webdriver
from entities import BookAttribute
from utils import PAGE_SLEEP_TIME

class BookAttributeScraper(ABC):
    """The abstract class for the book attributes scraper."""
    def __init__(self, banned_titles: list[str] = None) -> None:
        """
        Args:
            banned_titles (str, optional): list of banned phrases in title
        """
        if banned_titles is None:
            self._banned_titles = []
        elif isinstance(banned_titles, list):
            self._banned_titles = banned_titles
        else:
            raise ValueError('Expected a list.')

    def scrape_book_attributes_from_page(
            self, url: str, 
            driver: webdriver = None) -> Optional[BookAttribute]:
        """Scrapes all attributes from the book page

        Args:
            url (str): book url
            driver (webdriver, optional): webdriver

        Returns:
            Optional[BookAttribute]: scraped BookAttribute object
        """
        if not driver:
            driver = webdriver.Firefox()
        driver.get(url)
        time.sleep(PAGE_SLEEP_TIME)

        if not self._initialize(driver):
            return None

        title = self._extract_title_attribute(driver)
        if title is None:
            return None
        # if any of the banned phrases appear in the tile
        # drop the book
        for banned_title in self._banned_titles:
            if banned_title in title:
                print(f'{title} is banned!')
                return None

        isbn = self._extract_isbn_attribute(driver)
        if isbn is None: 
            return None

        language = self._extract_language_attribute(driver)
        if not language or language != 'English':
            return None
            
        uuid_str = str(uuid.uuid4())
        author = self._extract_author_attribute(driver)
        description = self._extract_description_attribute(driver)
        date = self._extract_date_attribute(driver)
        pages = self._extract_pages_attribute(driver)
        price = self._extract_price_attribute(driver)
        best_seller_rank = self._extract_best_seller_rank_attribute(driver)
        review_rating = self._extract_review_rating_attribute(driver)
        review_count = self._extract_review_count_attribute(driver)
        image_url = self._extract_image_url_attribute(driver)

        book_attributes = BookAttribute(
                                        title=title,
                                        isbn=isbn,
                                        uuid=uuid_str,
                                        author=author,
                                        description=description,
                                        date=date,
                                        pages=pages,
                                        price=price,
                                        best_seller_rank=best_seller_rank,
                                        review_rating=review_rating,
                                        review_count=review_count,
                                        image_url=image_url,
                                        book_url=url
                                        )
        return book_attributes
    
    @abstractmethod
    def _initialize(self, driver) -> bool:
        pass

    @abstractmethod
    def _extract_isbn_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_title_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_language_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_author_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_description_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_date_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_pages_attribute(self, driver):
        pass
        
    @abstractmethod
    def _extract_price_attribute(self, driver):
        pass
        
    @abstractmethod
    def _extract_best_seller_rank_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_review_rating_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_review_count_attribute(self, driver):
        pass

    @abstractmethod
    def _extract_image_url_attribute(self, driver):
        pass