import os
import pandas as pd
from amazon_scraper import AmazonBookScraper

url = "https://www.amazon.com/s?i=stripbooks&rh=n%3A25&fs=true&qid=1645782603&ref=sr_pg_1"
banned = ["Player's Handbook", "Dungeons and Dragons"]
amazonBookScraper = AmazonBookScraper(
    url, browser='firefox', banned_list=banned)

# choose one of below
# save_opt = None
# save_opt = {'strategy': 'local',
#             'location': os.getcwd()}
rds_dict = {'DATABASE_TYPE': 'postgresql',
            'DBAPI': 'psycopg2',
            'ENDPOINT': "aicore-webscraping-db.cwckuebjlobx.us-east-1.rds.amazonaws.com",
            'USER': 'postgres',
            'PASSWORD': 'aicore2022',
            'PORT': 5432,
            'DATABASE': 'postgres'}
save_opt = {'strategy': 'cloud',                # store it in cloud
            'location': 'aicore-web-scraping',  # AWS S3 bucket name
            'rds': rds_dict}  # AWS RDS

book_records, book_reviews = amazonBookScraper.scrape_books(
    10, save_opt=save_opt, review_num=50)

df = pd.DataFrame(book_records)
df.info()
print(df.head())
df = pd.DataFrame(book_reviews)
df.info()
print(df.head())

print(df["title"].head())
print(df["author(s)"].head())
print(df["best_seller_rank"].head())
print(df["review_count"].head())
print(df["review_rating"].head())
print(df["description"].head())
print(df["pages"].head())
print(df["price"].head())
print(df["date"].head())
print(df["image_link"].head())
print(df["uuid"].head())
print(df["isbn"].head())

# book_id = 'ISBN-13-978-1408856772'
# amazonBookScraper.get_cover_page_image_from_cloud(book_id)
