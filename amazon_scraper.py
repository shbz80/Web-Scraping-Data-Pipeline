import time
from selenium import webdriver
from selenium.webdriver.common.by import By

# sets the number of seconds to sleep after a click to a new page
PAGE_SLEEP_TIME = 3     

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
        self.driver.quit()  

        # returns only a maximum of num_books links
        if len(link_list) > num_books:
            return link_list[:num_books]
        else:
            return link_list

    # def scrape_book_data_from_link(self, link):
    #     """
    #     Returns a json dict with book attributes for a single book
    #     """
    #     self.driver.get(link)
    #     time.sleep(PAGE_SLEEP_TIME)

if __name__ == '__main__':
    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonBookScraper = AmazonBookScraper(url)
    amazonBookScraper.scraper_init_done = True
    amazonBookScraper.sort_by_reviews()
    item_links = amazonBookScraper.get_book_links(100)
    book_url = 'https://www.amazon.com/Midnight-Library-Novel-Matt-Haig/dp/0525559477/ref=sr_1_1?qid=1643367921&s=books&sr=1-1'
    amazonBookScraper.scrape_book_data_from_link(book_url)
    while True:
        pass
