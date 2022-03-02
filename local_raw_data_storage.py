"""Provides the implementation of the local raw data storage class"""
import dataclasses
from os import  getcwd
from os.path import join
import json
import urllib.request
from entities import Book, BookAttribute, Review
from raw_data_storage import RawDataStorage
from utils import create_dir_if_not_exists, get_list_of_files
from utils import get_list_of_dirs, is_dir_present

class LocalRawDataStorage(RawDataStorage):
    """This class provides methods for storing and retrieving scraped book
    data on the local machine. The object can be passed into the 
    main acraper object"""
    def __init__(self, path: str) -> None:
        """
        Args:
            path (str): path to where the 'raw_data' folder containing all
            the scraped datashould be stored.
        """
        self._path_to_raw_data = join(path, 'raw_data')
        create_dir_if_not_exists(self._path_to_raw_data)

    def save_book(self, book: Book) -> None:
        """Saves a book object

        Args:
            book (Book): the book object to be saved
        """
        book_path = join(self._path_to_raw_data, book.attributes.isbn)
        reviews_path = join(book_path, 'reviews')
        self._save_book_attributes(book.attributes, book_path)
        self._save_reviews(book.reviews, reviews_path)

    def get_saved_book_urls(self, num_reviews: int) -> list[str]:
        """Get all the saved book urls. It does not return books with
        insufficient number of review

        Args:
            num_reviews (int): number of reviews required

        Returns:
            list[str]: list of saved book urls
        """
        path = self._path_to_raw_data
        # get all saved book isbn numbers
        book_isbns = get_list_of_dirs(path)
        book_urls = []
        for book_isbn in book_isbns:
            review_path = join(path, book_isbn, 'reviews')
            saved_reviews = get_list_of_files(review_path)
            num_saved = len(saved_reviews)
            if num_saved >= num_reviews:
                attribute_path = join(path, book_isbn, 'data.json')
                with open(attribute_path, mode='r') as f:
                    attr_dict = json.load(f)
                book_url = attr_dict['book_url']
                book_urls.append(book_url)
        return book_urls

    def get_saved_review_users(self, isbn: str) -> list[str]:
        """Get all the user names of the saved reviews of a particular book.

        Args:
            isbn (str): the book isbn number

        Returns:
            list[str]: list of user names of reviews
        """
        path = self._path_to_raw_data
        # get all saved book isbn numbers
        if not is_dir_present(isbn, path):
            return []

        review_path = join(path, isbn, 'reviews')
        saved_reviews = get_list_of_files(review_path)
        saved_reviews = [user.split('.')[0] for user in saved_reviews]
        return saved_reviews

    def save_book_image(self, url: str, isbn: str) -> None:
        """Saves an image from the given url to the specified book

        Args:
            url (str): image url
            isbn (str): the book isbn
        """
        if not is_dir_present(isbn, self._path_to_raw_data):
            raise Exception('Book data folder does not exist.')
        image_path = join(self._path_to_raw_data, isbn, f'{isbn}.jpg')
        try:
            urllib.request.urlretrieve(url, filename=image_path)
        except:
            print(f"Could not save image for {isbn}")

    def _save_reviews(self, reviews, path):
        create_dir_if_not_exists(path)
        # get all reviews by their users name
        saved_users = get_list_of_files(path)
        # save all nonexisting reviews
        for review in reviews:
            if review.user not in saved_users:
                self._save_review(review, path)

    @staticmethod
    def _save_review(review, path):
        if not isinstance(review, Review):
            raise TypeError('Invalid type for review')
        with open(f"{path}/{review.user}.json", mode='w') as f:
            json.dump(dataclasses.asdict(review), f)

    @staticmethod
    def _save_book_attributes(book_attributes, path):
        if not isinstance(book_attributes, BookAttribute):
            raise TypeError('Invalid type for book attribute')
        if create_dir_if_not_exists(path):
            with open(f"{path}/data.json", mode='w') as f:
                json.dump(dataclasses.asdict(book_attributes), f)