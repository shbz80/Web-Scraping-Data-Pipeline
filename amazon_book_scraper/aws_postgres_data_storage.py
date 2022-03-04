"""Provides the implementation of the AWS Postgres RDS data storage class"""
from os.path import join
from dataclasses import asdict
from os import getcwd
import json
import pandas as pd
from sqlalchemy import create_engine, inspect, text
from entities import Book, BookAttribute, Review
from rds_data_storage import RDSDataStorage
from utils import create_dir_if_not_exists


class AWSPostgresRDSDataStorage(RDSDataStorage):
    """This class provides methods for storing and retrieving scraped book
    data on an ASW Postgres RDS. The object can be passed into the 
    main scraper object"""

    def __init__(self, rds_config: dict) -> None:
        """
        Args:
            rds_config (dict): RDS configs
        """
        DATABASE_TYPE = rds_config['DATABASE_TYPE']
        DBAPI = rds_config['DBAPI']
        ENDPOINT = rds_config['ENDPOINT']
        USER = rds_config['USER']
        PASSWORD = rds_config['PASSWORD']
        PORT = rds_config['PORT']
        DATABASE = rds_config['DATABASE']
        self._rds_engine = create_engine(
            f"{DATABASE_TYPE}+{DBAPI}://{USER}:{PASSWORD}@{ENDPOINT}:{PORT}/{DATABASE}")
        self._rds_engine.connect()
        self._rds_attribute_table = 'book_attributes'
        self._rds_review_table = 'book_reviews'

    def save_book(self, book: Book, saved_isbns: str) -> None:
        """Saves a book object in an S3 bucket

        Args:
            book (Book): the book object to be saved
            saved_isbns (str): list if isbns for which the
            attributes are already saved. Only reviews are new.
        """
        if book.attributes.isbn not in saved_isbns:
            self._save_book_attributes(book.attributes)
        self._save_reviews(book.reviews)

    def get_saved_book_urls(self, num_reviews: int) -> list[str]:
        """Get all the saved book urls. It does not return books with
        insufficient number of review

        Args:
            num_reviews (int): number of reviews required

        Returns:
            list[str]: list of saved book urls
        """
        # check is the review table exists
        insp = inspect(self._rds_engine)
        if not insp.has_table(self._rds_review_table):
            return []
        # if it exists get the urls with review >= num_review
        review_table = pd.read_sql_table(
            self._rds_review_table, self._rds_engine)
        isbn_count = review_table['isbn'] .value_counts()
        isbns = isbn_count.index[isbn_count >= num_reviews]

        attribute_table = pd.read_sql_table(
            self._rds_attribute_table, self._rds_engine).set_index('isbn')
        saved_urls = attribute_table['book_url'][isbns].tolist()
        return saved_urls

    def get_saved_book_isbns(self):
         # check is the attributes table exists
        insp = inspect(self._rds_engine)
        if not insp.has_table(self._rds_attribute_table):
            return []
        # if it exists gets the users for the given isbn    
        else:
            sql_query = f'''SELECT isbn FROM {self._rds_attribute_table};'''
            result = list(self._rds_engine.execute(sql_query).fetchall())
            result = [item[0] for item in result]
        return result

    def get_saved_review_users(self, isbn: str) -> list[str]:
        """Get all the user names of the saved reviews of a particular book.

        Args:
            isbn (str): the book isbn number

        Returns:
            list[str]: list of user names of reviews
        """
        # check is the reviews table exists
        insp = inspect(self._rds_engine)
        if not insp.has_table(self._rds_review_table):
            return []
        # if it exists gets the users for the given isbn    
        else:
            sql_query = f'''SELECT "user" FROM {self._rds_review_table} WHERE isbn = '{isbn}';'''
            result = self._rds_engine.execute(sql_query).fetchall()
            result = [item[0] for item in result]
        return result

    def _save_reviews(self, reviews):
        # save the reviews in RDS
        book_reviews_df = pd.DataFrame(reviews)
        try:
            book_reviews_df.to_sql(
                self._rds_review_table,
                self._rds_engine,
                if_exists='append',
                index=False)
        except:
            print(
                f"Could not save reviews in RDS")

    def _save_book_attributes(self, book_attributes):
        if not isinstance(book_attributes, BookAttribute):
            raise TypeError('Invalid type for book attribute')

        # save the book attribute in RDS
        book_attrubute_df = pd.DataFrame([asdict(book_attributes)])
        try:
            book_attrubute_df.to_sql(
                self._rds_attribute_table,
                self._rds_engine, if_exists='append',
                index=False)
        except:
            print(
                f"Could not save the record for {book_attributes.title} in RDS")

