# install the base image with Python
FROM python:3.9-slim-buster
# install wget and its dependencies
RUN apt-get update && apt-get install -y gnupg2
RUN apt-get update && apt-get install -y wget
# download and install Google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update && apt-get install -y google-chrome-stable
# install curl
RUN apt-get -y update && apt-get install -y curl
# download and install the Selenium chrome driver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN apt-get install -yqq unzip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
# copy all contents of the project folder
COPY . .
# set AWS credentials as env variables
# this is necessary for accessing the AWS S3 bucket
ENV AWS_CONFIG_FILE=/.aws/config
ENV AWS_SHARED_CREDENTIALS_FILE=/.aws/credentials
# install all python package requirements
RUN pip install -r requirements.txt
# install the AWS CLI (not sure this is required)
RUN pip install awscli
# runs the scraper program. amazon_book_scraper is a package
ENTRYPOINT ["python", "amazon_book_scraper"]
# the scraper program has two arguments: num_book and num_reviews
# both gets a default value of 5 and can be overdriven.
CMD ["5", "5"]