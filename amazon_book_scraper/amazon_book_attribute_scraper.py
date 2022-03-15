"""Provides the Amazon specific class for scraping book attributes."""
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from book_attribute_scraper import BookAttributeScraper
from utils import TIME_OUT

class AmazonBookAttributeScraper(BookAttributeScraper):
    """The Amazon specific book attribute scraper."""
    def __init__(self, banned_titles: list[str] = None) -> None:
        super().__init__(banned_titles)

    def _extract_isbn_attribute(self, driver):
        if not self.book_elements:
            raise Exception('This scraper in not initialized')
        
        isbn = None
        for element in self.book_elements:
            items = element.find_elements_by_xpath('./span/span')
            if 'ISBN-13' in items[0].text:
                isbn = items[0].text[:-2] + '-' + items[1].text
        return isbn

    def _extract_title_attribute(self, driver):
        xpath = '//span[@id="productTitle"]'
        # element = driver.find_element_by_xpath(xpath)
        element = WebDriverWait(driver, TIME_OUT).until(
            EC.presence_of_element_located((By.XPATH, xpath)))
        return element.text

    def _extract_language_attribute(self, driver):
        if not self.book_elements:
            raise Exception('This scraper in not initialized')

        language = None
        for element in self.book_elements:
            items = element.find_elements_by_xpath('./span/span')
            if "Language" in items[0].text:
                language = items[1].text
        return language

    def _extract_author_attribute(self, driver):
        xpath_1 = '//div[@id="authorFollow_feature_div"]'
        xpath_2 = '/div[@class="a-row a-spacing-top-small"]'
        xpath_3 = '/div[@class="a-column a-span4 authorNameColumn"]/a'
        elements = driver.find_elements_by_xpath(xpath_1+xpath_2+xpath_3)
        author = ",".join([element.text for element in elements])
        return author

    def _extract_description_attribute(self, driver):
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

    def _extract_date_attribute(self, driver):
        if not self.book_elements:
            raise Exception('This scraper in not initialized')
        
        date = None
        for element in self.book_elements:
            items = element.find_elements_by_xpath('./span/span')
            if "Publisher" in items[0].text:
                date_string = items[1].text
                # expects the date feature encolsed in 
                # paranthesis towards right
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

    def _extract_pages_attribute(self, driver):
        if not self.book_elements:
            raise Exception('This scraper in not initialized')
        pages = None
        for element in self.book_elements:
            items = element.find_elements_by_xpath('./span/span')
            if "pages" in items[1].text:
                pages_string = items[1].text
                pages = int(pages_string.split(" ")[0])
        return pages
        
    def _extract_price_attribute(self, driver):
        price = None
        try:
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
        except:
            pass
        return price
        
    def _extract_best_seller_rank_attribute(self, driver):
        if not self.product_elements:
            raise Exception('This scraper in not initialized')

        best_seller_rank = None
        for element in self.product_elements:
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

    def _extract_review_rating_attribute(self, driver):
        if not self.product_elements:
            raise Exception('This scraper in not initialized')

        review_rating = None
        for element in self.product_elements:
            try:
                xpath = './/span[@class="reviewCountTextLinkedHistogram noUnderline"]'
                rating_element = element.find_element_by_xpath(xpath)
                review_rating_string = rating_element.get_attribute("title")
                review_rating = float(review_rating_string[:3])
            except:
                pass
        return review_rating

    def _extract_review_count_attribute(self, driver):
        if not self.product_elements:
            raise Exception('This scraper in not initialized')

        review_count = None
        for element in self.product_elements:
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

    def _extract_image_url_attribute(self, driver):
        image_link = None
        try:
            xpath = '//div[@id="main-image-container"]//img[@id="imgBlkFront"]'
            element = driver.find_element_by_xpath(xpath)
            image_link = element.get_attribute("src")
        except:
            pass
        return image_link

    def _get_book_elements(self, driver):
        """Gets some book attribute elements from the current webpage:
        isbn, date, language, pages, 
        """
        try:
            xpath = '//div[@id="detailBullets_feature_div"]/ul/li'
            self.book_elements = driver.find_elements_by_xpath(xpath)
            return True
        except:
            return False

    def _get_product_elements(self, driver):
        """Gets some product feature elements from the current webpage:
        best_seller_rank, review_rating, review_count, 
        """
        try:
            xpath = '//div[@id="detailBulletsWrapper_feature_div"]/ul'
            self.product_elements = driver.find_elements_by_xpath(xpath)
            return True
        except:
            return False

    def _initialize(self, driver):
        if (bool(self._get_book_elements(driver)) and
            bool(self._get_product_elements(driver))):
            return True
        else:
            return False

    
