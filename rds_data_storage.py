"""Provides the abstract class for RDS data storage"""
from abc import ABC, abstractmethod
from entities import Book


class RDSDataStorage(ABC):
    """This class can be inherited by any RDS system.
    The interface to the RDS is supposed to be controlled by this class
    """
    @abstractmethod
    def save_book(self, book: Book, saved_isbns: str):
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
