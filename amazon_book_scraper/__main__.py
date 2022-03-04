from os import getcwd
from local_raw_data_storage import LocalRawDataStorage
from s3_raw_data_storage import S3RawDataStorage
from aws_postgres_data_storage import AWSPostgresRDSDataStorage
from amazon_book_attribute_scraper import AmazonBookAttributeScraper
from amazon_automated_book_review_scraper import AmazonAutomatedBookReviewScraper
from amazon_automated_book_scraper import AmazonAutomatedBookScraper

url = "https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1645782603&ref=sr_pg_1"
# object that scrapes attributes of single book
abas = AmazonBookAttributeScraper()
# object that scrapes a reviews of a single book
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
aabs.scrape_books(num_books=7, num_reviews=7)