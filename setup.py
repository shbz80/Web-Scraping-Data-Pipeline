from setuptools import setup
from setuptools import find_packages

setup(
    name='amazon_book_scraper',
    version='0.0.1',
    description="This web scraper can scrape book details from a specified book category in Amazon books section. The scraped books are either stored locally or in an Amazon S3 bucket. It can also be optionally stored in an AWS Postres relational database system (RDS). The application can be run multiple times and it will resume as a continuation of what was already scraped. Executing the application after the required number of books have been scraped will simply exit. Running the application with an increased number of book reviews will satisfy the requirements even for those books that are already scraped.",
    url='https://github.com/shbz80/Web-Scraping-Data-Pipeline',
    author='Shahbaz Khader',
    license='MIT',
    packages=find_packages(),
    install_requires=['boto3', 'pandas', 'selenium', 'SQLAlchemy'],
)
