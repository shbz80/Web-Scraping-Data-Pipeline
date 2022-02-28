"""Contains the book and the review classes
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class BookAttribute:
    title: str
    isbn: str
    uuid: str
    author: Optional[str]
    description: Optional[str]
    date: Optional[str]
    pages: Optional[int]
    price: Optional[float]
    best_seller_rank: Optional[int]
    review_rating: Optional[float]
    review_count: Optional[int]
    image_url: Optional[str]
    book_url: str

@dataclass
class Review:
    text: str
    rating: Optional[int]
    user: str

@dataclass
class Book:
    attributes: BookAttribute
    reviews: list[Review]


