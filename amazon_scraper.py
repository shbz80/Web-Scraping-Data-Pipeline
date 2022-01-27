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
        # click on the sort by dropdown button
        xpath = '//span[@class = "a-dropdown-container"]'
        sort_dropdown = self.driver.find_element_by_xpath(xpath)
        xpath = './/span[@class="a-button-text a-declarative"]'
        sort_dropdown_button = sort_dropdown.find_element_by_xpath(xpath)
        sort_dropdown_button.click()

        # click the sort criterion: sort by reviews
        xpath = '//div[@class="a-popover-inner"]'
        temp_tag = self.driver.find_element_by_xpath(xpath)
        sort_criteria = temp_tag.find_elements_by_xpath('./ul/li')
        xpath = './a'
        sort_criteria[-1].find_element_by_xpath(xpath).click()
        time.sleep(1)

    def go_to_next_page(self):
        """
        Goes to the next page if it not the last page
        """
        xpath = '//span[@class="s-pagination-strip"]'
        pagination_strip = self.driver.find_element_by_xpath(xpath)
        elements = pagination_strip.find_elements_by_xpath('./*')
        last_element = elements[-1]
        # if not the next page return False
        if last_element.find_elements(By.ID, "aria-disabled"):
            return False
        # else click next and return True
        else:
            last_element.click()
            return False


if __name__ == '__main__':
    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonScraper = AmazonScraper(url)
    amazonScraper.connect_to_link()
    amazonScraper.sort_by_reviews()
    is_not_last_page = amazonScraper.go_to_next_page()
    while True:
        pass
