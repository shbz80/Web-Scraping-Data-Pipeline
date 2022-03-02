import unittest
import os
from local_raw_data_storage import LocalRawDataStorage
from entities import Book, BookAttribute, Review
import utils


class TestLocalRawDataStorage(unittest.TestCase):
    def setUp(self) -> None:
        path = os.path.join(os.getcwd(), 'test_data')
        utils.create_dir_if_not_exists(path)
        self.storage = LocalRawDataStorage(path=path)
        book_attr = BookAttribute(
            title="Title", isbn='isbn-101', uuid='uuid', book_url='book_url',
            author='author', description='des', date='date',pages=100, 
            price=5.0,best_seller_rank=1, review_rating=2.5, review_count=400,
            image_url='image_url')
        book_review = Review(text='text', user='user', rating=3)
        self.test_book = Book(attributes=book_attr, reviews=[book_review])

    def test_save_book(self):
        self.storage.save_book(self.test_book)
        book_path = os.path.join(os.getcwd(), 'test_data', 'raw_data')
        self.assertTrue(utils.is_dir_present('isbn-101', book_path))
        attribute_path = os.path.join(book_path, 'isbn-101')
        self.assertTrue(utils.is_file_present('data.json', attribute_path))
        self.assertTrue(utils.is_dir_present('reviews', attribute_path))
        review_path = os.path.join(attribute_path, 'reviews')
        self.assertTrue(utils.is_file_present('user.json', review_path))

    def test_save_book_image(self):
        image_url = "https://images-na.ssl-images-amazon.com/images/I/41ATfFjhelL._SX329_BO1,204,203,200_.jpg"
        self.storage.save_book_image(image_url, 'isbn-101')
        book_path = os.path.join(os.getcwd(), 'test_data', 'raw_data')
        attribute_path = os.path.join(book_path, 'isbn-101')
        self.assertTrue(utils.is_file_present('isbn-101.jpg', attribute_path))

    def test_get_saved_book_urls(self):
        book_urls = self.storage.get_saved_book_urls(1)
        self.assertIsInstance(book_urls, list)
        self.assertEqual(len(book_urls), 1)
        self.assertEqual(book_urls[0], 'book_url')

    def test_get_saved_review_users(self):
        saved_users = self.storage.get_saved_review_users('isbn-101')
        self.assertIsInstance(saved_users, list)
        self.assertEqual(len(saved_users), 1)
        self.assertEqual(saved_users[0], 'user')


