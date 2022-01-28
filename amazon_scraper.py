import time
from selenium import webdriver
from selenium.webdriver.common.by import By


class AmazonScraper():
    def __init__(self, url) -> None:
        if not isinstance(url, str) or not len(url):
            raise ValueError('URL must be a nonempty string.')
        self.url = url
        self.driver = None

    def get_items(self, num_items, sort_oder) -> list:
        pass

    def connect_to_link(self):
        """
        Initializes Selenium and connects to the starting url
        """
        # inits selenium and gets to the link
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)

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
        time.sleep(3)

    def go_to_next_page(self):
        """
        Goes to the next page if it not the last page
        """
        xpath = '//span[@class="s-pagination-strip"]'
        pagination_strip = self.driver.find_element_by_xpath(xpath)
        elements = pagination_strip.find_elements_by_xpath('./*')
        last_element = elements[-1]
        # if not next page returns False
        if last_element.find_elements(By.ID, "aria-disabled"):
            return False
        # else clicks on next and returns True
        else:
            last_element.click()
            time.sleep(3)
            return True

    def get_page_links(self):
        """
        Gets all the links in the current page
        """
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

    def get_item_links(self, num_items):
        """
        Extract only links to first num_items items.
        Considers the current page as the first page.
        """

        # gets links form the first page
        link_list = self.get_page_links()

        # cycles through pages in sequential order and gets page links
        while self.go_to_next_page() and len(link_list) < num_items:
            page_links = self.get_page_links()
            link_list.extend(page_links)

        # returns only a maximum of num_items links
        if len(link_list) > num_items:
            return link_list[:num_items]
        else:
            return link_list


if __name__ == '__main__':
    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonScraper = AmazonScraper(url)
    amazonScraper.connect_to_link()
    amazonScraper.sort_by_reviews()
    # page_links = amazonScraper.get_page_links()
    item_links = amazonScraper.get_item_links(100)
    # is_not_last_page = amazonScraper.go_to_next_page()
    while True:
        pass
