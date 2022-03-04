"""Provides the abstract class for raw data storage"""
from abc import ABC, abstractmethod
from entities import Book

class RawDataStorage(ABC):
    """This class can be inherited by local and cloud raw data storage"""
    @abstractmethod
    def save_book(self, book: Book, saved_isbns: str):
        pass
    
    @abstractmethod
    def save_book_image(self, url: str, isbn: str):
        pass

    @abstractmethod
    def get_saved_book_urls(self, num_reviews: int):
        pass

    @abstractmethod
    def get_saved_book_isbns(self):
        pass

    @abstractmethod
    def get_saved_review_users(self, isbn: str):
        pass
