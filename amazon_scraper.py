import time
from selenium import webdriver

class AmazonScraper():
    def __init__(self, url) -> None:
        if not isinstance(url, str) or not len(url):
            raise ValueError('URL must be a nonempty string.')
        self.url = url
        self.driver = None

    def get_items(self, num_items, sort_oder) -> list:
        pass

    def connect_to_link(self):
        # inits selenium and gets the lik to the category
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)
        # time.sleep(20)

    def sort_by_reviews(self):
        xpath = '//span[@class = "a-dropdown-container"]'
        sort_dropdown = self.driver.find_element_by_xpath(xpath)
        xpath = './/span[@class="a-button-text a-declarative"]'
        sort_dropdown_button = sort_dropdown.find_element_by_xpath(xpath)
        sort_dropdown_button.click()
        xpath = '//ul[@tabindex="-1"]'
        sort_criteria = self.driver.find_elements_by_xpath(xpath)
        xpath = './a'
        sort_criteria[-1].find_element_by_xpath(xpath).click()
        while True:
            pass



        
if __name__ == '__main__':
    url = 'https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1643228276&ref=sr_pg_1'
    amazonScraper = AmazonScraper(url)
    amazonScraper.connect_to_link()
    amazonScraper.sort_by_reviews()
