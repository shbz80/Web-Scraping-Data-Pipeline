"""Provides Amazon specific class for automated review scraping"""
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from entities import Review
from book_review_scraper import AutomatedBookReviewScraper
from amazon_book_review_scraper import AmazonBookReviewScraper
from utils import PAGE_SLEEP_TIME, TIME_OUT


class AmazonAutomatedBookReviewScraper(
    AutomatedBookReviewScraper, AmazonBookReviewScraper):
    """Amazon specific class for automated review scraping"""

    @staticmethod
    def _get_to_first_review_page(driver: webdriver) -> None:
        """Clicks on see all reviews on the current book page"""
        try:
            xpath = '//a[@data-hook="see-all-reviews-link-foot"]'
            # element = driver.find_element_by_xpath(xpath)
            element = WebDriverWait(driver, TIME_OUT).until(
                EC.presence_of_element_located((By.XPATH, xpath)))
            element.click()
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Could not get to the first review page')

    @staticmethod
    def _go_to_next_review_page_if_available(driver: webdriver) -> None:
        try:
            xpath = '//div[@id="cm_cr-pagination_bar"]/ul/li'
            # element = driver.find_elements_by_xpath(xpath)[1]
            element = WebDriverWait(driver, TIME_OUT).until(
                EC.presence_of_all_elements_located((By.XPATH, xpath)))
            element = element[1]
            next_label = element.get_attribute('class')
            if next_label == 'a-last':
                element.click()
                time.sleep(PAGE_SLEEP_TIME)
                return True
            else:
                return False
        except:
            print('Could not advance to the next review page.')



        
