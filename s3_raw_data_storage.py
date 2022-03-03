"""Provides the implementation of the cloud raw data storage class"""
from os.path import join
from dataclasses import asdict
from os import getcwd
import json
import urllib.request
from attr import attributes
import boto3
from entities import Book, BookAttribute, Review
from raw_data_storage import RawDataStorage
from utils import create_dir_if_not_exists


class S3RawDataStorage(RawDataStorage):
    """This class provides methods for storing and retrieving scraped book
    data on a ASW S3 bucket in the clouyd. The object can be passed into the 
    main scraper object"""

    def __init__(self, path: str, bucket: str) -> None:
        """
        Args:
            path (str): path to where the 'raw_data' folder containing all
            the scraped datashould be stored.
            bucket (str): ASW S3 bucket name
        """
        self._s3_client = boto3.client('s3')
        self._s3_root_folder = join(path, 'raw_data') if path else 'raw_data'
        self._s3_bucket = bucket
        self._s3_resource = boto3.resource('s3')
        # temp folder for file buffer
        temp_path = join(getcwd(), 'temp')
        create_dir_if_not_exists(temp_path)

    def save_book(self, book: Book, saved_isbns: str) -> None:
        """Saves a book object in an S3 bucket

        Args:
            book (Book): the book object to be saved
            saved_isbns (str): list if isbns for which the
            attributes are already saved. Only reviews are new.
        """
        book_path = join(self._s3_root_folder, book.attributes.isbn)
        reviews_path = join(book_path, 'reviews')
        if book.attributes.isbn not in saved_isbns:
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
        saved_urls = []
        isbns = self._get_all_isbns()
        for isbn in isbns:
            count = self._get_review_count(isbn)
            if count >= num_reviews:
                url = self._get_book_url(isbn)
                saved_urls.append(url)

        return saved_urls

    def get_saved_book_isbns(self):
        """Gets all the saved book isbn numbers"""
        return self._get_all_isbns()

    def get_saved_review_users(self, isbn: str) -> list[str]:
        """Get all the user names of the saved reviews of a particular book.

        Args:
            isbn (str): the book isbn number

        Returns:
            list[str]: list of user names of reviews
        """
        saved_users = []
        review_path = join(self._s3_root_folder, isbn, 'reviews')
        all_files = self._get_all_file_keys()
        for file_key in all_files:
            # if it is a review
            if review_path in file_key:
                user_json = file_key.split('/')[-1]
                user = user_json.split('.')[0]
                saved_users.append(user)
        return saved_users

    def save_book_image(self, url: str, isbn: str) -> None:
        """Saves an image from the given url to the specified book
        location

        Args:
            url (str): image url
            isbn (str): the book isbn
        """
        # retirieve the image file to a temporary local location
        temp_path = join(getcwd(), 'temp')
        try:
            temp_image_path = join(temp_path, 'tmp.jpg')
            urllib.request.urlretrieve(url, filename=temp_image_path)
        except:
            print(f"Could retrieve coverpage image for {isbn}")

        # upload the image file to cloud (S3)
        file_key = join(self._s3_root_folder, isbn, f"{isbn}.jpg")
        try:
            self._s3_client.upload_file(
                temp_image_path, self._s3_bucket, file_key)
        except:
            print(
                f"Could not save the image for {isbn} in S3")

    def _save_reviews(self, reviews, path):
        # get all reviews by their users name
        for review in reviews:
            if not isinstance(review, Review):
                raise TypeError('Invalid type for review')
            # save the review as a json file
            try:
                file_key = f"{path}/{review.user}.json"
                review_dict = asdict(review)
                self._s3_client.put_object(Bucket=self._s3_bucket,
                                        Body=json.dumps(review_dict),
                                        Key=file_key)
            except:
                print(
                    f"Could not save review for {review.user} in S3")

    def _save_book_attributes(self, book_attributes, path):
        if not isinstance(book_attributes, BookAttribute):
            raise TypeError('Invalid type for book attribute')

        # save the book record as a json object in S3
        file_key = join(path, 'data.json')
        attr_dict = asdict(book_attributes)
        try:
            self._s3_client.put_object(Bucket=self._s3_bucket,
                                       Body=json.dumps(attr_dict),
                                       Key=file_key)
        except:
            print(
                f"Could not save the record for {book_attributes.title} in S3")


    def _get_all_file_keys(self):
        bucket = self._s3_resource.Bucket(self._s3_bucket)
        return [obj.key for obj in bucket.objects.all()]

    def _get_all_isbns(self):
        all_files = self._get_all_file_keys()
        return list(set([(key).split('/')[1] for key in all_files]))

    def _get_review_count(self, isbn):
        all_files = self._get_all_file_keys()
        isbn_review = join(self._s3_root_folder, isbn, 'reviews')
        count = 0
        for file_key in all_files:
            if isbn_review in file_key:
                count += 1
        return count

    def _get_book_url(self, isbn):
        # download the data.json file from S3
        data_key = join(self._s3_root_folder, isbn, 'data.json')
        temp_path = join(getcwd(), 'temp', 'data.json')
        self._s3_client.download_file(
            self._s3_bucket, data_key, temp_path)

        # read the file
        with open(temp_path, mode='r') as f:
            attribute_dict = json.load(f)

        return attribute_dict['book_url']
