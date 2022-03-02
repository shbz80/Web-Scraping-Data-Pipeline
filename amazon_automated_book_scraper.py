"""Provides the class for an Amazon specific automated book scraper """
import time
from selenium.webdriver.common.by import By
from automated_book_scraper import AutomatedBookScraper
from amazon_book_attribute_scraper import AmazonBookAttributeScraper
from amazon_automated_book_review_scraper import AmazonAutomatedBookReviewScraper
from raw_data_storage import RawDataStorage
from utils import PAGE_SLEEP_TIME

class AmazonAutomatedBookScraper(AutomatedBookScraper):
    """The Amazon specific class for automating the book scraping process."""
    def __init__(self, url: str, 
            book_attribute_scraper: AmazonBookAttributeScraper, 
            automated_book_review_scraper: AmazonAutomatedBookReviewScraper, 
            raw_data_storage: RawDataStorage,
            browser: str = 'chrome', 
            banned_titles: list[str] = None) -> None:
        super().__init__(url, 
                book_attribute_scraper,
                automated_book_review_scraper,
                raw_data_storage,
                browser, banned_titles)
        self._sort_by_reviews()

    def _get_book_urls_from_page(self):
        """Gets all the urls in the current page."""
        # get a list of book elements on the current page
        xpath = '//div[@class="s-main-slot s-result-list s-search-results sg-row"]'
        table_element = self._driver.find_element_by_xpath(xpath)
        xpath = './div[@data-asin]//a[@class="a-link-normal s-no-outline"]'
        books_elements = table_element.find_elements_by_xpath(xpath)

        # extract link from each book element and returns a list of links
        book_urls = []
        for books_element in books_elements:
            book_url = books_element.get_attribute('href')
            book_url = self._normalize_url(book_url)
            book_urls.append(book_url)

        return book_urls
    
    @staticmethod
    def _normalize_url(url):
        if 'ref=' in url:
            return url.split('ref=')[0]
        return url

    def _go_to_next_page_if_exists(self):
        """Goes to the next page if it not the last page."""
        # if no next page returns False else clicks on next and returns True
        xpath = '//span[@class="s-pagination-strip"]'
        pagination_strip = self._driver.find_element_by_xpath(xpath)
        elements = pagination_strip.find_elements_by_xpath('./*')
        last_element = elements[-1]
        if last_element.find_elements(By.ID, "aria-disabled"):
            return False
        else:
            last_element.click()
            time.sleep(PAGE_SLEEP_TIME)
            return True

    def _sort_by_reviews(self) -> None:
        """Sort the books by the number of reviews
        TODO: recieve the sort criterion as argument
        """
        # click on the sort by dropdown button
        try:
            xpath = '//span[@class = "a-dropdown-container"]'
            sort_dropdown = self._driver.find_element_by_xpath(xpath)
            xpath = './/span[@class="a-button-text a-declarative"]'
            sort_dropdown_button = sort_dropdown.find_element_by_xpath(xpath)
            sort_dropdown_button.click()
        except:
            print('Failed to click on sort by dropdown')

        # click on the sort criterion: sort by reviews
        try:
            xpath = '//div[@class="a-popover-inner"]'
            temp_tag = self._driver.find_element_by_xpath(xpath)
            sort_criteria = temp_tag.find_elements_by_xpath('./ul/li')
            xpath = './a'
            sort_criteria[-1].find_element_by_xpath(xpath).click()
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Failed to click on the sort option')

if __name__=='__main__':
    from os import getcwd
    from local_raw_data_storage import LocalRawDataStorage
    from s3_raw_data_storage import S3RawDataStorage

    url = "https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1645782603&ref=sr_pg_1"
    abas = AmazonBookAttributeScraper()
    aabrs = AmazonAutomatedBookReviewScraper()
    # storage = LocalRawDataStorage(path=getcwd())
    storage = S3RawDataStorage(path=None, bucket='aicore-web-scraping')
    aabs = AmazonAutomatedBookScraper(
                                    url=url,
                                    book_attribute_scraper=abas,
                                    automated_book_review_scraper=aabrs,
                                    raw_data_storage=storage,
                                    browser='firefox')
    aabs.scrape_books(num_books=11, num_reviews=5)