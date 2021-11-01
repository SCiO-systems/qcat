FROM python:3.6

ENV PYTHONUNBUFFERED 1
RUN mkdir /code
WORKDIR /code

# Django-gis packages
RUN apt-get update && apt-get install -y \
    curl \
    binutils \
    libproj-dev \
    gdal-bin \
    libmemcached-dev

# Dependencies for static assets
RUN curl -sL https://deb.nodesource.com/setup_14.x | bash -
RUN apt-get install -y nodejs \
    build-essential

# Install wkhtmltopdf binary for summary pdf
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.4/wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
RUN tar xvf wkhtmltox-0.12.4_linux-generic-amd64.tar.xz
RUN mv wkhtmltox/bin/wkhtmlto* /usr/bin

ADD requirements/* /code/
RUN pip install -r development.txt
#RUN pip install --upgrade -r production.txt

ADD . /code/

# Make 'wait' script available for the entrypoint-script.
ADD https://raw.githubusercontent.com/eficode/wait-for/master/wait-for /usr/local/bin/waitfor
RUN chmod +x /usr/local/bin/waitfor

# install google chrome
RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
RUN apt-get -y update
RUN apt-get install -y google-chrome-stable

# install chromedriver
RUN apt-get install -yqq unzip
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# set display port to avoid crash
ENV DISPLAY=:99

ENTRYPOINT ["/docker/django/entrypoint.sh"]
