"""This module implements a scraper class for scraping book details from 
a specific category in Amazon.com.
"""
from ctypes import Union
import os
from typing import Any, Union, Optional
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import uuid
import json
import urllib.request
from utils import create_dir_if_not_exists

# the number of seconds to sleep after a click to a new page
PAGE_SLEEP_TIME = 2

class AmazonBookScraper():
    """Scrapes any number of books from a ctaegory after sorting by a 
    specific criterion.

    Each book record consists of title, authors' name, publication date,
    cover page image, description, number of pages, isbn number, bestseller 
    rank, review rating, review count and uuidv4.

    The book category is hardcoded to "science finction and fantasy"

    The sort criterion is hardcoded to number of reviews (descending)
    """    

    def __init__(self, url: str,
                browser: str='chrome',
                banned_list: Optional[list[str]]=None) -> None:
        """Inits Selenium driver and gets to the given url

        Sorts the books by the criterion: number of reviews.
        TODO: accept the sort criterion as a parameter

        Args:
            url (str): expects the url to the required book category
            browser (str): which browser to use
            banned_list (str): list of banned phrases in the title
        """
        self._scraper_init_done = False
        self._url = url
        self._banned_list = banned_list
        self._browser = browser
        
        # init Selenium and get to the url
        try:
            if self._browser == 'chrome':
            self._driver = webdriver.Chrome()
            elif self._browser == 'firefox':
                self._driver = webdriver.Firefox()
            else:
                raise NotImplementedError('Only Chrome and Firefox are supported.')
        except:
            print('Selenium driver error')
        try:
            self._driver.get(self._url)
        except:
            print('Invalid url')
        time.sleep(PAGE_SLEEP_TIME)
        self._sort_by_reviews()
        self._scraper_init_done = True

    def scrape_books(
            self, num_books: int, 
            review_num = 10,
            save_loc: str=None,
            save_data: bool=False,
                    ) -> tuple[list[dict[Any, Any]], int]:
        """The main method that acquires the required number of
        book records

        Args:
            num_books (int): the number of books to acquire
            save_loc (str, optional): file save location
            save_data (bool, optional): flag to save data locally.
                                        Defaults to False.

        Returns:
            list[dict[Any, Any]]: list of num_books book records
            int: number of skipped books due to invlaid format
        """
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # get the links for the required number of books
        book_links = self.get_book_links(num_books)

        if save_data:
            # create the parent directory for local data storage
            if not save_loc:
                save_loc = os.getcwd()
            path_to_local_data_dir = save_loc + '/raw_data/'
            create_dir_if_not_exists(path_to_local_data_dir)

        # prepare a list of scraped book records
        scraped_record_list = []
        invalid_count = 0
        for count, book_link in enumerate(book_links):
            # get the book record for the book_link
            book_record = self.scrape_book_data_from_link(book_link, review_num=review_num)
            # continue with this book only if a valid record was created
            if book_record is None:
                invalid_count += 1
                continue
            if save_data:
                # each record dir is named after its isbn number
                # save a local copy only if it doesn't exist
                path_to_record = path_to_local_data_dir + book_record['isbn']
                if create_dir_if_not_exists(path_to_record):
                    self._save_book_record(path_to_record, book_record)
                else:
                    print(
                        f"Local record for '{book_record['title']}' already exisits")
            scraped_record_list.append(book_record)
            print(f'Book count: {count}')

        # return the list of book records (dicts) and the number of skipped books
        return scraped_record_list, invalid_count
    
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

    def get_book_links(self, num_books: int) -> list[str]:
        """Acquires num_books number of book urls from the sorted book listing

        Args:
            num_books (int): the required number of books

        Raises:
            Exception: if sraper is not initialized

        Returns:
            list[str]: list of book webpage urls
        """
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # get links form the first page
        book_link_list = self._get_book_links_from_current_page()

        # cycle through pages in sequential order and get page links
        while self._go_to_next_page() and len(book_link_list) < num_books:
            book_links_on_page = self._get_book_links_from_current_page()
            book_link_list.extend(book_links_on_page)

        # return only a maximum of num_books links
        if len(book_link_list) > num_books:
            return book_link_list[:num_books]
        else:
            return book_link_list

    def scrape_book_data_from_link(
                self, link: str,
                review_num: int=10) -> Union[dict[str, Any], None]:
        """Returns a dict with book attributes for a single book

        Args:
            link (str): url to the book webpage
            review_num (int): max number of reviews to scrape for each book

        Returns:
            Union[dict[str, Any], None]: dict record of a valid book
        """
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # open the book page
        try:
            self._driver.get(link)
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Could not open the book url.')

        book_record = {}

        # get the book title
        book_record["title"] = self._get_book_title(self._driver)
        # skip this record item if it is not in a valid format
        if book_record['title'] is None:
            return None

        # get the author names
        book_record["author(s)"] = self._get_book_author(self._driver)

        # get the book price
        book_record["price"] = self._get_book_price(self._driver)

        # get book attribute elements
        # this includes date, pages and ISBN number
        elements = self._get_book_attribute_elements(self._driver)

        # extract the ISBN attribute from book attribute elements
        book_record["isbn"] = self._extract_isbn_attribute(elements)
        # skip this record item if there is no isbn number
        if book_record['isbn'] is None:
            return None

        # extract the date attribute from book attribute elements if it exists
        book_record["date"] = self._extract_date_attribute(elements)

        # extract the pages attribute from book attribute elements if it exists
        book_record["pages"] = self._extract_pages_attribute(elements)

        # get product feature elements
        # this includes best seller rank, review rating and review count
        elements = self._get_product_feature_elements_from_link(self._driver)

        # extract the best seller rank from product feature elements if it exists
        book_record["best_seller_rank"] = self._extract_best_seller_ranking(
            elements)

        # extract the review rating from product feature elements if it exists
        book_record["review_rating"] = self._extract_review_rating(elements)

        # extract the review count from product feature elements if it exists
        book_record["review_count"] = self._extract_review_count(elements)

        # get the cover page image for the book
        book_record["image_link"] = self._get_cover_page_image(self._driver)

        # get the book description text
        book_record["description"] = self._get_book_description(self._driver)

        # get book reviews
        book_record["reviews"] = self._get_book_reviews(self._driver, num=review_num)

        # add a globally unique identifier for each book
        book_record['uuid'] = str(uuid.uuid4())

        return book_record

    @staticmethod
    def _save_book_record(path_to_record, book_record):
        """Save the book record locally."""
        try:
            # save the book record as a json object
            with open(f"{path_to_record}/data.json", mode='w') as f:
                json.dump(book_record, f)
            # save the cover page image file with isbn as name
            image_path = path_to_record + "/" + book_record['isbn']
            urllib.request.urlretrieve(
                book_record['image_link'], filename=image_path)
        except:
            print(f"Could not save the record for {book_record['title']}")

    def _go_to_next_page(self):
        """Goes to the next page if it not the last page."""
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

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

    def _get_book_links_from_current_page(self):
        """Gets all the links in the current page."""
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # get a list of book elements on the current page
        xpath = '//div[@class="s-main-slot s-result-list s-search-results sg-row"]'
        table_element = self._driver.find_element_by_xpath(xpath)
        xpath = './div[@data-asin]//a[@class="a-link-normal s-no-outline"]'
        books = table_element.find_elements_by_xpath(xpath)

        # extract link from each book element and returns a list of links
        book_links = []
        for book in books:
            book_link = book.get_attribute('href')
            book_links.append(book_link)

        return book_links

    def _get_book_title(self, driver):
        """Gets the book title from the current book webpage"""
        xpath = '//span[@id="productTitle"]'
        element = driver.find_element_by_xpath(xpath)
        # avoids player's handbooks because they are of different format
        # and will break the logic
        if isinstance(self._banned_list, list):
        for banned in self._banned_list:
            if banned in element.text:
            print(
                f'Skipping {element.text} since it is not in the right format')
            return None

            return element.text

    def _get_book_author(self, driver):
        """Gets the author names from the current book webpage"""
        xpath_1 = '//div[@id="authorFollow_feature_div"]'
        xpath_2 = '/div[@class="a-row a-spacing-top-small"]'
        xpath_3 = '/div[@class="a-column a-span4 authorNameColumn"]/a'
        elements = driver.find_elements_by_xpath(xpath_1+xpath_2+xpath_3)
        author_names = ",".join([element.text for element in elements])
        return author_names

    def _get_book_price(self, driver):
        """Gets the book's hardcover price"""
        xpath = '//div[@id="tmmSwatches"]'
        element = driver.find_element_by_xpath(xpath)
        price_str = element.text
        price_l = price_str.split('\n')
        if 'Paperback' in price_l:
            option = 'Paperback'
        elif 'Mass Market Paperback' in price_l:
            option = 'Mass Market Paperback'
        elif 'Hardcover' in price_l:
            option = 'Hardcover'
        else:
            return None
        i = price_l.index(option)
        price_str = price_l[i + 1]
        i = price_str.index('$')
        price = float(price_str[i+1:])
        return price

    def _get_book_attribute_elements(self, driver):
        """Gets some book attribute elements from the current webpage"""
        xpath = '//div[@id="detailBullets_feature_div"]/ul/li'
        elements = driver.find_elements_by_xpath(xpath)
        return elements

    def _extract_date_attribute(self, elements):
        """Extracts the book title from a list of book attribute elements.
        Return None if date attribute not found
        """
        date = None
        for element in elements:
            items = element.find_elements_by_xpath('./span/span')
            if "Publisher" in items[0].text:
                date_string = items[1].text
                # expects the date feature encolsed in paranthesis towards right
                if date_string[-1] != ")":
                    raise ValueError('No date value')
                start_idx = 0
                # searches backwards to find the opening bracket
                for i in range(len(date_string)-1, -1, -1):
                    if date_string[i] == "(":
                        start_idx = i
                        break
                else:
                    raise ValueError('No date value.')
                date = date_string[start_idx+1:-1]
                # removes a comma
                date = "".join(date.split(","))
        return date
    
    def _extract_pages_attribute(self, elements):
        """Extracts the page numbers from a list of book attribute elements.
        Return None if not found
        """
        pages = None
        for element in elements:
            items = element.find_elements_by_xpath('./span/span')
            if "pages" in items[1].text:
                pages_string = items[1].text
                pages = int(pages_string.split(" ")[0])
        return pages

    def _extract_isbn_attribute(self, elements):
        """Extracts the isbn number from a list of book attribute elements.
        Return None if not found
        """
        isbn = None
        for element in elements:
            items = element.find_elements_by_xpath('./span/span')
            if 'ISBN' in items[0].text:
                isbn = items[0].text[:-2] + '-' + items[1].text
        return isbn

    def _get_product_feature_elements_from_link(self, driver):
        """Gets some product feature elements from the current webpage"""
        xpath = '//div[@id="detailBulletsWrapper_feature_div"]/ul'
        elements = driver.find_elements_by_xpath(xpath)
        return elements

    def _extract_best_seller_ranking(self, elements):
        """Extracts the bestseller ranking from a list of product features.
        Return None if not found
        """
        best_seller_rank = None
        for element in elements:
            try:
                xpath = './li/span'
                best_seller_string = element.find_element_by_xpath(xpath)
                best_seller_string = best_seller_string.text
                start_idx = best_seller_string.index("#") + 1
                idx = start_idx
                while best_seller_string[idx] != " ":
                    idx += 1
                best_seller_string = best_seller_string[start_idx:idx]
                best_seller_string = "".join(best_seller_string.split(","))
                best_seller_rank = int(best_seller_string)
            except:
                pass
        return best_seller_rank

    def _extract_review_rating(self, elements):
        """Extracts the review ratings from a list of product features.
        Return None if not found
        """
        review_rating = None
        for element in elements:
            try:
                xpath = './/span[@class="reviewCountTextLinkedHistogram noUnderline"]'
                rating_element = element.find_element_by_xpath(xpath)
                review_rating_string = rating_element.get_attribute("title")
                review_rating = float(review_rating_string[:3])
            except:
                pass
        return review_rating

    def _extract_review_count(self, elements):
        """Extracts the review count from a list of product features.
        Return None if not found
        """
        review_count = None
        for element in elements:
            try:
                xpath = './/span[@id="acrCustomerReviewText"]'
                count_element = element.find_element_by_xpath(xpath)
                review_count_string = count_element.text
                review_count_string = review_count_string.split(" ")[0]
                review_count_string = "".join(review_count_string.split(","))
                review_count = int(review_count_string)
            except:
                pass
        return review_count

    def _get_cover_page_image(self, driver):
        """Extracts the cover page image from the current book page.
        Return None if not found
        """
        image_link = None
        try:
            xpath = '//div[@id="main-image-container"]//img'
            element = driver.find_element_by_xpath(xpath)
            image_link = element.get_attribute("src")
        except:
            pass
        return image_link

    def _get_book_description(self, driver):
        """Extracts the book description from the current book page.
        Return None if not found
        """
        description = ""
        try:
            xpath_1 = '//div[@data-a-expander-name="book_description_expander"]'
            xpath_2 = '/div/span'
            elements = driver.find_elements_by_xpath(xpath_1 + xpath_2)
            for element in elements:
                description = description + element.text
        except:
            pass
        return description

    def _get_book_reviews(self, driver, num=10):
        """Exctacts num top reviews from the current book page if available."""
        self._go_to_all_review_page(driver)
        reviews = []
        while len(reviews) < num:
            reviews.extend(self._extract_reviews_from_curr_page(driver))
            if not self._go_to_next_review_page_if_available(driver):
                break
        review_count = len(reviews)        
        return reviews[:num if num > review_count else review_count]
    
    def _go_to_all_review_page(self, driver):
        """Clicks on see all reviews on the current book page"""
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        xpath = '//a[@data-hook="see-all-reviews-link-foot"]'
        element = driver.find_element_by_xpath(xpath)
        element.click()
        time.sleep(PAGE_SLEEP_TIME)

    def _extract_reviews_from_curr_page(self, driver):
        xpath = '//div[@id="cm_cr-review_list"]/div[@data-hook="review"]'
        elements = driver.find_elements_by_xpath(xpath)
        reviews = []
        for element in elements:
            xpath = './/span[@data-hook="review-body"]/span'
            review_text = element.find_element_by_xpath(xpath).text
            xpath = './div/div/div/a[@class="a-link-normal"]'
            review_rating_text = element.find_element_by_xpath(
                xpath).get_attribute('title')
            rating_l = review_rating_text.split(" ")
            assert(rating_l[1] == 'out')
            assert(rating_l[2] == 'of')
            assert(rating_l[3] == '5')
            assert(rating_l[4] == 'stars')
            review_rating = int(float(rating_l[0]))
            reviews.append((review_text, review_rating))
        return reviews

    def _go_to_next_review_page_if_available(self, driver):
        xpath = '//div[@id="cm_cr-pagination_bar"]/ul/li'
        element = driver.find_elements_by_xpath(xpath)[1]
        next_label = element.get_attribute('class')
        if next_label == 'a-last':
            element.click()
            time.sleep(PAGE_SLEEP_TIME)
            return True
        else: 
            return False


if __name__ == '__main__':
    import pandas as pd
    import os

    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonBookScraper = AmazonBookScraper(url)
    book_records, _ = amazonBookScraper.scrape_books(5, review_num=20, save_data=True)
    print(f'Total:{len(book_records)}')
    df = pd.DataFrame(book_records)
    print(df)
    print(df['title'])
    print(df['author(s)'])
    print(df['date'])
    print(df['pages'])
    print(df['isbn'])
    print(df['best_seller_rank'])
    print(df['review_rating'])
    print(df['review_count'])
    print(df['image_link'])
    print(df['description'])
    print(df['uuid'])
    print(len(df['reviews']))



