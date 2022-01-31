import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# sets the number of seconds to sleep after a click to a new page
PAGE_SLEEP_TIME = 6     

class AmazonBookScraper():
    def __init__(self, url) -> None:
        if not isinstance(url, str) or not url:
            raise ValueError('URL must be a nonempty string.')
        self.scraper_init_done = False
        self.sorting_done = False
        self.url = url
        
        # inits selenium and gets to the url
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        time.sleep(PAGE_SLEEP_TIME)

    def sort_by_reviews(self):
        """
        Sort the results by number of reviews
        TODO: recieve the sort criterion as argument
        """
        # clicks on the sort by dropdown button
        xpath = '//span[@class = "a-dropdown-container"]'
        sort_dropdown = self.driver.find_element_by_xpath(xpath)
        xpath = './/span[@class="a-button-text a-declarative"]'
        sort_dropdown_button = sort_dropdown.find_element_by_xpath(xpath)
        sort_dropdown_button.click()

        # clicks on the sort criterion: sort by reviews
        xpath = '//div[@class="a-popover-inner"]'
        temp_tag = self.driver.find_element_by_xpath(xpath)
        sort_criteria = temp_tag.find_elements_by_xpath('./ul/li')
        xpath = './a'
        sort_criteria[-1].find_element_by_xpath(xpath).click()
        time.sleep(PAGE_SLEEP_TIME)
        self.sorting_done = True

    def go_to_next_page(self):
        """
        Goes to the next page if it not the last page
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        xpath = '//span[@class="s-pagination-strip"]'
        pagination_strip = self.driver.find_element_by_xpath(xpath)
        elements = pagination_strip.find_elements_by_xpath('./*')
        last_element = elements[-1]
        # if no next page returns False
        if last_element.find_elements(By.ID, "aria-disabled"):
            return False
        # else clicks on next and returns True
        else:
            last_element.click()
            time.sleep(PAGE_SLEEP_TIME)
            return True

    def get_page_links(self):
        """
        Gets all the links in the current page
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        # gets a list of book elements on the current page
        xpath = '//div[@class="s-main-slot s-result-list s-search-results sg-row"]'
        table_element = self.driver.find_element_by_xpath(xpath)
        xpath = './div[@data-asin]//a[@class="a-link-normal s-no-outline"]'
        books = table_element.find_elements_by_xpath(xpath)

        # extracts link from each book element and returns a list of links
        book_links = []
        for book in books:
            book_link = book.get_attribute('href')
            book_links.append(book_link)

        return book_links

    def get_book_links(self, num_books):
        """
        Extract only links to first num_books books.
        Considers the current page as the first page.
        """
        if not self.scraper_init_done:
            raise Exception('Scraper not initialized.')

        # gets links form the first page
        link_list = self.get_page_links()

        # cycles through pages in sequential order and gets page links
        while self.go_to_next_page() and len(link_list) < num_books:
            page_links = self.get_page_links()
            link_list.extend(page_links)

        # Closes the browser after extracting all links
        # self.driver.quit()  

        # returns only a maximum of num_books links
        if len(link_list) > num_books:
            return link_list[:num_books]
        else:
            return link_list

    def scrape_book_data_from_link(self, link):
        """
        Returns a dict with book attributes for a single book
        TODO: consider breaking this function into smaller pieces
        """
        # opens the book page
        self.driver.get(link)
        time.sleep(PAGE_SLEEP_TIME)

        book_dict = {}

        # gets the book title
        xpath = '//span[@id="productTitle"]'
        element = self.driver.find_element_by_xpath(xpath)
        # avoids player's handbooks because they are of different format
        # and will break the logic
        if "Player's Handbook" in element.text:
            return None
        book_dict["title"] = element.text

        # gets the author name
        xpath_1 = '//div[@id="authorFollow_feature_div"]'
        xpath_2 = '/div[@class="a-row a-spacing-top-small"]'
        xpath_3 = '/div[@class="a-column a-span4 authorNameColumn"]/a'
        elements = self.driver.find_elements_by_xpath(xpath_1+xpath_2+xpath_3)
        book_dict["author(s)"] = ",".join([element.text for element in elements])

        # gets some attributes
        xpath = '//div[@id="detailBullets_feature_div"]/ul/li'
        elements = self.driver.find_elements_by_xpath(xpath)
        book_dict["date"] = None
        book_dict["pages"] = None
        book_dict["isbn"] = None
        for element in elements:
            items = element.find_elements_by_xpath('./span/span')
            
            # extracts date attribute
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
                book_dict["date"] = date

            # extracts pages attribute
            if "pages" in items[1].text:
                pages_string = items[1].text
                pages = int(pages_string.split(" ")[0])
                book_dict["pages"] = pages

            # extracts isbn attribute
            if 'ISBN-10' in items[0].text:
                isbn_string = items[1].text
                book_dict["isbn"] = isbn_string

        # considers ISBN to be the unique id, so it is a must
        if book_dict["isbn"] is None:
            raise Exception(f"No ISBN for {book_dict['title']}")
        
        # gets product features
        book_dict["best_seller_rank"] = None
        book_dict["review_rating"] = None
        book_dict["review_count"] = None

        try: 
            xpath = '//div[@id="detailBulletsWrapper_feature_div"]/ul'
            elements = self.driver.find_elements_by_xpath(xpath)
            for element in elements:
                # gets best selling rating
                xpath = './li/span'
                best_seller_string = element.find_element_by_xpath(
                    xpath)
                best_seller_string = best_seller_string.text
                try:
                    start_idx = best_seller_string.index("#") + 1
                    idx = start_idx
                    while best_seller_string[idx] != " ":
                        idx += 1
                    best_seller_string = best_seller_string[start_idx:idx]
                    best_seller_string = "".join(best_seller_string.split(","))
                    best_seller_rank = int(best_seller_string)
                    book_dict["best_seller_rank"] = best_seller_rank
                except: 
                    pass
            
                # gets reviwer rating
                try:
                    xpath = './/span[@class="reviewCountTextLinkedHistogram noUnderline"]'
                    rating_element = element.find_element_by_xpath(xpath)
                    review_rating_string = rating_element.get_attribute(
                        "title")
                    review_rating = float(review_rating_string[:3])
                    book_dict["review_rating"] = review_rating
                except:
                    pass

                # gets review count
                try:
                    xpath = './/span[@id="acrCustomerReviewText"]'
                    count_element = element.find_element_by_xpath(xpath)
                    review_count_string = count_element.text
                    review_count_string = review_count_string.split(" ")[0]
                    review_count_string = "".join(review_count_string.split(","))
                    review_count = int(review_count_string)
                    book_dict["review_count"] = review_count
                except:
                    pass
        except:
            pass

        # gets cover page image link
        book_dict["image_link"] = None
        try:
            xpath = '//div[@id="main-image-container"]//img'
            element = self.driver.find_element_by_xpath(xpath)
            image_link = element.get_attribute("src")
            book_dict["image_link"] = image_link
        except:
            pass

        # gets book description
        book_dict["description"] = None
        try:
            xpath_1 = '//div[@data-a-expander-name="book_description_expander"]'
            xpath_2 = '/div/span'
            element = self.driver.find_element_by_xpath(xpath_1 + xpath_2)
            description = element.text
            book_dict["description"] = description
        except:
            pass

        return book_dict

    def scrape_books(self, num_books):
        """
        Collects num_books book links and then scraped data from 
        each link.
        Returns a list of dictionaries, with a dcitionay containing
        data of a single book
        """
        # sorts the books by a criterion 
        self.sort_by_reviews()

        self.scraper_init_done = True
        
        # gets all links for the required number of books
        book_links = self.get_book_links(num_books)

        # prepares a list of scraped book records
        scrape_list = []
        count = 0
        for book_link in book_links:
            book_dict = self.scrape_book_data_from_link(book_link)
            # add to list only if valid record
            if book_dict: scrape_list.append(book_dict)
            count += 1
            print(f'Count: {count}')

        # returns the list of book records (dicts)
        return scrape_list

if __name__ == '__main__':
    import pandas as pd

    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonBookScraper = AmazonBookScraper(url)
    # amazonBookScraper.scraper_init_done = True
    # amazonBookScraper.sort_by_reviews()
    # item_links = amazonBookScraper.get_book_links(100)
    # book_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/ref=sr_1_1?qid=1643367921&s=books&sr=1-1'
    # book_details = amazonBookScraper.scrape_book_data_from_link(book_url)
    book_records = amazonBookScraper.scrape_books(5)
    print(f'Total:{len(book_records)}')
    df = pd.DataFrame(book_records)
    print(df)



