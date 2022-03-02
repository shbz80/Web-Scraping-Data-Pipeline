from abc import ABC, abstractmethod
from entities import Book

class RawDataStorage(ABC):
    @abstractmethod
    def save_book(self, book: Book):
        pass
    
    @abstractmethod
    def save_book_image(self, url: str, isbn: str):
        pass

    @abstractmethod
    def get_saved_book_urls(self, num_reviews: int):
        pass

    @abstractmethod
    def get_saved_review_users(self, isbn: str):
        pass
