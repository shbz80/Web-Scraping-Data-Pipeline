import time
from selenium import webdriver
from selenium.webdriver.common.by import By
import uuid
import json
import urllib.request
import os
from utils import create_dir_if_not_exists

# sets the number of seconds to sleep after a click to a new page
PAGE_SLEEP_TIME = 2 

class AmazonBookScraper():
    """[summary]
    """    
    def __init__(self, url) -> None:
        self.scraper_init_done = False
        self.url = url
        
        # init selenium and get to the url
        try:
            self.driver = webdriver.Chrome()
        except:
            print('Selenium driver error')
        try:
            self.driver.get(self.url)
        except:
            print('Invalid url')
        time.sleep(PAGE_SLEEP_TIME)

    def scrape_books(self, num_books, save_data=False):
        """
        Collects num_books book links and then scrape data from 
        each link.
        Returns a list of dictionaries, with a dcitionay containing
        record of a single book
        """
        # sorts the books by the criterion: number of reviews
        # TODO: accept the sort criterion as a parameter
        self.sort_by_reviews()

        self.scraper_init_done = True

        # get the links for the required number of books
        book_links = self.get_book_links(num_books)

        if save_data:
            # create the parent directory for local data storage
            path_to_local_data_dir = os.getcwd() + '/raw_data/'
            create_dir_if_not_exists(path_to_local_data_dir)

        # prepare a list of scraped book records
        scraped_record_list = []
        for count, book_link in enumerate(book_links):
            # get the book record for the book_link
            book_record = self.scrape_book_data_from_link(book_link)
            # continue with this book only if a valid record was created
            if book_record is None:
                continue
            if save_data:
                # each record dir is named after its isbn number
                # save a local copy only if it doesn't exist
                path_to_record = path_to_local_data_dir + book_record['isbn']
                if create_dir_if_not_exists(path_to_record):
                    self.__save_book_record(path_to_record, book_record)
                else:
                    print(
                        f"Local record for '{book_record['title']}' already exisits")
            scraped_record_list.append(book_record)
            print(f'Book count: {count}')

        # return the list of book records (dicts)
        return scraped_record_list
    
    def sort_by_reviews(self):
        """
        Sort the results by number of reviews
        TODO: recieve the sort criterion as argument
        """
        # click on the sort by dropdown button
        try:
            xpath = '//span[@class = "a-dropdown-container"]'
            sort_dropdown = self.driver.find_element_by_xpath(xpath)
            xpath = './/span[@class="a-button-text a-declarative"]'
            sort_dropdown_button = sort_dropdown.find_element_by_xpath(xpath)
            sort_dropdown_button.click()
        except:
            print('Failed to click on sort by dropdown')

        # click on the sort criterion: sort by reviews
        try:
            xpath = '//div[@class="a-popover-inner"]'
            temp_tag = self.driver.find_element_by_xpath(xpath)
            sort_criteria = temp_tag.find_elements_by_xpath('./ul/li')
            xpath = './a'
            sort_criteria[-1].find_element_by_xpath(xpath).click()
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Failed to click on the sort option')

    def get_book_links(self, num_books):
        """
        Extract links of first num_books books.
        Considers the current page as the first page.
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        # get links form the first page
        book_link_list = self.__get_book_links_from_current_page()

        # cycle through pages in sequential order and get page links
        while self.__go_to_next_page() and len(book_link_list) < num_books:
            book_links_on_page = self.__get_book_links_from_current_page()
            book_link_list.extend(book_links_on_page)

        # return only a maximum of num_books links
        if len(book_link_list) > num_books:
            return book_link_list[:num_books]
        else:
            return book_link_list

    def scrape_book_data_from_link(self, link):
        """
        Returns a dict with book attributes for a single book
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        # open the book page
        try:
            self.driver.get(link)
            time.sleep(PAGE_SLEEP_TIME)
        except:
            print('Could not open the book url.')

        book_record = {}

        # get the book title
        book_record["title"] = self.__get_book_title(self.driver)
        # skip this record item if it is not in a valid format
        if book_record['title'] is None:
            return None

        # extract the ISBN attribute from book attribute elements
        book_record["isbn"] = self.__extract_isbn_attribute(elements)
        # skip this record item if there is no isbn number
        if book_record['isbn'] is None:
            return None

        # get the author names
        book_record["author(s)"] = self.__get_book_author(self.driver)

        # get book attribute elements
        # this includes date, pages and ISBN-13 number
        elements = self.__get_book_attribute_elements(self.driver)

        # extract the date attribute from book attribute elements if it exists
        book_record["date"] = self.__extract_date_attribute(elements)

        # extract the pages attribute from book attribute elements if it exists
        book_record["pages"] = self.__extract_pages_attribute(elements)

        # get product feature elements
        # this includes best seller rank, review rating and review count
        elements = self.__get_product_feature_elements_from_link(self.driver)

        # extract the best seller rank from product feature elements if it exists
        book_record["best_seller_rank"] = self.__extract_best_seller_ranking(
            elements)

        # extract the review rating from product feature elements if it exists
        book_record["review_rating"] = self.__extract_review_ranting(elements)

        # extract the review count from product feature elements if it exists
        book_record["review_count"] = self.__extract_review_count(elements)

        # get the cover page image for the book
        book_record["image_link"] = self.__get_cover_page_image(self.driver)

        # get the book description text
        book_record["description"] = self.__get_book_description(self.driver)

        # add a globally unique identifier for each book
        book_record['uuid'] = str(uuid.uuid4())

        return book_record

    @staticmethod
    def __save_book_record(path_to_record, book_record):
        try:
            # save the book record as a json object
            with open(f"{path_to_record}/data.json", mode='w') as f:
                json.dump(book_record, f)
            # save the cover page image file
            urllib.request.urlretrieve(
                book_record['image_link'], filename=path_to_record+'/0.jpg')
        except:
            print(f"Could not save the record for {book_record['title']}")

    def __go_to_next_page(self):
        """
        Goes to the next page if it not the last page
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        # if no next page returns False else clicks on next and returns True
        xpath = '//span[@class="s-pagination-strip"]'
        pagination_strip = self.driver.find_element_by_xpath(xpath)
        elements = pagination_strip.find_elements_by_xpath('./*')
        last_element = elements[-1] 
        if last_element.find_elements(By.ID, "aria-disabled"):
            return False
        else:
            last_element.click()
            time.sleep(PAGE_SLEEP_TIME)
            return True

    def __get_book_links_from_current_page(self):
        """
        Gets all the links in the current page
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        # get a list of book elements on the current page
        xpath = '//div[@class="s-main-slot s-result-list s-search-results sg-row"]'
        table_element = self.driver.find_element_by_xpath(xpath)
        xpath = './div[@data-asin]//a[@class="a-link-normal s-no-outline"]'
        books = table_element.find_elements_by_xpath(xpath)

        # extract link from each book element and returns a list of links
        book_links = []
        for book in books:
            book_link = book.get_attribute('href')
            book_links.append(book_link)

        return book_links

    def __get_book_title(self, driver):
        xpath = '//span[@id="productTitle"]'
        element = driver.find_element_by_xpath(xpath)
        # avoids player's handbooks because they are of different format
        # and will break the logic
        # TODO: implement a list of banned keywords/phrases
        if "Player's Handbook" in element.text:
            print(
                f'Skipping {element.text} since it is not in the right format')
            return None
        else:
            return element.text

    def __get_book_author(self, driver):
        xpath_1 = '//div[@id="authorFollow_feature_div"]'
        xpath_2 = '/div[@class="a-row a-spacing-top-small"]'
        xpath_3 = '/div[@class="a-column a-span4 authorNameColumn"]/a'
        elements = driver.find_elements_by_xpath(xpath_1+xpath_2+xpath_3)
        author_names = ",".join([element.text for element in elements])
        return author_names

    def __get_book_attribute_elements(self, driver):
        xpath = '//div[@id="detailBullets_feature_div"]/ul/li'
        elements = driver.find_elements_by_xpath(xpath)
        return elements

    def __extract_date_attribute(self, elements):
        # return None if date attribute not found
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
    
    def __extract_pages_attribute(self, elements):
        pages = None
        for element in elements:
            items = element.find_elements_by_xpath('./span/span')
            if "pages" in items[1].text:
                pages_string = items[1].text
                pages = int(pages_string.split(" ")[0])
        return pages

    def __extract_isbn_attribute(self, elements):
        isbn = None
        for element in elements:
            items = element.find_elements_by_xpath('./span/span')
            if 'ISBN' in items[0].text:
                isbn = items[0].text[:-2] + '-' + items[1].text
        return isbn

    def __get_product_feature_elements_from_link(self, driver):
        xpath = '//div[@id="detailBulletsWrapper_feature_div"]/ul'
        elements = driver.find_elements_by_xpath(xpath)
        return elements

    def __extract_best_seller_ranking(self, elements):
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

    def __extract_review_ranting(self, elements):
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

    def __extract_review_count(self, elements):
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

    def __get_cover_page_image(self, driver):
        image_link = None
        try:
            xpath = '//div[@id="main-image-container"]//img'
            element = driver.find_element_by_xpath(xpath)
            image_link = element.get_attribute("src")
        except:
            pass
        return image_link

    def __get_book_description(self, driver):
        description = None
        try:
            xpath_1 = '//div[@data-a-expander-name="book_description_expander"]'
            xpath_2 = '/div/span'
            element = driver.find_element_by_xpath(xpath_1 + xpath_2)
            description = element.text
        except:
            pass
        return description

if __name__ == '__main__':
    import pandas as pd

    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonBookScraper = AmazonBookScraper(url)
    # amazonBookScraper.scraper_init_done = True
    # amazonBookScraper.sort_by_reviews()
    # item_links = amazonBookScraper.get_book_links(100)
    # book_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/ref=sr_1_1?qid=1643367921&s=books&sr=1-1'
    # book_details = amazonBookScraper.scrape_book_data_from_link(book_url)
    book_records = amazonBookScraper.scrape_books(200, save_data=True)
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



