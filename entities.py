"""Contains the book and the review classes
"""
from dataclasses import dataclass

@dataclass
class Book:
    """The basic book class
    """
    title: str
    isbn: str
    uuid: str
    author: str
    description: str
    date: str
    pages: int
    price: float
    best_seller_rank: int
    review_rating: float
    review_count: int
    image_url: str
    reviews: list[str]


@dataclass
class Review:
    """The basic review class
    """
    text: str
    rating: int
    user: str




