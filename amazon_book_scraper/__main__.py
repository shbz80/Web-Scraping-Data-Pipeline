import sys
from os import getcwd
from local_raw_data_storage import LocalRawDataStorage
from s3_raw_data_storage import S3RawDataStorage
from aws_postgres_data_storage import AWSPostgresRDSDataStorage
from amazon_book_attribute_scraper import AmazonBookAttributeScraper
from amazon_automated_book_review_scraper import AmazonAutomatedBookReviewScraper
from amazon_automated_book_scraper import AmazonAutomatedBookScraper

url = "https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1645782603&ref=sr_pg_1"
# specify a list of banned title pharses that are likely to be of
# a special format
banned_titles = [
    'Dungeons and Dragons',
    'Dungeons & Dragons',
    "Player's Handbook",
    "Users's Manual",
]
# object that scrapes attributes of single book
abas = AmazonBookAttributeScraper(banned_titles=banned_titles)

# object that scrapes reviews of a single book
aabrs = AmazonAutomatedBookReviewScraper()

# choose and initialize raw storage object: local or S3 bucket
# raw_storage = LocalRawDataStorage(path=getcwd())
raw_storage = S3RawDataStorage(path=None, bucket='aicore-web-scraping')

# params for the AWS Postgres RDS
rds_param = {'DATABASE_TYPE': 'postgresql',
             'DBAPI': 'psycopg2',
             'ENDPOINT': "aicore-webscraping-db.cwckuebjlobx.us-east-1.rds.amazonaws.com",
             'USER': 'postgres',
             'PASSWORD': 'aicore2022',
             'PORT': 5432,
             'DATABASE': 'postgres'}
# rds storage is optional
rds_storage = AWSPostgresRDSDataStorage(rds_param)
# rds_storage = None

# initialize the scraper object
aabs = AmazonAutomatedBookScraper(
    url=url,
    book_attribute_scraper=abas,
    automated_book_review_scraper=aabrs,
    raw_data_storage=raw_storage,
    rds_data_storage=rds_storage,
    browser='firefox')
    
# run the scraper
num_books = int(sys.argv[1])
num_reviews = int(sys.argv[2])
# num_books = 50
# num_reviews = 5
aabs.scrape_books(num_books=num_books, num_reviews=num_reviews)
