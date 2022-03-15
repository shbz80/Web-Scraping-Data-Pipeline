"""Provides the Amazon specific review sraper for a single page."""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from entities import Review
from book_review_scraper import BookReviewScraper
from utils import PAGE_SLEEP_TIME, TIME_OUT

class AmazonBookReviewScraper(BookReviewScraper):
    """Amazon specific review sraper for a single page"""
    def scrape_reviews_from_curr_page(
            self, isbn: str, driver: webdriver = None, url: str = None,
            skip_users: list[str] = None) -> list[Review]:
        """ Scrapes reviews from the current page.
        Expects either the webdriver or the url.

        Args:
            isbn (str): book isbn number
            driver (webdriver, optional): webdriver point to the review page
            url (str, optional): url of the review page
            skip_users (list[str], optional): list of users to skip

        Returns:
            list[Review]: list of scraped reviews
        """
        if not driver and not url:
            raise ValueError('Requires either the webdriver or the url.')

        if not driver and url:
            driver = webdriver.Firefox()
            driver.get(url)
            time.sleep(PAGE_SLEEP_TIME)
        # get a list of review elements in the current page
        xpath = '//div[@id="cm_cr-review_list"]/div[@data-hook="review"]'
        # elements = driver.find_elements_by_xpath(xpath)
        elements = WebDriverWait(driver, TIME_OUT).until(
            EC.presence_of_all_elements_located((By.XPATH, xpath)))
        reviews = []
        for element in elements:
            user = self._get_review_user_from_element(element)
            if user is None:
                continue
            if isinstance(skip_users, list) and user in skip_users:
                continue
            text = self._get_review_text_from_element(element)
            if text is None:
                continue
            rating = self._get_review_rating_from_element(element)
            review = Review(isbn, text, rating, user)
            reviews.append(review)
        return reviews
    
    @staticmethod
    def _get_review_rating_from_element(element):
        xpath = './div/div/div/a[@class="a-link-normal"]'
        try:
            review_rating_text = element.find_element_by_xpath(
                xpath).get_attribute('title')
            rating_l = review_rating_text.split(" ")
            assert(rating_l[1] == 'out')
            assert(rating_l[2] == 'of')
            assert(rating_l[3] == '5')
            assert(rating_l[4] == 'stars')
            return int(float(rating_l[0]))
        except:
            return None

    @staticmethod
    def _get_review_text_from_element(element):
        xpath = './/span[@data-hook="review-body"]/span'
        try:
            return element.find_element_by_xpath(xpath).text
        except:
            return None
    
    @staticmethod
    def _get_review_user_from_element(element):
        xpath = './/div[@class="a-profile-content"]/span[@class="a-profile-name"]'
        try:
            return element.find_element_by_xpath(xpath).text
        except:
            return None




