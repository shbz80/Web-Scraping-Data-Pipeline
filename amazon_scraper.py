"""This module implements a scraper class for scraping book details from 
a specific category in Amazon.com.
"""
import os
from typing import Any, Union, Optional
import time
import operator
from selenium import webdriver
from selenium.webdriver.common.by import By
import pandas as pd
import uuid
import json
import urllib.request
import boto3
from sqlalchemy import create_engine, inspect
from utils import create_dir_if_not_exists
# the number of seconds to sleep after a click to a new page
PAGE_SLEEP_TIME = 1


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
                 browser: str = 'chrome',
                banned_list: Optional[list[str]] = None) -> None:
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
        self._save_strategy = None

        # init Selenium and get to the url
        try:
            if self._browser == 'chrome':
                self._driver = webdriver.Chrome()
            elif self._browser == 'firefox':
                self._driver = webdriver.Firefox()
            else:
                raise NotImplementedError(
                    'Only Chrome and Firefox are supported.')
        except:
            print('Selenium driver error')
        try:
            self._driver.get(self._url)
        except:
            print('Invalid url')
        time.sleep(PAGE_SLEEP_TIME)
        self._sort_by_reviews()
        self._scraper_init_done = True

    def scrape_books(self, 
                num_books: int,
                save_opt: Optional[dict] = None,
                review_num=10) -> tuple[list[dict], list[dict]]:
        """The main method that acquires the required number of
        book records and reviews. It returns two lists of items:
        1) list of scraped book attributes except reviews (records)
        2) list of scraped book reviews (reviews)
        Since each book has review_num reviews, 2) is review_num times
        larger than 1).
        All reviews for a book has the book uuid associated with it.

        Args:
            num_books (int): the number of books to acquire
            save_opt (dict, optional): dict that contains local/cloud
                                       save details
            review_num (int): number of reviews for each book

        Returns:
            list[dict]: list of num_books book records
            list[dict]: list of num_books book reviews
        """
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # get the links for the required number of books
        book_links = self.get_book_links(num_books)

        # initialize data storage if required
        if save_opt is not None:
            self._initialize_data_saving(save_opt)
        else:
            self._save_strategy = None

        # prepare a list of scraped book records and reviews
        scraped_record_list = []
        scraped_review_list = []
        for count, book_link in enumerate(book_links):
            # check if the book has valid isbn
            # this has side effect: the driver points to the page
            isbn = self._get_isbn_from_book_link(book_link)
            if isbn is None:
                continue
            # check if the book is already scraped. This is checked
            # either in local storage or the cloud (S3 and RDS)
            # based on the save stratgey.
            if self._save_strategy:
                if self._is_scraped(isbn):
                    continue
            # get the book record for the book_link
            # the driver already points to the page
            book_record, book_reviews = self.scrape_book_data_from_link(
                review_num=review_num)
            # continue only if the book data is valid and not already scraped
            if book_record is None:
                continue
            # save data either locally or in the cloud based on the save strategy
            # saves in the cloud as raw data and an RDS,
            # both of which are expected to always match
            if save_opt is not None:
                self._save_book_data(book_record, book_reviews)
                
            scraped_record_list.append(book_record)
            scraped_review_list.extend(book_reviews)
            print(f'Book count: {count}')

        # return the list of book records and reviews
        return scraped_record_list, scraped_review_list

    def get_cover_page_image_from_cloud(self, book_id):
        '''Checks is the book record exists in the RDS
        and extracts the image from S3 bucket'''
        if not self._is_saved_in_cloud(book_id):
            return None
        
        s3 = boto3.resource('s3')
        project_bucket = s3.Bucket(self._s3_bucket)
        for file in project_bucket.objects.all():
            if book_id in file.key and ".jpg" in file.key:
                image_key = file.key
                break
        self._s3_client.download_file(
            self._s3_bucket, image_key, os.getcwd() + f'/temp/{book_id}.jpg')
                
    def _initialize_data_saving(self, save_opt):
        if not isinstance(save_opt, dict):
            raise ValueError('Save option should be a dict.')

        # create the parent directory if local data storage
        if save_opt['strategy'] == 'local':
            self._path_to_local_data_dir = save_opt['location'] + '/raw_data'
            self._save_strategy = 'local'
            create_dir_if_not_exists(self._path_to_local_data_dir)
        # initialize cloud client (boto3 for S3 bucket) and
        # RDS, if cloud storage
        elif save_opt['strategy'] == 'cloud':
            self._s3_client = boto3.client('s3')
            self._s3_root_folder = 'raw_data'
            self._s3_bucket = save_opt['location']
            self._save_strategy = 'cloud'
            DATABASE_TYPE = save_opt['rds']['DATABASE_TYPE']
            DBAPI = save_opt['rds']['DBAPI']
            ENDPOINT = save_opt['rds']['ENDPOINT']
            USER = save_opt['rds']['USER']
            PASSWORD = save_opt['rds']['PASSWORD']
            PORT = save_opt['rds']['PORT']
            DATABASE = save_opt['rds']['DATABASE']
            self._rds_engine = create_engine(
                f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{ENDPOINT}:{PORT}/{DATABASE}")
            self._rds_engine.connect()
            self._rds_attribute_table = 'book_attributes'
            self._rds_review_table = 'book_reviews'
        else:
            raise ValueError('Invalid save strategy.')

    def _save_book_data(self, book_record, book_reviews):
        if self._save_strategy:
            if self._save_strategy == 'local':
                # each record dir is named after its isbn number
                # saves a local copy only if it doesn't exist
                self._save_local_book_record(
                        book_record, book_reviews)
            elif self._save_strategy == 'cloud':
                # saves a copy only if it doesn't exist in cloud
                self._save_cloud_book_record(
                        book_record, book_reviews)
            else:
                raise ValueError('Invalid save strategy.') 

    def _save_local_book_record(self, book_record, book_reviews):
        """Save the book record locally."""
        path_to_record = self._path_to_local_data_dir + \
            '/' + book_record['isbn']
        if not create_dir_if_not_exists(path_to_record):
            print(
                f"Local record for '{book_record['title']}' already exisits")
            return

        try:
            # save the book record as a json object
            with open(f"{path_to_record}/data.json", mode='w') as f:
                json.dump(book_record, f)
        except:
            print(f"Could not save the record for {book_record['title']}")

        try:
            # save the cover page image file with isbn as name
            image_path = path_to_record + "/" + book_record['isbn'] + ".jpg"
            urllib.request.urlretrieve(
                book_record['image_link'], filename=image_path)
        except:
            print(f"Could not save coverpage image for {book_record['title']}")

        try:
            # create the review folder
            path_to_review_dir = path_to_record + '/reviews'
            create_dir_if_not_exists(path_to_review_dir)
            if isinstance(book_reviews, list):
                # save each review as a json file
                for i, review in enumerate(book_reviews):
                    with open(f"{path_to_review_dir}/data{i}.json", mode='w') as f:
                        json.dump(review, f)
        except:
            print(f"Could not save reviews for {book_record['title']}")

    def _is_in_s3(self, book_id):
        s3 = boto3.resource('s3')
        project_bucket = s3.Bucket(self._s3_bucket)
        for file in project_bucket.objects.all():
            file_id_l = (file.key).split('/')
            if file_id_l[1] == book_id:
                return True
        return False

    def _is_in_rds(self, book_id):
        # assumes rds_engine is connected
        insp = inspect(self._rds_engine)
        if not insp.has_table(self._rds_attribute_table):
            return False
        else:
            return bool(self._rds_engine.execute(
                f'''SELECT COUNT(1) FROM {self._rds_attribute_table} WHERE isbn = '{book_id}';''').fetchall()[0][0])

    def _is_saved_in_cloud(self, book_id):
        # check in S3
        in_s3 = self._is_in_s3(book_id)
        in_rds = self._is_in_rds(book_id)
        # it is expected S3 and RDS to be macthed
        if operator.xor(in_s3, in_rds):
            raise Exception('Unmatched entry in S3 and RDS')
        return in_s3 and in_rds

    def _is_saved_in_local(self, book_id):
        scraped_books = next(os.walk(self._path_to_local_data_dir))[1]
        return book_id in scraped_books

    def _save_cloud_book_record(self, book_record, book_reviews):
        """Save the book record in the cloud."""
        if not (self._s3_client and self._rds_engine):
            raise Exception('Cloud storage not initialized')

        # do not save if the book details are already in the cloud
        if self._is_saved_in_cloud(book_record['isbn']):
            print(
                f"Cloud record for '{book_record['title']}' already exisits")
            return

        # save the book record as a json object in S3
        path_to_record = self._s3_root_folder + '/' + book_record['isbn']
        file_key = path_to_record + '/data.json'
        try:
            self._s3_client.put_object(Bucket=self._s3_bucket,
                                Body=json.dumps(book_record),
                                Key=file_key)
        except:
            print(
                f"Could not save the record for {book_record['title']} in S3")

        # save the book record in RDS
        book_record_df = pd.DataFrame([book_record])
        try:
            book_record_df.to_sql(
                self._rds_attribute_table,
                self._rds_engine, if_exists='append',
                index=False)
        except:
            print(
                f"Could not save the record for {book_record['title']} in RDS")

        # save the cover page image file with isbn as name in S3
        # retirieve the image file to a temporary local location
        temp_path = os.getcwd() + '/temp'
        create_dir_if_not_exists(temp_path)
        try:
            temp_image_path = temp_path + '/tmp.jpg'
            urllib.request.urlretrieve(
                book_record['image_link'], filename=temp_image_path)
        except:
            print(f"Could retrieve coverpage image for {book_record['title']}")
        # upload the image file to cloud (S3)
        file_key = path_to_record + "/" + book_record['isbn'] + ".jpg"
        try:
            self._s3_client.upload_file(
                temp_image_path, self._s3_bucket, file_key)
        except:
            print(
                f"Could not save the image for {book_record['title']} in S3")

        # save the reviews in S3
        path_to_reviews = path_to_record + '/reviews'
            for i, review in enumerate(book_reviews):
                try:
                    # save each review as a json file
                    file_key = f"{path_to_reviews}/data{i}.json"
                    self._s3_client.put_object(Bucket=self._s3_bucket,
                                        Body=json.dumps(review),
                                        Key=file_key)
                except:
                print(
                    f"Could not save review {i} for {book_record['title']} in S3")

        # save the reviews in RDS
        book_reviews_df = pd.DataFrame(book_reviews)
        try:
            book_reviews_df.to_sql(
                self._rds_review_table,
                self._rds_engine,
                if_exists='append',
                index=False)
        except:
            print(
                f"Could not save reviews for {book_record['title']} in RDS")
            
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

    def _is_scraped(self, book_id):
        is_saved = False
        if self._save_strategy == 'cloud':
            is_saved = self._is_saved_in_cloud(book_id)
        elif self._save_strategy == 'local':
            is_saved = self._is_saved_in_local(book_id)
        else:
            raise Exception
        return is_saved

    def _get_isbn_from_book_link(self, link):
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # open the book page
        try:
            self._driver.get(link)
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Could not open the book url.')

        elements = self._get_book_attribute_elements(self._driver)
        return self._extract_isbn_attribute(elements)

    def scrape_book_data_from_link(
            self, link: Optional[str] = None,
            review_num: int = 10) -> tuple[Optional[dict], Optional[list[dict]]]:
        """Returns a dict with book attributes for a single book

        Args:
            link (str): url to the book webpage. Assumes the driver already
                        points to the page if None
            review_num (int): max number of reviews to scrape for each book

        Returns:
            Optional[dict]: dict record of a valid book
            Optional[list[dict]]: list of dict reviews a valid book
        """
        if link:
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        # open the book page
        try:
            self._driver.get(link)
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Could not open the book url.')

        book_record = {}
        # get book attribute elements
        # this includes date, pages and ISBN number
        elements = self._get_book_attribute_elements(self._driver)

        # extract the ISBN attribute from book attribute elements
        book_record["isbn"] = self._extract_isbn_attribute(elements)
        # skip this book item if there is no isbn number
        if book_record['isbn'] is None:
            return None, None

        # extract the date attribute from book attribute elements if it exists
        book_record["date"] = self._extract_date_attribute(elements)

        # extract the pages attribute from book attribute elements if it exists
        book_record["pages"] = self._extract_pages_attribute(elements)

        # get the book title
        book_record["title"] = self._get_book_title(self._driver)
        # skip this record item if it is not in a valid format
        if book_record['title'] is None:
            return None, None

        # get the author names
        book_record["author(s)"] = self._get_book_author(self._driver)

        # get the book price
        book_record["price"] = self._get_book_price(self._driver)

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

        # add a globally unique identifier for each book
        book_record['uuid'] = str(uuid.uuid4())

        # get book reviews, this is a seperate list of dicts
        book_reviews = self._get_book_reviews(self._driver, num=review_num)
        # append the book's uuid for all reviews
        for review in book_reviews:
            review['isbn'] = book_record['isbn']

        return book_record, book_reviews

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
            if 'ISBN-13' in items[0].text:
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
        """Extracts the average review ratings from a list of product features.
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
            xpath = '//div[@id="main-image-container"]//img[@id="imgBlkFront"]'
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
        return reviews[:num if num < review_count else review_count]

    def _go_to_all_review_page(self, driver):
        """Clicks on see all reviews on the current book page"""
        if not self._scraper_init_done:
            raise Exception('Scraper not initialized.')

        xpath = '//a[@data-hook="see-all-reviews-link-foot"]'
        element = driver.find_element_by_xpath(xpath)
        element.click()
        time.sleep(PAGE_SLEEP_TIME)

    def _extract_reviews_from_curr_page(self, driver):
        """Extracts both review text and rating of the reviews"""
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
            reviews.append({'text': review_text, 'rating': review_rating})
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
