FROM python:3.9-slim-buster
RUN apt-get update && apt-get install -y gnupg2
RUN apt-get update && apt-get install -y wget
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - 
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update && apt-get install -y google-chrome-stable
RUN apt-get -y update && apt-get install -y curl
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN apt-get install -yqq unzip \
    && unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/
COPY . .
ENV AWS_CONFIG_FILE=/.aws/config
ENV AWS_SHARED_CREDENTIALS_FILE=/.aws/credentials
RUN pip install -r requirements.txt
RUN pip install awscli
ENTRYPOINT ["python", "amazon_book_scraper"]
CMD ["5", "5"]